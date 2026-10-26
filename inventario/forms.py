from django import forms

from .models import CaracteristicaProducto, Categoria, Producto, Proveedor


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
    class Meta:
        model = Proveedor
        fields = ('nombre', 'nit', 'contacto', 'telefono', 'email', 'direccion')

    def clean_nit(self):
        return self.cleaned_data['nit'].strip()


class CategoriaForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ('nombre', 'descripcion')


class ProductoForm(EstiloBootstrapMixin, forms.ModelForm):
    precio = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2)

    class Meta:
        model = Producto
        fields = ('codigo', 'nombre', 'descripcion', 'precio', 'stock',
                  'proveedor', 'categorias')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'categorias': forms.CheckboxSelectMultiple(),
        }

    def clean_codigo(self):
        return self.cleaned_data['codigo'].strip()


class AsignarCategoriasForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ('categorias',)
        widgets = {'categorias': forms.CheckboxSelectMultiple()}


class CaracteristicaForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = CaracteristicaProducto
        fields = ('nombre', 'valor')
