from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from .models import TIPOS_DOCUMENTO, Cliente, Empleado, Usuario, validar_telefono

class IniciarSesionForm(AuthenticationForm):
    username = forms.CharField(
        label = "Usuario",
        widget = forms.TextInput(attrs={
            'class':'form-control',
            'placeholder':'Ingrese su usuario'
        })
    )

    password = forms.CharField(
        label = "Contraseña",
        widget = forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder':'Ingrese su contraseña'
        })
    )

    class Meta:

        model = Usuario
        fields = ['username', 'password']



# --------------------------------------------------------------------------
# Empleados y clientes
# --------------------------------------------------------------------------

def _texto(label, placeholder='', required=True, max_length=None):
    return forms.CharField(
        label=label,
        required=required,
        max_length=max_length,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': placeholder or label}),
    )


class PerfilMixin(forms.Form):
    """Campos y validaciones compartidos por los formularios de empleados y clientes.

    Cada formulario concreto define:
      ES_STAFF   -> tipo de usuario que crea (True = empleado, False = cliente). Lo fija
                    el formulario, el usuario no puede elegirlo ni cambiarlo.
      PERFIL     -> modelo con los datos propios (Empleado o Cliente).
      RELACION   -> nombre de la relación inversa desde Usuario ('empleado' / 'cliente').
      CAMPO_EXTRA-> campo propio del perfil ('cargo' / 'ciudad').
    """

    ES_STAFF = None
    PERFIL = None
    RELACION = None
    CAMPO_EXTRA = None
    TIPOS_DOCUMENTO_PERMITIDOS = None  # None = todos

    tipo_usuario = forms.CharField(
        label='Tipo de usuario',
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    first_name = _texto('Nombre', 'Nombre', max_length=150)
    last_name = _texto('Apellidos', 'Apellidos', max_length=150)
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
    )
    tipo_documento = forms.ChoiceField(
        label='Tipo de documento',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    numero_documento = _texto('Número de documento', 'Número de documento', max_length=20)
    telefono = _texto('Teléfono', 'Teléfono', max_length=20)
    direccion = _texto('Dirección', 'Dirección', required=False, max_length=255)

    # ---- inicialización ---------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tipos = [
            (codigo, nombre) for codigo, nombre in TIPOS_DOCUMENTO
            if self.TIPOS_DOCUMENTO_PERMITIDOS is None or codigo in self.TIPOS_DOCUMENTO_PERMITIDOS
        ]
        self.fields['tipo_documento'].choices = [('', 'Seleccione...')] + tipos
        self.fields['tipo_usuario'].initial = 'Empleado' if self.ES_STAFF else 'Cliente'
        self.fields['telefono'].validators.append(validar_telefono)

        # Al modificar, se cargan los datos que ya tiene el perfil.
        perfil = self._perfil_actual()
        if perfil is not None:
            for nombre in ('tipo_documento', 'numero_documento', 'telefono', 'direccion', self.CAMPO_EXTRA):
                self.initial.setdefault(nombre, getattr(perfil, nombre))

    def _perfil_actual(self):
        instancia = getattr(self, 'instance', None)
        if instancia is None or instancia.pk is None:
            return None
        return getattr(instancia, self.RELACION, None)

    @property
    def campo_extra(self):
        return self[self.CAMPO_EXTRA]

    # ---- validaciones -----------------------------------------------------
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        usuarios = Usuario.objects.filter(email__iexact=email)
        if getattr(self, 'instance', None) is not None and self.instance.pk:
            usuarios = usuarios.exclude(pk=self.instance.pk)
        if usuarios.exists():
            raise forms.ValidationError('Ya existe un usuario registrado con este correo electrónico.')
        return email

    def clean_first_name(self):
        return self.cleaned_data['first_name'].strip()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].strip()

    def clean_numero_documento(self):
        numero = self.cleaned_data['numero_documento'].strip().replace(' ', '')
        if not numero.isalnum():
            raise forms.ValidationError('El número de documento solo puede contener letras y números.')
        if len(numero) < 5:
            raise forms.ValidationError('El número de documento debe tener al menos 5 caracteres.')
        return numero.upper()

    def clean_telefono(self):
        return self.cleaned_data['telefono'].strip()

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo_documento')
        numero = cleaned.get('numero_documento')

        if tipo and numero:
            if tipo != 'PAS' and not numero.isdigit():
                self.add_error('numero_documento', 'Para este tipo de documento solo se permiten números.')
            else:
                existentes = self.PERFIL.objects.filter(tipo_documento=tipo, numero_documento=numero)
                perfil = self._perfil_actual()
                if perfil is not None:
                    existentes = existentes.exclude(pk=perfil.pk)
                if existentes.exists():
                    self.add_error(
                        'numero_documento',
                        'Ya existe un registro con este tipo y número de documento.',
                    )
        return cleaned

    # ---- guardado ---------------------------------------------------------
    @transaction.atomic
    def _guardar_usuario_y_perfil(self, usuario):
        usuario.is_staff = self.ES_STAFF
        usuario.email = self.cleaned_data['email']
        usuario.save()
        datos = {
            'tipo_documento': self.cleaned_data['tipo_documento'],
            'numero_documento': self.cleaned_data['numero_documento'],
            'telefono': self.cleaned_data['telefono'],
            'direccion': self.cleaned_data.get('direccion', ''),
            self.CAMPO_EXTRA: self.cleaned_data.get(self.CAMPO_EXTRA, ''),
        }
        self.PERFIL.objects.update_or_create(usuario=usuario, defaults=datos)
        return usuario


