import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """El producto en inventario deja de duplicar código, nombre, descripción y proveedor."""

    dependencies = [
        ('inventario', '0003_copiar_productos_a_listas'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='producto',
            options={'ordering': ['referencia__nombre'], 'verbose_name': 'Producto', 'verbose_name_plural': 'Productos'},
        ),
        migrations.RemoveField(model_name='producto', name='codigo'),
        migrations.RemoveField(model_name='producto', name='nombre'),
        migrations.RemoveField(model_name='producto', name='descripcion'),
        migrations.RemoveField(model_name='producto', name='proveedor'),
        migrations.AlterField(
            model_name='producto', name='referencia',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='inventario', to='inventario.productoproveedor',
            ),
        ),
    ]
