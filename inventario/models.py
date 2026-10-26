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
    nombre = models.CharField(max_length=150)
    nit = models.CharField('NIT', max_length=30, unique=True)
    contacto = models.CharField(max_length=150, blank=True)
    telefono = models.CharField('teléfono', max_length=30, blank=True)
    email = models.EmailField('correo electrónico', blank=True)
    direccion = models.CharField('dirección', max_length=255, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return f'{self.nombre} ({self.nit})'


class Producto(models.Model):
    codigo = models.CharField('código', max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField('descripción', blank=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, related_name='productos'
    )
    categorias = models.ManyToManyField(
        Categoria, blank=True, related_name='productos'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

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
