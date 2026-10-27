from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.IniciarSesionView, name='login'),
    path('logout/', views.CerrarSesionView, name='logout'),

    # Empleados
    path('empleados/', views.ListarEmpleadosView, name='listar_empleados'),
    path('empleados/registrar/', views.RegistrarEmpleadoView, name='registrar_empleado'),
    path('empleados/<int:user_id>/modificar/', views.ModificarEmpleadoView, name='modificar_empleado'),

    # Clientes
    path('clientes/', views.ListarClientesView, name='listar_clientes'),
    path('clientes/registrar/', views.RegistrarClienteView, name='registrar_cliente'),
    path('clientes/<int:user_id>/modificar/', views.ModificarClienteView, name='modificar_cliente'),

    # Acciones comunes
    path('cambiar_estado/<int:user_id>/', views.CambiarEstadoUsuarioView, name='cambiar_estado_usuario'),
    path('eliminar_usuario/<int:user_id>/', views.EliminarUsuarioView, name='eliminar_usuario'),
]
