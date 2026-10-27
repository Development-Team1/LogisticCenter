from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    AsignarCategoriasForm,
    CaracteristicaForm,
    CategoriaForm,
    ProductoForm,
    ProductoProveedorForm,
    ProductosProveedorFormSet,
    ProveedorForm,
)
from .models import CaracteristicaProducto, Categoria, Producto, ProductoProveedor, Proveedor


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
        'volver_url': reverse(volver),
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
    """Registra el proveedor junto con su lista de productos (mínimo uno)."""
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        formset = ProductosProveedorFormSet(request.POST, instance=Proveedor())
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                proveedor = form.save()
                formset.instance = proveedor
                formset.save()
            messages.success(request, 'Proveedor registrado correctamente con su lista de productos.')
            return redirect('listar_proveedores')
        messages.error(request, 'No fue posible guardar. Verifique los datos ingresados.')
    else:
        form = ProveedorForm()
        formset = ProductosProveedorFormSet(instance=Proveedor())

    return render(request, 'inventario/registrar_proveedor.html', {
        'form': form,
        'formset': formset,
    })


@solo_staff
def ModificarProveedorView(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    return _vista_formulario(
        request, ProveedorForm, f'Modificar proveedor: {proveedor.nombre}',
        'listar_proveedores', 'Proveedor modificado correctamente.',
        instancia=proveedor,
    )


@solo_staff
def DetalleProveedorView(request, pk):
    """Lista de productos del proveedor, con formulario para agregar más."""
    proveedor = get_object_or_404(Proveedor, pk=pk)

    if request.method == 'POST':
        form = ProductoProveedorForm(request.POST, proveedor=proveedor)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.proveedor = proveedor
            producto.save()
            messages.success(request, 'Producto agregado a la lista del proveedor.')
            return redirect('detalle_proveedor', pk=proveedor.pk)
        messages.error(request, 'No fue posible agregar el producto.')
    else:
        form = ProductoProveedorForm(proveedor=proveedor)

    productos = proveedor.productos.select_related('inventario')
    return render(request, 'inventario/detalle_proveedor.html', {
        'proveedor': proveedor,
        'productos': productos,
        'form': form,
    })


@solo_staff
def ModificarProductoProveedorView(request, pk):
    producto = get_object_or_404(ProductoProveedor.objects.select_related('proveedor'), pk=pk)
    volver = reverse('detalle_proveedor', args=[producto.proveedor_id])

    if request.method == 'POST':
        form = ProductoProveedorForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto del proveedor modificado correctamente.')
            return redirect(volver)
        messages.error(request, 'No fue posible guardar. Verifique los datos ingresados.')
    else:
        form = ProductoProveedorForm(instance=producto)

    return render(request, 'inventario/formulario.html', {
        'form': form,
        'titulo': f'Modificar producto: {producto.nombre}',
        'volver_url': volver,
    })


@solo_staff
@require_POST
def EliminarProductoProveedorView(request, pk):
    producto = get_object_or_404(ProductoProveedor, pk=pk)
    proveedor_id = producto.proveedor_id
    nombre = producto.nombre

    try:
        producto.delete()
    except ProtectedError:
        messages.warning(
            request,
            f'No se puede quitar {nombre} de la lista porque ya está registrado en el inventario.',
        )
    else:
        messages.success(request, f'El producto {nombre} fue quitado de la lista del proveedor.')

    return redirect('detalle_proveedor', pk=proveedor_id)


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
            f'No se puede eliminar a {nombre} porque alguno de sus productos está registrado en el inventario.',
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
    productos = Producto.objects.select_related('referencia__proveedor').prefetch_related('categorias')

    if busqueda:
        productos = productos.filter(
            Q(referencia__nombre__icontains=busqueda)
            | Q(referencia__codigo__icontains=busqueda)
            | Q(referencia__proveedor__nombre__icontains=busqueda)
        )

    return render(request, 'inventario/listar_productos.html', {
        'productos': productos,
        'busqueda': busqueda,
    })


def _catalogo_para_autocompletar():
    """Productos de cada proveedor que aún no están en inventario, para el autocompletado."""
    catalogo = {}
    disponibles = (
        ProductoProveedor.objects.filter(inventario__isnull=True)
        .select_related('proveedor').order_by('nombre')
    )
    for p in disponibles:
        catalogo.setdefault(str(p.proveedor_id), []).append({
            'codigo': p.codigo,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'marca': p.marca,
            'unidad': p.get_unidad_medida_display(),
        })
    return catalogo


@solo_staff
def RegistrarProductoView(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto registrado correctamente.')
            return redirect('listar_productos')
        messages.error(request, 'No fue posible guardar. Verifique los datos ingresados.')
    else:
        form = ProductoForm()

    return render(request, 'inventario/formulario_producto.html', {
        'form': form,
        'titulo': 'Registrar producto',
        'catalogo': _catalogo_para_autocompletar(),
    })


@solo_staff
def ModificarProductoView(request, pk):
    producto = get_object_or_404(
        Producto.objects.select_related('referencia__proveedor'), pk=pk
    )

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto modificado correctamente.')
            return redirect('listar_productos')
        messages.error(request, 'No fue posible guardar. Verifique los datos ingresados.')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'inventario/formulario_producto.html', {
        'form': form,
        'titulo': f'Modificar producto: {producto.nombre}',
        'producto': producto,
    })


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

    productos = Producto.objects.select_related('referencia__proveedor').prefetch_related('categorias')

    if busqueda:
        productos = productos.filter(
            Q(referencia__nombre__icontains=busqueda)
            | Q(referencia__descripcion__icontains=busqueda)
            | Q(referencia__codigo__icontains=busqueda)
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
        Producto.objects.select_related('referencia__proveedor').prefetch_related(
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
