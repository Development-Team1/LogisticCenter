from django.db import migrations


def copiar(apps, schema_editor):
    """Cada producto ya registrado pasa a formar parte de la lista de su proveedor."""
    Producto = apps.get_model('inventario', 'Producto')
    ProductoProveedor = apps.get_model('inventario', 'ProductoProveedor')

    for producto in Producto.objects.all():
        producto.referencia = ProductoProveedor.objects.create(
            proveedor_id=producto.proveedor_id,
            codigo=producto.codigo,
            nombre=producto.nombre,
            descripcion=producto.descripcion or producto.nombre,
            marca='Sin especificar',
            unidad_medida='UND',
        )
        producto.save(update_fields=['referencia'])


def revertir(apps, schema_editor):
    Producto = apps.get_model('inventario', 'Producto')
    for producto in Producto.objects.select_related('referencia'):
        ref = producto.referencia
        producto.codigo, producto.nombre = ref.codigo, ref.nombre
        producto.descripcion, producto.proveedor_id = ref.descripcion, ref.proveedor_id
        producto.save()


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0002_productoproveedor'),
    ]

    operations = [
        migrations.RunPython(copiar, revertir),
    ]
