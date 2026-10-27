from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario

from .models import Producto, ProductoProveedor, Proveedor

PROVEEDOR = {
    'nombre': 'Aceros SA', 'nit': '900111222', 'telefono': '3001112233',
    'email': 'ventas@aceros.com', 'direccion': 'Cra 5 # 6-7',
}


def fila(i, **extra):
    d = {
        f'productos-{i}-codigo': f'AC-00{i}', f'productos-{i}-nombre': f'Producto {i}',
        f'productos-{i}-descripcion': 'Descripción', f'productos-{i}-marca': 'Marca',
        f'productos-{i}-unidad_medida': 'UND',
    }
    d.update({f'productos-{i}-{k}': v for k, v in extra.items()})
    return d


def formset(*filas, total=None):
    d = {'productos-TOTAL_FORMS': str(total if total is not None else len(filas)),
         'productos-INITIAL_FORMS': '0', 'productos-MIN_NUM_FORMS': '1', 'productos-MAX_NUM_FORMS': '1000'}
    for f in filas:
        d.update(f)
    return d


class BaseTest(TestCase):
    def setUp(self):
        self.client.force_login(Usuario.objects.create_user('admin', 'a@a.com', 'x', is_staff=True))
        self.pa = Proveedor.objects.create(nombre='Prov A', nit='1', telefono='1234567', email='a@a.com', direccion='d')
        self.pb = Proveedor.objects.create(nombre='Prov B', nit='2', telefono='1234567', email='b@b.com', direccion='d')
        self.tornillo = ProductoProveedor.objects.create(
            proveedor=self.pa, codigo='A-001', nombre='Tornillo', descripcion='M8', marca='X')
        self.tuerca = ProductoProveedor.objects.create(
            proveedor=self.pb, codigo='B-001', nombre='Tuerca', descripcion='M8', marca='Y')


class ProveedorTest(BaseTest):
    def test_registro_con_lista_de_productos(self):
        r = self.client.post(reverse('registrar_proveedor'), {**PROVEEDOR, **formset(fila(0), fila(1))})
        self.assertRedirects(r, reverse('listar_proveedores'))
        self.assertEqual(Proveedor.objects.get(nit='900111222').productos.count(), 2)

    def test_todos_los_campos_obligatorios(self):
        r = self.client.post(reverse('registrar_proveedor'), {**formset(fila(0))})
        for campo in PROVEEDOR:
            self.assertIn(campo, r.context['form'].errors, campo)

    def test_exige_al_menos_un_producto(self):
        r = self.client.post(reverse('registrar_proveedor'), {**PROVEEDOR, **formset(total=0)})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Proveedor.objects.filter(nit='900111222').exists())

    def test_campos_del_producto_obligatorios(self):
        r = self.client.post(reverse('registrar_proveedor'), {**PROVEEDOR, **formset(fila(0, descripcion='', marca=''))})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Proveedor.objects.filter(nit='900111222').exists())

    def test_codigo_unico_global_y_dentro_de_la_lista(self):
        r = self.client.post(reverse('registrar_proveedor'), {**PROVEEDOR, **formset(fila(0, codigo='A-001'))})
        self.assertEqual(r.status_code, 200)  # ya lo usa otro proveedor
        r = self.client.post(reverse('registrar_proveedor'), {**PROVEEDOR, **formset(fila(0, codigo='N-1'), fila(1, codigo='N-1'))})
        self.assertEqual(r.status_code, 200)  # repetido en la misma lista
        self.assertFalse(Proveedor.objects.filter(nit='900111222').exists())

    def test_agregar_y_modificar_producto_de_la_lista(self):
        url = reverse('detalle_proveedor', args=[self.pa.pk])
        datos = {'codigo': 'a-002', 'nombre': 'Arandela', 'descripcion': 'd', 'marca': 'm', 'unidad_medida': 'UND'}
        self.assertRedirects(self.client.post(url, datos), url)
        nuevo = ProductoProveedor.objects.get(codigo='A-002')  # el código se normaliza a mayúsculas
        # nombre repetido en el mismo proveedor
        r = self.client.post(url, {**datos, 'codigo': 'A-003'})
        self.assertIn('nombre', r.context['form'].errors)
        # el código no se puede cambiar al editar
        self.client.post(reverse('modificar_producto_proveedor', args=[nuevo.pk]), {**datos, 'codigo': 'ZZZ', 'marca': 'otra'})
        nuevo.refresh_from_db()
        self.assertEqual((nuevo.codigo, nuevo.marca), ('A-002', 'otra'))
        # nombre repetido al editar
        r = self.client.post(reverse('modificar_producto_proveedor', args=[nuevo.pk]), {**datos, 'nombre': 'Tornillo'})
        self.assertIn('nombre', r.context['form'].errors)

    def test_no_se_elimina_producto_ya_en_inventario(self):
        Producto.objects.create(referencia=self.tornillo, precio=1, stock=1)
        self.client.post(reverse('eliminar_producto_proveedor', args=[self.tornillo.pk]))
        self.assertTrue(ProductoProveedor.objects.filter(pk=self.tornillo.pk).exists())
        self.client.post(reverse('eliminar_proveedor', args=[self.pa.pk]))
        self.assertTrue(Proveedor.objects.filter(pk=self.pa.pk).exists())
        self.client.post(reverse('eliminar_proveedor', args=[self.pb.pk]))  # sin inventario: se elimina con su lista
        self.assertFalse(Proveedor.objects.filter(pk=self.pb.pk).exists())


