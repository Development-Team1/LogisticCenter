from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    # Todos los datos del proveedor son obligatorios.
    nombre = models.CharField(max_length=150)
    nit = models.CharField('NIT', max_length=30, unique=True)
    telefono = models.CharField('teléfono', max_length=30)
    email = models.EmailField('correo electrónico')
    direccion = models.CharField('dirección', max_length=255)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return f'{self.nombre} ({self.nit})'


class ProductoProveedor(models.Model):
    """Producto de la lista (catálogo) de un proveedor.

    Cada proveedor tiene su propia lista. El código es único en todo el sistema,
    por lo que identifica a un único producto de un único proveedor.
    """

    UNIDADES = [
        ('UND', 'Unidad'),
        ('CJA', 'Caja'),
        ('PAQ', 'Paquete'),
        ('KG', 'Kilogramo'),
        ('LT', 'Litro'),
        ('MT', 'Metro'),
    ]

    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.CASCADE, related_name='productos'
    )
    codigo = models.CharField(
        'código', max_length=50, unique=True,
        error_messages={'unique': 'Ya existe un producto con este código.'},
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField('descripción')
    marca = models.CharField(max_length=100)
    unidad_medida = models.CharField('unidad de medida', max_length=3, choices=UNIDADES, default='UND')

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Producto del proveedor'
        verbose_name_plural = 'Productos del proveedor'
        constraints = [
            models.UniqueConstraint(
                fields=['proveedor', 'nombre'],
                name='producto_proveedor_nombre_unico',
                violation_error_message='Este proveedor ya tiene un producto con ese nombre.',
            )
        ]

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class Producto(models.Model):
    """Producto en inventario.

    Nace siempre de un producto de la lista de un proveedor (`referencia`), de modo
    que código, nombre y proveedor siempre son coherentes entre sí. Una vez
    registrado solo se modifican el precio y el stock.
    """

    referencia = models.OneToOneField(
        ProductoProveedor, on_delete=models.PROTECT, related_name='inventario'
    )
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    categorias = models.ManyToManyField(
        Categoria, blank=True, related_name='productos'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['referencia__nombre']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    # Los datos de identificación viven en la referencia del proveedor.
    @property
    def codigo(self):
        return self.referencia.codigo

    @property
    def nombre(self):
        return self.referencia.nombre

    @property
    def descripcion(self):
        return self.referencia.descripcion

    @property
    def marca(self):
        return self.referencia.marca

    @property
    def unidad_medida(self):
        return self.referencia.get_unidad_medida_display()

    @property
    def proveedor(self):
        return self.referencia.proveedor

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class CaracteristicaProducto(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='caracteristicas'
    )
    nombre = models.CharField(max_length=100)
    valor = models.CharField(max_length=200)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Característica'
        verbose_name_plural = 'Características'

    def __str__(self):
        return f'{self.nombre}: {self.valor}'
