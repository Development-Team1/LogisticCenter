from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.IniciarSesionView, name= 'login'),
    path('logout/', views.CerrarSesionView, name= 'logout'),
    path('registrar_usuario/', views.RegistrarUsuarioView, name= 'registro'),
    path('modificar_usuario/<int:user_id>/', views.ModificarUsuarioView, name='modificar_usuario'),
    path('listar/', views.ListarUsuariosView, name='listar_usuarios'),
    path('cambiar_estado/<int:user_id>/', views.CambiarEstadoUsuarioView, name='cambiar_estado_usuario'),
    path('eliminar_usuario/<int:user_id>/', views.EliminarUsuarioView, name='eliminar_usuario')

]
