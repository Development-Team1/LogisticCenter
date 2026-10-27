import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Crea la lista de productos de cada proveedor y la enlaza con el inventario."""

    dependencies = [
        ('inventario', '0001_initial'),
    ]

    operations = [
        # Los datos del proveedor pasan a ser obligatorios (solo cambia la validación).
        migrations.AlterField(
            model_name='proveedor', name='contacto',
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name='proveedor', name='telefono',
            field=models.CharField(max_length=30, verbose_name='teléfono'),
        ),
        migrations.AlterField(
            model_name='proveedor', name='email',
            field=models.EmailField(max_length=254, verbose_name='correo electrónico'),
        ),
        migrations.AlterField(
            model_name='proveedor', name='direccion',
            field=models.CharField(max_length=255, verbose_name='dirección'),
        ),
        # Libera el nombre `productos` para la nueva lista del proveedor.
        migrations.AlterField(
            model_name='producto', name='proveedor',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='productos_anteriores', to='inventario.proveedor',
            ),
        ),
        migrations.CreateModel(
            name='ProductoProveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(error_messages={'unique': 'Ya existe un producto con este código.'}, max_length=50, unique=True, verbose_name='código')),
                ('nombre', models.CharField(max_length=150)),
                ('descripcion', models.TextField(verbose_name='descripción')),
                ('marca', models.CharField(max_length=100)),
                ('unidad_medida', models.CharField(choices=[('UND', 'Unidad'), ('CJA', 'Caja'), ('PAQ', 'Paquete'), ('KG', 'Kilogramo'), ('LT', 'Litro'), ('MT', 'Metro')], default='UND', max_length=3, verbose_name='unidad de medida')),
                ('proveedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productos', to='inventario.proveedor')),
            ],
            options={
                'verbose_name': 'Producto del proveedor',
                'verbose_name_plural': 'Productos del proveedor',
                'ordering': ['nombre'],
            },
        ),
        migrations.AddConstraint(
            model_name='productoproveedor',
            constraint=models.UniqueConstraint(
                fields=('proveedor', 'nombre'), name='producto_proveedor_nombre_unico',
                violation_error_message='Este proveedor ya tiene un producto con ese nombre.',
            ),
        ),
        migrations.AddField(
            model_name='producto', name='referencia',
            field=models.OneToOneField(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='inventario', to='inventario.productoproveedor',
            ),
        ),
    ]
