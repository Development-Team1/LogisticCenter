from django.test import TestCase
from django.urls import reverse

from .models import Cliente, Empleado, Usuario

DATOS_BASE = {
    'username': 'persona1',
    'password1': 'ClaveSegura-2026',
    'password2': 'ClaveSegura-2026',
    'first_name': 'Ana',
    'last_name': 'Pérez',
    'email': 'ana@example.com',
    'tipo_documento': 'CC',
    'numero_documento': '1020304050',
    'telefono': '3001234567',
    'direccion': 'Calle 1 # 2-3',
    'is_active': 'on',
}


class BaseTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            'admin', 'admin@example.com', 'x', is_staff=True, first_name='A', last_name='B')
        self.client.force_login(self.admin)


class RegistroEmpleadoTest(BaseTest):
    url = 'registrar_empleado'

    def test_registra_empleado_con_perfil_y_tipo_fijo(self):
        # Aunque se intente enviar is_staff=False, el registro de empleados siempre crea un empleado.
        r = self.client.post(reverse(self.url), {**DATOS_BASE, 'cargo': 'Bodeguero', 'is_staff': ''})
        self.assertRedirects(r, reverse('listar_empleados'))
        u = Usuario.objects.get(username='persona1')
        self.assertTrue(u.is_staff)
        self.assertEqual(u.empleado.cargo, 'Bodeguero')
        self.assertEqual(u.empleado.numero_documento, '1020304050')
        self.assertFalse(Cliente.objects.filter(usuario=u).exists())

    def test_campos_obligatorios(self):
        r = self.client.post(reverse(self.url), {'username': 'x', 'password1': 'a', 'password2': 'a'})
        for campo in ('first_name', 'last_name', 'email', 'tipo_documento', 'numero_documento', 'telefono'):
            self.assertIn(campo, r.context['form'].errors, campo)
        # El cargo y la dirección no son obligatorios.
        self.assertNotIn('cargo', r.context['form'].errors)
        self.assertNotIn('direccion', r.context['form'].errors)

    def test_correo_unico_sin_importar_mayusculas(self):
        Usuario.objects.create_user('otro', 'ANA@example.com', 'x')
        r = self.client.post(reverse(self.url), DATOS_BASE)
        self.assertIn('email', r.context['form'].errors)
        self.assertFalse(Usuario.objects.filter(username='persona1').exists())

    def test_correo_unico_entre_empleado_y_cliente(self):
        self.client.post(reverse('registrar_cliente'), {**DATOS_BASE, 'ciudad': 'Cali'})
        r = self.client.post(reverse(self.url), {**DATOS_BASE, 'username': 'persona2', 'numero_documento': '999999'})
        self.assertIn('email', r.context['form'].errors)

    def test_documento_unico_por_tipo(self):
        self.client.post(reverse(self.url), DATOS_BASE)
        r = self.client.post(reverse(self.url), {**DATOS_BASE, 'username': 'p2', 'email': 'otro@example.com'})
        self.assertIn('numero_documento', r.context['form'].errors)

    def test_documento_numerico_salvo_pasaporte(self):
        r = self.client.post(reverse(self.url), {**DATOS_BASE, 'numero_documento': 'AB12345'})
        self.assertIn('numero_documento', r.context['form'].errors)
        r = self.client.post(reverse(self.url), {**DATOS_BASE, 'tipo_documento': 'PAS', 'numero_documento': 'AB12345'})
        self.assertRedirects(r, reverse('listar_empleados'))

    def test_telefono_invalido(self):
        r = self.client.post(reverse(self.url), {**DATOS_BASE, 'telefono': 'abc'})
        self.assertIn('telefono', r.context['form'].errors)


class RegistroClienteTest(BaseTest):
    def test_registra_cliente_con_ciudad(self):
        r = self.client.post(reverse('registrar_cliente'), {**DATOS_BASE, 'ciudad': 'Medellín'})
        self.assertRedirects(r, reverse('listar_clientes'))
        u = Usuario.objects.get(username='persona1')
        self.assertFalse(u.is_staff)
        self.assertEqual(u.cliente.ciudad, 'Medellín')
        self.assertEqual(u.cliente.direccion, 'Calle 1 # 2-3')
        self.assertFalse(Empleado.objects.filter(usuario=u).exists())

    def test_cliente_acepta_nit(self):
        r = self.client.post(reverse('registrar_cliente'), {**DATOS_BASE, 'tipo_documento': 'NIT', 'numero_documento': '900123456'})
        self.assertRedirects(r, reverse('listar_clientes'))

    def test_empleado_no_acepta_nit(self):
        r = self.client.post(reverse('registrar_empleado'), {**DATOS_BASE, 'tipo_documento': 'NIT', 'numero_documento': '900123456'})
        self.assertIn('tipo_documento', r.context['form'].errors)


class ModificacionTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.client.post(reverse('registrar_empleado'), {**DATOS_BASE, 'cargo': 'Jefe'})
        self.client.post(reverse('registrar_cliente'), {
            **DATOS_BASE, 'username': 'cli', 'email': 'cli@example.com', 'numero_documento': '777777', 'ciudad': 'Cali'})
        self.emp = Usuario.objects.get(username='persona1')
        self.cli = Usuario.objects.get(username='cli')

    def datos(self, **extra):
        d = {k: v for k, v in DATOS_BASE.items() if not k.startswith('password')}
        return {**d, **extra}

    def test_empleado_no_se_abre_desde_clientes_y_viceversa(self):
        self.assertEqual(self.client.get(reverse('modificar_cliente', args=[self.emp.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('modificar_empleado', args=[self.cli.pk])).status_code, 404)

    def test_tipo_de_usuario_no_se_puede_cambiar(self):
        r = self.client.post(reverse('modificar_empleado', args=[self.emp.pk]),
                             self.datos(is_staff='', tipo_usuario='Cliente', cargo='Nuevo'))
        self.assertEqual(r.status_code, 302)
        self.emp.refresh_from_db()
        self.assertTrue(self.emp.is_staff)
        self.assertEqual(self.emp.empleado.cargo, 'Nuevo')

        r = self.client.post(reverse('modificar_cliente', args=[self.cli.pk]),
                             self.datos(username='cli', email='cli@example.com', numero_documento='777777',
                                        is_staff='on', ciudad='Bogotá'))
        self.assertEqual(r.status_code, 302)
        self.cli.refresh_from_db()
        self.assertFalse(self.cli.is_staff)
        self.assertEqual(self.cli.cliente.ciudad, 'Bogotá')

    def test_el_campo_tipo_esta_deshabilitado_en_el_formulario(self):
        r = self.client.get(reverse('modificar_empleado', args=[self.emp.pk]))
        self.assertTrue(r.context['form'].fields['tipo_usuario'].disabled)
        self.assertNotIn('is_staff', r.context['form'].fields)
        self.assertContains(r, 'disabled')

    def test_correo_unico_al_modificar(self):
        r = self.client.post(reverse('modificar_empleado', args=[self.emp.pk]), self.datos(email='cli@example.com'))
        self.assertIn('email', r.context['form'].errors)
        # Conservar el propio correo sí es válido.
        r = self.client.post(reverse('modificar_empleado', args=[self.emp.pk]), self.datos())
        self.assertEqual(r.status_code, 302)

    def test_usuario_antiguo_sin_perfil_debe_completar_datos(self):
        viejo = Usuario.objects.create_user('viejo', 'viejo@example.com', 'x', is_staff=True,
                                            first_name='V', last_name='J')
        # Aparece en la lista aunque no tenga perfil.
        self.assertContains(self.client.get(reverse('listar_empleados')), 'viejo')
        r = self.client.post(reverse('modificar_empleado', args=[viejo.pk]),
                             {'username': 'viejo', 'first_name': 'V', 'last_name': 'J', 'email': 'viejo@example.com'})
        self.assertIn('numero_documento', r.context['form'].errors)
        r = self.client.post(reverse('modificar_empleado', args=[viejo.pk]), {
            'username': 'viejo', 'first_name': 'V', 'last_name': 'J', 'email': 'viejo@example.com',
            'tipo_documento': 'CC', 'numero_documento': '55555', 'telefono': '3111111111', 'is_active': 'on'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Empleado.objects.get(usuario=viejo).numero_documento, '55555')


class ListasTest(BaseTest):
    def test_listas_separadas(self):
        self.client.post(reverse('registrar_empleado'), {**DATOS_BASE, 'cargo': 'Jefe'})
        self.client.post(reverse('registrar_cliente'), {
            **DATOS_BASE, 'username': 'cli', 'email': 'cli@example.com', 'numero_documento': '777777', 'ciudad': 'Cali'})
        emp = self.client.get(reverse('listar_empleados'))
        cli = self.client.get(reverse('listar_clientes'))
        self.assertContains(emp, 'persona1'); self.assertNotContains(emp, 'cli@example.com')
        self.assertContains(cli, 'cli@example.com'); self.assertNotContains(cli, 'persona1')
        self.assertContains(emp, 'Jefe'); self.assertContains(cli, 'Cali')

    def test_solo_empleados_acceden(self):
        self.client.force_login(Usuario.objects.create_user('c', 'c@example.com', 'x'))
        for nombre in ('listar_empleados', 'listar_clientes', 'registrar_empleado', 'registrar_cliente'):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 302, nombre)

    def test_dashboard_y_menu(self):
        r = self.client.get(reverse('dashboard'))
        self.assertContains(r, 'Registrar empleado'); self.assertContains(r, 'Registrar cliente')
