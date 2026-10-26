from django.urls import path

from . import views

urlpatterns = [
    # Proveedores
    path('proveedores/', views.ListarProveedoresView, name='listar_proveedores'),
    path('proveedores/registrar/', views.RegistrarProveedorView, name='registrar_proveedor'),
    path('proveedores/<int:pk>/modificar/', views.ModificarProveedorView, name='modificar_proveedor'),
    path('proveedores/<int:pk>/eliminar/', views.EliminarProveedorView, name='eliminar_proveedor'),

    # Categorías
    path('categorias/', views.CategoriasView, name='categorias'),
    path('categorias/<int:pk>/eliminar/', views.EliminarCategoriaView, name='eliminar_categoria'),

    # Productos (gestión)
    path('productos/', views.ListarProductosView, name='listar_productos'),
    path('productos/registrar/', views.RegistrarProductoView, name='registrar_producto'),
    path('productos/<int:pk>/modificar/', views.ModificarProductoView, name='modificar_producto'),
    path('productos/<int:pk>/eliminar/', views.EliminarProductoView, name='eliminar_producto'),

    # Catálogo
    path('catalogo/', views.CatalogoView, name='catalogo'),
    path('productos/<int:pk>/', views.DetalleProductoView, name='detalle_producto'),
    path('caracteristicas/<int:pk>/eliminar/', views.EliminarCaracteristicaView, name='eliminar_caracteristica'),
]
