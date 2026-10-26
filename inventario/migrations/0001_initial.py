import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('descripcion', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Proveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
                ('nit', models.CharField(max_length=30, unique=True, verbose_name='NIT')),
                ('contacto', models.CharField(blank=True, max_length=150)),
                ('telefono', models.CharField(blank=True, max_length=30, verbose_name='teléfono')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='correo electrónico')),
                ('direccion', models.CharField(blank=True, max_length=255, verbose_name='dirección')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Proveedor',
                'verbose_name_plural': 'Proveedores',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=50, unique=True, verbose_name='código')),
                ('nombre', models.CharField(max_length=150)),
                ('descripcion', models.TextField(blank=True, verbose_name='descripción')),
                ('precio', models.DecimalField(decimal_places=2, max_digits=12)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('categorias', models.ManyToManyField(blank=True, related_name='productos', to='inventario.categoria')),
                ('proveedor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='productos', to='inventario.proveedor')),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='CaracteristicaProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('valor', models.CharField(max_length=200)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='caracteristicas', to='inventario.producto')),
            ],
            options={
                'verbose_name': 'Característica',
                'verbose_name_plural': 'Características',
                'ordering': ['nombre'],
            },
        ),
    ]
