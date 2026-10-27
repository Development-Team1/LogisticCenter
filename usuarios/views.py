from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required,  user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import (
    IniciarSesionForm,
    ModificarClienteForm,
    ModificarEmpleadoForm,
    RegistrarClienteForm,
    RegistrarEmpleadoForm,
)
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
    
solo_staff = lambda vista: login_required(user_passes_test(lambda u: u.is_staff)(vista))


# Configuración de cada tipo de usuario. Empleados y clientes comparten la lógica,
# pero cada uno tiene sus propias páginas (registro, lista y modificación) y su
# propio formulario; el tipo lo fija la página, nunca el usuario.
TIPOS = {
    'empleado': {
        'is_staff': True,
        'relacion': 'empleado',
        'singular': 'empleado',
        'plural': 'empleados',
        'titulo_plural': 'Empleados',
        'form_registro': RegistrarEmpleadoForm,
        'form_modificar': ModificarEmpleadoForm,
        'url_lista': 'listar_empleados',
        'url_registro': 'registrar_empleado',
        'url_modificar': 'modificar_empleado',
    },
    'cliente': {
        'is_staff': False,
        'relacion': 'cliente',
        'singular': 'cliente',
        'plural': 'clientes',
        'titulo_plural': 'Clientes',
        'form_registro': RegistrarClienteForm,
        'form_modificar': ModificarClienteForm,
        'url_lista': 'listar_clientes',
        'url_registro': 'registrar_cliente',
        'url_modificar': 'modificar_cliente',
    },
}


def _contexto(tipo, **extra):
    return {'tipo': tipo, 'cfg': TIPOS[tipo], **extra}


def _url_lista_de(usuario):
    return TIPOS['empleado' if usuario.is_staff else 'cliente']['url_lista']


def _registrar(request, tipo):
    cfg = TIPOS[tipo]

    if request.method == 'POST':
        form = cfg['form_registro'](request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'{cfg["singular"].capitalize()} registrado correctamente.')
            return redirect(cfg['url_lista'])
        messages.error(
            request,
            f'No fue posible registrar al {cfg["singular"]}. Verifique los datos ingresados.',
        )
    else:
        form = cfg['form_registro'](initial={'is_active': True})

    return render(request, 'registrar_persona.html', _contexto(tipo, form=form))


def _listar(request, tipo):
    cfg = TIPOS[tipo]
    busqueda = request.GET.get('q', '').strip()

    base = Usuario.objects.filter(is_staff=cfg['is_staff'])
    personas = base.select_related(cfg['relacion']).order_by('user_id')

    if busqueda:
        personas = personas.filter(
            Q(username__icontains=busqueda)
            | Q(first_name__icontains=busqueda)
            | Q(last_name__icontains=busqueda)
            | Q(email__icontains=busqueda)
            | Q(**{f'{cfg["relacion"]}__numero_documento__icontains': busqueda})
        )

    return render(request, 'listar_personas.html', _contexto(
        tipo, personas=personas, busqueda=busqueda, total=base.count(),
    ))


def _modificar(request, tipo, user_id):
    cfg = TIPOS[tipo]
    # Un empleado solo se edita desde empleados y un cliente solo desde clientes.
    usuario = get_object_or_404(Usuario, user_id=user_id, is_staff=cfg['is_staff'])

    if usuario.is_superuser and not request.user.is_superuser:
        messages.warning(request, 'No tiene permisos para modificar a un superusuario.')
        return redirect(cfg['url_lista'])

    if request.method == 'POST':
        form = cfg['form_modificar'](request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'{cfg["singular"].capitalize()} actualizado correctamente.')
            return redirect(cfg['url_modificar'], user_id=usuario.user_id)
        messages.error(request, f'No fue posible modificar al {cfg["singular"]}.')
    else:
        form = cfg['form_modificar'](instance=usuario)

    return render(request, 'modificar_persona.html', _contexto(tipo, form=form, usuario=usuario))


# ---- Empleados --------------------------------------------------------------

@solo_staff
def RegistrarEmpleadoView(request):
    return _registrar(request, 'empleado')


@solo_staff
def ListarEmpleadosView(request):
    return _listar(request, 'empleado')


@solo_staff
def ModificarEmpleadoView(request, user_id):
    return _modificar(request, 'empleado', user_id)


# ---- Clientes ---------------------------------------------------------------

@solo_staff
def RegistrarClienteView(request):
    return _registrar(request, 'cliente')


@solo_staff
def ListarClientesView(request):
    return _listar(request, 'cliente')


@solo_staff
def ModificarClienteView(request, user_id):
    return _modificar(request, 'cliente', user_id)


# ---- Acciones comunes (activar / inactivar / eliminar) -----------------------

@solo_staff
def CambiarEstadoUsuarioView(request, user_id):
    usuario = get_object_or_404(Usuario, user_id=user_id)
    destino = _url_lista_de(usuario)

    if usuario.is_superuser:
        messages.warning(request, 'No es posible modificar el estado de un superusuario.')
        return redirect(destino)

    if usuario == request.user:
        messages.warning(request, 'No puede cambiar el estado de su propio usuario.')
        return redirect(destino)

    usuario.is_active = not usuario.is_active
    usuario.save()

    accion = 'activado' if usuario.is_active else 'inactivado'
    messages.success(request, f'El usuario {usuario.username} fue {accion} correctamente.')
    return redirect(destino)


@solo_staff
@require_POST
def EliminarUsuarioView(request, user_id):
    usuario = get_object_or_404(Usuario, user_id=user_id)
    destino = _url_lista_de(usuario)

    if usuario.is_superuser:
        messages.warning(request, 'No es posible eliminar a un superusuario.')
        return redirect(destino)

    if usuario == request.user:
        messages.warning(request, 'No puede eliminar su propio usuario.')
        return redirect(destino)

    username = usuario.username
    usuario.delete()

    messages.success(request, f'El usuario {username} fue eliminado correctamente.')
    return redirect(destino)