class RegistrarPerfilForm(PerfilMixin, UserCreationForm):
    username = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese la contraseña'}),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme la contraseña'}),
    )

    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active')
        labels = {'is_active': 'Usuario activo'}
        widgets = {'is_active': forms.CheckboxInput(attrs={'class': 'switch'})}

    def save(self, commit=True):
        usuario = super().save(commit=False)  # asigna la contraseña cifrada
        return self._guardar_usuario_y_perfil(usuario)


class ModificarPerfilForm(PerfilMixin, forms.ModelForm):
    password = forms.CharField(
        label='Nueva contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar vacío para mantener la actual',
        }),
    )

    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active')
        labels = {'username': 'Nombre de usuario', 'is_active': 'Usuario activo'}
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'switch'}),
        }

    def save(self, commit=True):
        usuario = super().save(commit=False)
        nueva_password = self.cleaned_data.get('password')
        if nueva_password:
            usuario.set_password(nueva_password)
        return self._guardar_usuario_y_perfil(usuario)


# ---- Empleados ------------------------------------------------------------

class _EmpleadoMixin(forms.Form):
    ES_STAFF = True
    PERFIL = Empleado
    RELACION = 'empleado'
    CAMPO_EXTRA = 'cargo'
    TIPOS_DOCUMENTO_PERMITIDOS = ('CC', 'CE', 'PPT', 'PAS')

    cargo = _texto('Cargo', 'Cargo', required=False, max_length=100)


class RegistrarEmpleadoForm(_EmpleadoMixin, RegistrarPerfilForm):
    pass


class ModificarEmpleadoForm(_EmpleadoMixin, ModificarPerfilForm):
    pass


# ---- Clientes -------------------------------------------------------------

class _ClienteMixin(forms.Form):
    ES_STAFF = False
    PERFIL = Cliente
    RELACION = 'cliente'
    CAMPO_EXTRA = 'ciudad'

    ciudad = _texto('Ciudad', 'Ciudad', required=False, max_length=100)


class RegistrarClienteForm(_ClienteMixin, RegistrarPerfilForm):
    pass


class ModificarClienteForm(_ClienteMixin, ModificarPerfilForm):
    pass
