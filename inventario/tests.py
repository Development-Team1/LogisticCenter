from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import CaracteristicaProducto, Categoria, Producto, Proveedor

Usuario = get_user_model()


class InventarioBaseTest(TestCase):
    def setUp(self):
        self.empleado = Usuario.objects.create_user('empleado', password='Clave12345', is_staff=True)
        self.cliente = Usuario.objects.create_user('cliente', password='Clave12345')
        self.proveedor = Proveedor.objects.create(nombre='Proveedor A', nit='900123')
        self.producto = Producto.objects.create(
            codigo='P-001', nombre='Caja', precio='1500.00', stock=10, proveedor=self.proveedor
        )


class PermisosTest(InventarioBaseTest):
    def test_cliente_no_puede_gestionar_proveedores(self):
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('listar_proveedores'))
        self.assertEqual(r.status_code, 302)

    def test_cliente_puede_ver_catalogo(self):
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('catalogo'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Caja')

    def test_cliente_no_puede_registrar_caracteristicas(self):
        self.client.force_login(self.cliente)
        r = self.client.post(reverse('detalle_producto', args=[self.producto.pk]),
                             {'accion': 'caracteristica', 'nombre': 'Color', 'valor': 'Rojo'})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(CaracteristicaProducto.objects.count(), 0)


class ProveedoresTest(InventarioBaseTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.empleado)

    def test_registrar_proveedor(self):
        r = self.client.post(reverse('registrar_proveedor'), {'nombre': 'Nuevo', 'nit': '800555'})
        self.assertRedirects(r, reverse('listar_proveedores'))
        self.assertTrue(Proveedor.objects.filter(nit='800555').exists())

    def test_modificar_proveedor(self):
        self.client.post(reverse('modificar_proveedor', args=[self.proveedor.pk]),
                         {'nombre': 'Editado', 'nit': '900123'})
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.nombre, 'Editado')

    def test_no_elimina_proveedor_con_productos(self):
        self.client.post(reverse('eliminar_proveedor', args=[self.proveedor.pk]))
        self.assertTrue(Proveedor.objects.filter(pk=self.proveedor.pk).exists())

    def test_elimina_proveedor_sin_productos(self):
        libre = Proveedor.objects.create(nombre='Libre', nit='111')
        self.client.post(reverse('eliminar_proveedor', args=[libre.pk]))
        self.assertFalse(Proveedor.objects.filter(pk=libre.pk).exists())

    def test_eliminar_exige_post(self):
        r = self.client.get(reverse('eliminar_proveedor', args=[self.proveedor.pk]))
        self.assertEqual(r.status_code, 405)


class ProductosTest(InventarioBaseTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.empleado)

    def test_registrar_producto(self):
        r = self.client.post(reverse('registrar_producto'), {
            'codigo': 'P-002', 'nombre': 'Estante', 'precio': '2500.50',
            'stock': 3, 'proveedor': self.proveedor.pk,
        })
        self.assertRedirects(r, reverse('listar_productos'))
        self.assertTrue(Producto.objects.filter(codigo='P-002').exists())

    def test_precio_negativo_es_invalido(self):
        self.client.post(reverse('registrar_producto'), {
            'codigo': 'P-003', 'nombre': 'X', 'precio': '-1',
            'stock': 1, 'proveedor': self.proveedor.pk,
        })
        self.assertFalse(Producto.objects.filter(codigo='P-003').exists())

    def test_eliminar_producto(self):
        self.client.post(reverse('eliminar_producto', args=[self.producto.pk]))
        self.assertFalse(Producto.objects.filter(pk=self.producto.pk).exists())

    def test_asignar_categorias(self):
        cat = Categoria.objects.create(nombre='Embalaje')
        self.client.post(reverse('detalle_producto', args=[self.producto.pk]),
                         {'accion': 'categorias', 'categorias': [cat.pk]})
        self.assertEqual(list(self.producto.categorias.all()), [cat])

    def test_registrar_y_quitar_caracteristica(self):
        url = reverse('detalle_producto', args=[self.producto.pk])
        self.client.post(url, {'accion': 'caracteristica', 'nombre': 'Color', 'valor': 'Rojo'})
        car = self.producto.caracteristicas.get()
        self.assertEqual((car.nombre, car.valor), ('Color', 'Rojo'))
        self.client.post(reverse('eliminar_caracteristica', args=[car.pk]))
        self.assertEqual(self.producto.caracteristicas.count(), 0)

    def test_filtrar_catalogo_por_categoria(self):
        cat = Categoria.objects.create(nombre='Embalaje')
        self.producto.categorias.add(cat)
        otro = Producto.objects.create(codigo='P-009', nombre='Otro', precio='1', proveedor=self.proveedor)
        r = self.client.get(reverse('catalogo'), {'categoria': cat.pk})
        self.assertContains(r, 'Caja')
        self.assertNotContains(r, otro.nombre)