class ProductoTest(BaseTest):
    url = 'registrar_producto'

    def datos(self, **extra):
        return {'proveedor': self.pa.pk, 'nombre': 'Tornillo', 'codigo': 'A-001', 'precio': '1500.50', 'stock': '10', **extra}

    def test_registro_correcto(self):
        r = self.client.post(reverse(self.url), self.datos(codigo='a-001', nombre='tornillo'))
        self.assertRedirects(r, reverse('listar_productos'))
        p = Producto.objects.get()
        self.assertEqual((p.codigo, p.nombre, p.proveedor), ('A-001', 'Tornillo', self.pa))
        self.assertEqual(p.precio, Decimal('1500.50'))

    def test_codigo_de_otro_proveedor(self):
        r = self.client.post(reverse(self.url), self.datos(codigo='B-001', nombre='Tuerca'))
        self.assertIn('codigo', r.context['form'].errors)
        self.assertIn('otro proveedor', r.context['form'].errors['codigo'][0])
        self.assertFalse(Producto.objects.exists())

    def test_codigo_inexistente(self):
        r = self.client.post(reverse(self.url), self.datos(codigo='NO-EXISTE'))
        self.assertIn('codigo', r.context['form'].errors)

    def test_codigo_no_coincide_con_el_nombre(self):
        r = self.client.post(reverse(self.url), self.datos(nombre='Tuerca'))
        self.assertIn('nombre', r.context['form'].errors)
        self.assertFalse(Producto.objects.exists())

    def test_no_se_registra_dos_veces(self):
        self.client.post(reverse(self.url), self.datos())
        r = self.client.post(reverse(self.url), self.datos())
        self.assertIn('codigo', r.context['form'].errors)
        self.assertEqual(Producto.objects.count(), 1)

    def test_autocompletado_solo_ofrece_productos_del_proveedor(self):
        r = self.client.get(reverse(self.url))
        cat = r.context['catalogo']
        self.assertEqual([p['codigo'] for p in cat[str(self.pa.pk)]], ['A-001'])
        self.assertEqual([p['codigo'] for p in cat[str(self.pb.pk)]], ['B-001'])
        self.client.post(reverse(self.url), self.datos())
        cat = self.client.get(reverse(self.url)).context['catalogo']
        self.assertNotIn(str(self.pa.pk), cat)  # ya registrado: no se vuelve a ofrecer
        self.assertContains(r, 'catalogo-data')

    def test_modificar_solo_precio_y_stock(self):
        self.client.post(reverse(self.url), self.datos())
        p = Producto.objects.get()
        r = self.client.get(reverse('modificar_producto', args=[p.pk]))
        form = r.context['form']
        for campo in ('proveedor', 'nombre', 'codigo'):
            self.assertTrue(form.fields[campo].disabled, campo)
        self.assertNotIn('categorias', form.fields)
        # Aunque se intente alterar código, nombre y proveedor, se ignoran.
        self.client.post(reverse('modificar_producto', args=[p.pk]), {
            'proveedor': self.pb.pk, 'nombre': 'Tuerca', 'codigo': 'B-001', 'precio': '2000', 'stock': '3'})
        p.refresh_from_db()
        self.assertEqual((p.codigo, p.nombre, p.proveedor), ('A-001', 'Tornillo', self.pa))
        self.assertEqual((p.precio, p.stock), (Decimal('2000'), 3))

    def test_listado_catalogo_y_detalle(self):
        self.client.post(reverse(self.url), self.datos())
        p = Producto.objects.get()
        for nombre, args in (('listar_productos', []), ('catalogo', []), ('detalle_producto', [p.pk]),
                             ('listar_proveedores', []), ('detalle_proveedor', [self.pa.pk]),
                             ('registrar_proveedor', []), ('modificar_proveedor', [self.pa.pk]),
                             ('modificar_producto_proveedor', [self.tornillo.pk])):
            self.assertEqual(self.client.get(reverse(nombre, args=args)).status_code, 200, nombre)
        self.assertContains(self.client.get(reverse('listar_productos') + '?q=A-001'), 'Tornillo')
        self.assertContains(self.client.get(reverse('catalogo') + '?q=tornillo'), 'Tornillo')
