from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required,  user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import IniciarSesionForm, RegistrarUsuarioForm, ModificarUsuarioForm
from .models import Usuario

# Create your views here.

def IniciarSesionView(request):

    if request.user.is_authenticated: 
        return redirect('dashboard') 
    
    if request.method == 'POST': 
        form = IniciarSesionForm(request, data=request.POST) 
        if form.is_valid(): 
            user = form.get_user() 
            login(request, user) 
            return redirect('dashboard') 
    else: 
        form = IniciarSesionForm() 
    
    return render( request, 'login.html', {'form': form} )

   

@login_required
def CerrarSesionView(request):
    logout(request)
    return redirect('bienvenida')
    
@login_required
@user_passes_test(lambda u: u.is_staff)
def RegistrarUsuarioView(request):

    if request.method == 'POST':

        form = RegistrarUsuarioForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Usuario registrado correctamente.'
            )

            return redirect('registro')

        messages.error(
            request,
            'No fue posible registrar el usuario. Verifique los datos ingresados.'
        )

    else:

        form = RegistrarUsuarioForm()

    return render(
        request,
        'registrar_usuario.html',
        {
            'form': form
        }
    )


@login_required
@user_passes_test(lambda u: u.is_staff)
def ListarUsuariosView(request):

    busqueda = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')

    usuarios = Usuario.objects.all().order_by('user_id')

    if busqueda:
        usuarios = usuarios.filter(username__icontains=busqueda)

    if tipo == 'empleados':
        usuarios = usuarios.filter(is_staff=True)
    elif tipo == 'clientes':
        usuarios = usuarios.filter(is_staff=False)
    else:
        tipo = ''

    return render(
        request,
        'listar_usuarios.html',
        {
            'usuarios': usuarios,
            'busqueda': busqueda,
            'tipo': tipo
        }
    )

@login_required
@user_passes_test(lambda u: u.is_staff)

def ModificarUsuarioView(request, user_id):

    usuario = get_object_or_404(
        Usuario,
        user_id=user_id
    )

    if request.method == 'POST':

        form = ModificarUsuarioForm(
            request.POST,
            instance=usuario
        )

        if form.is_valid():

            usuario = form.save(commit=False)

            nueva_password = form.cleaned_data.get('password')

            if nueva_password:
                usuario.set_password(nueva_password)

            usuario.save()

            messages.success(
                request,
                'Usuario modificado correctamente.'
            )

            return redirect(
                'modificar_usuario',
                user_id=usuario.user_id
            )

        messages.error(
            request,
            'No fue posible modificar el usuario.'
        )

    else:

        form = ModificarUsuarioForm(
            instance=usuario
        )

    return render(
        request,
        'modificar_usuario.html',
        {
            'form': form,
            'usuario': usuario
        }
    )
        
@login_required
@user_passes_test(lambda u: u.is_staff)
def CambiarEstadoUsuarioView(request, user_id):

    usuario = get_object_or_404(
        Usuario,
        user_id=user_id
    )

    if usuario.is_superuser:

        messages.warning(
            request,
            'No es posible modificar el estado de un superusuario.'
        )

        return redirect('listar_usuarios')
    
    if usuario == request.user:

        messages.warning(
        request,
        'No puede cambiar el estado de su propio usuario.'
    )

        return redirect('listar_usuarios')

    usuario.is_active = not usuario.is_active

    usuario.save()

    if usuario.is_active:

        messages.success(
            request,
            f'El usuario {usuario.username} fue activado correctamente.'
        )

    else:

        messages.success(
            request,
            f'El usuario {usuario.username} fue inactivado correctamente.'
        )

    return redirect('listar_usuarios')


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def EliminarUsuarioView(request, user_id):

    usuario = get_object_or_404(
        Usuario,
        user_id=user_id
    )

    if usuario.is_superuser:

        messages.warning(
            request,
            'No es posible eliminar a un superusuario.'
        )

        return redirect('listar_usuarios')

    if usuario == request.user:

        messages.warning(
            request,
            'No puede eliminar su propio usuario.'
        )

        return redirect('listar_usuarios')

    username = usuario.username

    usuario.delete()

    messages.success(
        request,
        f'El usuario {username} fue eliminado correctamente.'
    )

    return redirect('listar_usuarios')
