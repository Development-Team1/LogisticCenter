from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

TIPOS_DOCUMENTO = [
    ('CC', 'Cédula de ciudadanía'),
    ('CE', 'Cédula de extranjería'),
    ('TI', 'Tarjeta de identidad'),
    ('PPT', 'Permiso por protección temporal'),
    ('PAS', 'Pasaporte'),
    ('NIT', 'NIT'),
]

validar_telefono = RegexValidator(
    r'^\+?[0-9 ]{7,15}$',
    'Ingrese un teléfono válido: entre 7 y 15 dígitos (puede iniciar con +).',
)


class Usuario(AbstractUser):
    user_id = models.AutoField(primary_key=True)

    # El correo identifica a la persona: no puede repetirse entre usuarios.
    email = models.EmailField(
        'correo electrónico',
        unique=True,
        error_messages={'unique': 'Ya existe un usuario registrado con este correo electrónico.'},
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    @property
    def tipo_usuario(self):
        return 'Empleado' if self.is_staff else 'Cliente'


class DatosPersona(models.Model):
    """Datos de identificación y contacto comunes a empleados y clientes."""

    tipo_documento = models.CharField('tipo de documento', max_length=3, choices=TIPOS_DOCUMENTO)
    numero_documento = models.CharField('número de documento', max_length=20)
    telefono = models.CharField('teléfono', max_length=20, validators=[validar_telefono])
    direccion = models.CharField('dirección', max_length=255, blank=True)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['tipo_documento', 'numero_documento'],
                name='%(app_label)s_%(class)s_documento_unico',
            )
        ]


class Empleado(DatosPersona):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='empleado')
    cargo = models.CharField(max_length=100, blank=True)

    class Meta(DatosPersona.Meta):
        db_table = 'empleados'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        return f'{self.usuario.get_full_name()} ({self.cargo or "sin cargo"})'


class Cliente(DatosPersona):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='cliente')
    ciudad = models.CharField(max_length=100, blank=True)

    class Meta(DatosPersona.Meta):
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username
