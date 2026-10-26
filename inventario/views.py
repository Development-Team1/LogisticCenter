from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AsignarCategoriasForm,
    CaracteristicaForm,
    CategoriaForm,
    ProductoForm,
    ProveedorForm,
)
from .models import CaracteristicaProducto, Categoria, Producto, Proveedor


def solo_staff(vista):
    """Exige sesión iniciada y que el usuario sea empleado (is_staff)."""
    return login_required(user_passes_test(lambda u: u.is_staff)(vista))


def _vista_formulario(request, form_class, titulo, volver, mensaje_ok, instancia=None):
    if request.method == 'POST':
        form = form_class(request.POST, instance=instancia)
        if form.is_valid():
            form.save()
            messages.success(request, mensaje_ok)
            return redirect(volver)
        messages.error(request, 'No fue posible guardar. Verifique los datos ingresados.')
    else:
        form = form_class(instance=instancia)

    return render(request, 'inventario/formulario.html', {
        'form': form,
        'titulo': titulo,
        'volver': volver,
    })


# ---------------------------------------------------------------- Proveedores

@solo_staff
def ListarProveedoresView(request):
    busqueda = request.GET.get('q', '').strip()
    proveedores = Proveedor.objects.annotate(total_productos=Count('productos'))

    if busqueda:
        proveedores = proveedores.filter(
            Q(nombre__icontains=busqueda) | Q(nit__icontains=busqueda)
        )

    return render(request, 'inventario/listar_proveedores.html', {
        'proveedores': proveedores,
        'busqueda': busqueda,
    })


@solo_staff
def RegistrarProveedorView(request):
    return _vista_formulario(
        request, ProveedorForm, 'Registrar proveedor',
        'listar_proveedores', 'Proveedor registrado correctamente.',
    )


@solo_staff
def ModificarProveedorView(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    return _vista_formulario(
        request, ProveedorForm, f'Modificar proveedor: {proveedor.nombre}',
        'listar_proveedores', 'Proveedor modificado correctamente.',
        instancia=proveedor,
    )


@solo_staff
@require_POST
def EliminarProveedorView(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    nombre = proveedor.nombre

    try:
        proveedor.delete()
    except ProtectedError:
        messages.warning(
            request,
            f'No se puede eliminar a {nombre} porque tiene productos asociados.',
        )
    else:
        messages.success(request, f'El proveedor {nombre} fue eliminado correctamente.')

    return redirect('listar_proveedores')


# ----------------------------------------------------------------- Categorías

@solo_staff
def CategoriasView(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada correctamente.')
            return redirect('categorias')
        messages.error(request, 'No fue posible crear la categoría.')
    else:
        form = CategoriaForm()

    categorias = Categoria.objects.annotate(total_productos=Count('productos'))
    return render(request, 'inventario/categorias.html', {
        'form': form,
        'categorias': categorias,
    })


@solo_staff
@require_POST
def EliminarCategoriaView(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    nombre = categoria.nombre
    categoria.delete()
    messages.success(request, f'La categoría {nombre} fue eliminada correctamente.')
    return redirect('categorias')


# ------------------------------------------------------------------ Productos

@solo_staff
def ListarProductosView(request):
    busqueda = request.GET.get('q', '').strip()
    productos = Producto.objects.select_related('proveedor').prefetch_related('categorias')

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | Q(codigo__icontains=busqueda)
        )

    return render(request, 'inventario/listar_productos.html', {
        'productos': productos,
        'busqueda': busqueda,
    })


@solo_staff
def RegistrarProductoView(request):
    return _vista_formulario(
        request, ProductoForm, 'Registrar producto',
        'listar_productos', 'Producto registrado correctamente.',
    )


@solo_staff
def ModificarProductoView(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return _vista_formulario(
        request, ProductoForm, f'Modificar producto: {producto.nombre}',
        'listar_productos', 'Producto modificado correctamente.',
        instancia=producto,
    )


@solo_staff
@require_POST
def EliminarProductoView(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    nombre = producto.nombre
    producto.delete()
    messages.success(request, f'El producto {nombre} fue eliminado correctamente.')
    return redirect('listar_productos')


# ------------------------------------------------------------------- Catálogo

@login_required
def CatalogoView(request):
    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')

    productos = Producto.objects.prefetch_related('categorias')

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    if categoria_id.isdigit():
        productos = productos.filter(categorias__pk=int(categoria_id))
    else:
        categoria_id = ''

    return render(request, 'inventario/catalogo.html', {
        'productos': productos,
        'categorias': Categoria.objects.all(),
        'busqueda': busqueda,
        'categoria_id': categoria_id,
    })


@login_required
def DetalleProductoView(request, pk):
    producto = get_object_or_404(
        Producto.objects.select_related('proveedor').prefetch_related(
            'categorias', 'caracteristicas'
        ),
        pk=pk,
    )
    form_caracteristica = CaracteristicaForm()
    form_categorias = AsignarCategoriasForm(instance=producto)

    if request.method == 'POST':
        if not request.user.is_staff:
            raise PermissionDenied

        accion = request.POST.get('accion')

        if accion == 'caracteristica':
            form_caracteristica = CaracteristicaForm(request.POST)
            if form_caracteristica.is_valid():
                caracteristica = form_caracteristica.save(commit=False)
                caracteristica.producto = producto
                caracteristica.save()
                messages.success(request, 'Característica registrada correctamente.')
                return redirect('detalle_producto', pk=producto.pk)
            messages.error(request, 'No fue posible registrar la característica.')

        elif accion == 'categorias':
            form_categorias = AsignarCategoriasForm(request.POST, instance=producto)
            if form_categorias.is_valid():
                form_categorias.save()
                messages.success(request, 'Categorías asignadas correctamente.')
                return redirect('detalle_producto', pk=producto.pk)
            messages.error(request, 'No fue posible asignar las categorías.')

    return render(request, 'inventario/detalle_producto.html', {
        'producto': producto,
        'form_caracteristica': form_caracteristica,
        'form_categorias': form_categorias,
    })


@solo_staff
@require_POST
def EliminarCaracteristicaView(request, pk):
    caracteristica = get_object_or_404(CaracteristicaProducto, pk=pk)
    producto_id = caracteristica.producto_id
    caracteristica.delete()
    messages.success(request, 'Característica eliminada correctamente.')
    return redirect('detalle_producto', pk=producto_id)
