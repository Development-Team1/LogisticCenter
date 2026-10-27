/* Logistic Center — comportamiento de la interfaz (menú, modales, avisos). */
(function () {
  'use strict';

  var body = document.body;
  var lastFocus = null;

  /* ---- Menú en móvil ---------------------------------------------------- */
  var toggle = document.querySelector('.nav-toggle');
  var menu = document.getElementById('menu');
  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      var abierto = menu.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', abierto ? 'true' : 'false');
    });
  }

  /* ---- Modales ---------------------------------------------------------- */
  function abrirModal(id, disparador) {
    var modal = document.getElementById(id);
    if (!modal) { return null; }
    lastFocus = disparador || document.activeElement;
    modal.hidden = false;
    body.classList.add('has-modal');
    var inicial = modal.querySelector('[data-autofocus]') || modal.querySelector('button, a[href]');
    if (inicial) { inicial.focus(); }
    return modal;
  }

  function cerrarModal(modal) {
    modal.hidden = true;
    if (!document.querySelector('.modal:not([hidden])')) {
      body.classList.remove('has-modal');
    }
    if (lastFocus && typeof lastFocus.focus === 'function') { lastFocus.focus(); }
  }

  function texto(modal, selector, valor) {
    var el = modal.querySelector(selector);
    if (el && valor) { el.textContent = valor; }
  }

  document.addEventListener('click', function (e) {
    var abrir = e.target.closest('[data-open-modal]');
    if (abrir) {
      e.preventDefault();
      abrirModal(abrir.getAttribute('data-open-modal'), abrir);
      return;
    }

    /* Eliminar: el botón trae la URL de destino y los textos del aviso. */
    var eliminar = e.target.closest('[data-delete-url]');
    if (eliminar) {
      var m = document.getElementById('modal-eliminar');
      if (m) {
        texto(m, '[data-modal-title]', eliminar.getAttribute('data-title'));
        texto(m, '[data-modal-text]', eliminar.getAttribute('data-text'));
        m.querySelector('form').action = eliminar.getAttribute('data-delete-url');
        abrirModal('modal-eliminar', eliminar);
      }
      return;
    }

    /* Activar / inactivar: el enlace conserva su href como alternativa sin JS. */
    var estado = e.target.closest('[data-state-url]');
    if (estado) {
      var s = document.getElementById('modal-estado');
      if (s) {
        e.preventDefault();
        texto(s, '[data-modal-title]', estado.getAttribute('data-title'));
        texto(s, '[data-modal-text]', estado.getAttribute('data-text'));
        texto(s, '[data-state-confirm]', estado.getAttribute('data-confirm-label'));
        s.querySelector('[data-state-confirm]').href = estado.getAttribute('data-state-url');
        abrirModal('modal-estado', estado);
      }
      return;
    }

    var cerrar = e.target.closest('[data-close-modal]');
    if (cerrar) {
      cerrarModal(cerrar.closest('.modal'));
      return;
    }

    if (e.target.classList && e.target.classList.contains('modal')) {
      cerrarModal(e.target);
    }
  });

  document.addEventListener('keydown', function (e) {
    var abierto = document.querySelector('.modal:not([hidden])');
    if (!abierto) { return; }

    if (e.key === 'Escape') {
      cerrarModal(abierto);
      return;
    }

    if (e.key === 'Tab') {
      var items = abierto.querySelectorAll('button, a[href], input, select, textarea');
      if (!items.length) { return; }
      var primero = items[0];
      var ultimo = items[items.length - 1];
      if (e.shiftKey && document.activeElement === primero) {
        e.preventDefault(); ultimo.focus();
      } else if (!e.shiftKey && document.activeElement === ultimo) {
        e.preventDefault(); primero.focus();
      }
    }
  });

  /* ---- Avisos (toasts) -------------------------------------------------- */
  function quitarAviso(aviso) {
    aviso.classList.add('is-leaving');
    setTimeout(function () { if (aviso.parentNode) { aviso.parentNode.removeChild(aviso); } }, 260);
  }

  document.querySelectorAll('.toast').forEach(function (aviso) {
    aviso.addEventListener('click', function () { quitarAviso(aviso); });
    setTimeout(function () { quitarAviso(aviso); }, 6000);
  });

  /* ---- Lista de productos al registrar un proveedor (formset) ----------- */
  var lista = document.getElementById('lista-productos');
  var plantilla = document.getElementById('plantilla-producto');
  var agregar = document.getElementById('agregar-producto');
  if (lista && plantilla && agregar) {
    var prefijo = lista.getAttribute('data-prefix');
    var total = document.getElementById('id_' + prefijo + '-TOTAL_FORMS');

    function filas() { return lista.querySelectorAll('[data-fila]'); }

    // Renumera filas, nombres e ids para que el formset siga siendo consecutivo.
    function renumerar() {
      var patron = new RegExp('(' + prefijo + '-)(\\d+|__prefix__)(-)', 'g');
      filas().forEach(function (fila, i) {
        fila.querySelectorAll('[name], [id], label[for]').forEach(function (el) {
          ['name', 'id', 'for'].forEach(function (a) {
            var v = el.getAttribute(a);
            if (v) {
              el.setAttribute(a, v.replace(new RegExp(prefijo + '-(\\d+)-', 'g'), prefijo + '-' + i + '-'));
            }
          });
        });
        fila.querySelector('[data-numero]').textContent = i + 1;
      });
      total.value = filas().length;
      var unica = filas().length <= 1;
      lista.querySelectorAll('[data-quitar-producto]').forEach(function (b) { b.hidden = unica; });
    }

    agregar.addEventListener('click', function () {
      var indice = filas().length;
      var html = plantilla.innerHTML
        .replace(/__prefix__/g, indice)
        .replace(/__num__/g, indice + 1);
      lista.insertAdjacentHTML('beforeend', html);
      renumerar();
      var campo = lista.lastElementChild.querySelector('input:not([type=hidden])');
      if (campo) { campo.focus(); }
    });

    lista.addEventListener('click', function (e) {
      var boton = e.target.closest('[data-quitar-producto]');
      if (!boton || filas().length <= 1) { return; }
      boton.closest('[data-fila]').remove();
      renumerar();
    });

    renumerar();
  }
})();
