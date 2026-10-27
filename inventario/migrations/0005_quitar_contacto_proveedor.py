from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0004_producto_solo_referencia'),
    ]

    operations = [
        migrations.RemoveField(model_name='proveedor', name='contacto'),
    ]
