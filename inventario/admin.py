from django.contrib import admin

from .models import CaracteristicaProducto, Categoria, Producto, ProductoProveedor, Proveedor

admin.site.register(Categoria)
admin.site.register(Proveedor)
admin.site.register(ProductoProveedor)
admin.site.register(Producto)
admin.site.register(CaracteristicaProducto)
