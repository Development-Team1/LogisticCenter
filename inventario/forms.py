import re

from django import forms
from django.forms import inlineformset_factory

from .models import CaracteristicaProducto, Categoria, Producto, ProductoProveedor, Proveedor


class EstiloBootstrapMixin:
    """Agrega las clases de Bootstrap a todos los campos del formulario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            clase = 'form-select' if isinstance(widget, forms.Select) else 'form-control'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {clase}".strip()


class ProveedorForm(EstiloBootstrapMixin, forms.ModelForm):
    """Todos los campos del proveedor son obligatorios."""

    class Meta:
        model = Proveedor
        fields = ('nombre', 'nit', 'telefono', 'email', 'direccion')

    def clean_nit(self):
        return self.cleaned_data['nit'].strip()

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        if not re.fullmatch(r'\+?[0-9 ]{7,20}', telefono):
            raise forms.ValidationError('Ingrese un teléfono válido (solo dígitos, entre 7 y 20).')
        return telefono


class ProductoProveedorForm(EstiloBootstrapMixin, forms.ModelForm):
    """Producto de la lista de un proveedor. Todos los campos son obligatorios.

    El código es el identificador del producto: una vez creado no se puede cambiar.
    """

    class Meta:
        model = ProductoProveedor
        fields = ('codigo', 'nombre', 'descripcion', 'marca', 'unidad_medida')
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, proveedor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._proveedor = proveedor
        if self.instance.pk:
            self.fields['codigo'].disabled = True
            self.fields['codigo'].help_text = 'El código no se puede modificar.'

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].strip().upper()
        if not re.fullmatch(r'[A-Z0-9._-]+', codigo):
            raise forms.ValidationError('Use solo letras, números, punto, guion o guion bajo (sin espacios).')
        return codigo

    def clean_nombre(self):
        return ' '.join(self.cleaned_data['nombre'].split())

    def clean(self):
        cleaned = super().clean()
        proveedor_id = self._proveedor.pk if self._proveedor else self.instance.proveedor_id
        nombre = cleaned.get('nombre')
        if proveedor_id and nombre:
            repetidos = ProductoProveedor.objects.filter(proveedor_id=proveedor_id, nombre__iexact=nombre)
            if self.instance.pk:
                repetidos = repetidos.exclude(pk=self.instance.pk)
            if repetidos.exists():
                self.add_error('nombre', 'Este proveedor ya tiene un producto con ese nombre.')
        return cleaned


# Lista de productos que se diligencia al registrar un proveedor (mínimo uno).
ProductosProveedorFormSet = inlineformset_factory(
    Proveedor, ProductoProveedor, form=ProductoProveedorForm,
    extra=0, min_num=1, validate_min=True, can_delete=False,
)


class CategoriaForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ('nombre', 'descripcion')


class ProductoForm(EstiloBootstrapMixin, forms.ModelForm):
    """Registro y modificación de un producto en inventario.

    Registro: se elige el proveedor y el producto (nombre + código) de la lista de ese
    proveedor; el nombre y el código deben coincidir entre sí y con el proveedor.
    Modificación: solo se pueden cambiar el precio y el stock.
    """

    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(), empty_label='Seleccione un proveedor',
    )
    nombre = forms.CharField(max_length=150, label='Nombre del producto')
    codigo = forms.CharField(max_length=50, label='Código')
    precio = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2)

    field_order = ('proveedor', 'nombre', 'codigo', 'precio', 'stock', 'categorias')

    class Meta:
        model = Producto
        fields = ('precio', 'stock', 'categorias')
        widgets = {'categorias': forms.CheckboxSelectMultiple(attrs={'class': 'checklist'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.referencia = None
        self.fields['nombre'].widget.attrs.update({'list': 'opciones-nombre', 'autocomplete': 'off'})
        self.fields['codigo'].widget.attrs.update({'list': 'opciones-codigo', 'autocomplete': 'off'})

        if self.instance.pk:
            # Modificación: la identidad del producto queda bloqueada.
            ref = self.instance.referencia
            self.initial.update({'proveedor': ref.proveedor_id, 'nombre': ref.nombre, 'codigo': ref.codigo})
            for nombre in ('proveedor', 'nombre', 'codigo'):
                self.fields[nombre].disabled = True
            del self.fields['categorias']

    @property
    def es_modificacion(self):
        return bool(self.instance.pk)

    def clean(self):
        cleaned = super().clean()
        if self.es_modificacion:
            return cleaned

        proveedor = cleaned.get('proveedor')
        codigo = (cleaned.get('codigo') or '').strip().upper()
        nombre = ' '.join((cleaned.get('nombre') or '').split())
        if not (proveedor and codigo and nombre):
            return cleaned

        referencia = ProductoProveedor.objects.filter(
            proveedor=proveedor, codigo__iexact=codigo
        ).first()

        if referencia is None:
            otro = ProductoProveedor.objects.select_related('proveedor').filter(codigo__iexact=codigo).first()
            if otro:
                self.add_error(
                    'codigo',
                    f'El código {codigo} pertenece a otro proveedor ({otro.proveedor.nombre}), '
                    f'no a {proveedor.nombre}.',
                )
            else:
                self.add_error(
                    'codigo',
                    f'El código {codigo} no está en la lista de productos de {proveedor.nombre}.',
                )
        elif referencia.nombre.casefold() != nombre.casefold():
            self.add_error(
                'nombre',
                f'El código {codigo} corresponde a «{referencia.nombre}», no a «{nombre}».',
            )
        elif Producto.objects.filter(referencia=referencia).exists():
            self.add_error('codigo', 'Este producto ya está registrado en el inventario.')
        else:
            self.referencia = referencia
        return cleaned

    def save(self, commit=True):
        if self.referencia is not None:
            self.instance.referencia = self.referencia
        return super().save(commit=commit)


class AsignarCategoriasForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ('categorias',)
        widgets = {'categorias': forms.CheckboxSelectMultiple(attrs={'class': 'checklist'})}


class CaracteristicaForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = CaracteristicaProducto
        fields = ('nombre', 'valor')
