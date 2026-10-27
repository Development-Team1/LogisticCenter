/* Registro de productos: al elegir un proveedor se ofrecen solo los productos de su
   lista; al elegir el nombre se completa el código y viceversa. La validación real
   (código ↔ proveedor ↔ nombre) se repite siempre en el servidor. */
(function () {
  'use strict';

  var datos = document.getElementById('catalogo-data');
  var proveedor = document.getElementById('id_proveedor');
  var nombre = document.getElementById('id_nombre');
  var codigo = document.getElementById('id_codigo');
  var listaNombres = document.getElementById('opciones-nombre');
  var listaCodigos = document.getElementById('opciones-codigo');
  var info = document.getElementById('info-producto');
  if (!datos || !proveedor || !nombre || !codigo) { return; }

  var catalogo = JSON.parse(datos.textContent);

  function productos() { return catalogo[proveedor.value] || []; }

  function normal(t) { return (t || '').trim().toLowerCase(); }

  function buscar(campo, valor) {
    var v = normal(valor);
    if (!v) { return null; }
    var lista = productos();
    for (var i = 0; i < lista.length; i++) {
      if (normal(lista[i][campo]) === v) { return lista[i]; }
    }
    return null;
  }

  function mostrarInfo(p) {
    if (!info) { return; }
    if (p) {
      info.textContent = p.descripcion + ' · Marca: ' + p.marca + ' · Unidad: ' + p.unidad;
      info.hidden = false;
    } else {
      info.hidden = true;
    }
  }

  function opciones() {
    listaNombres.innerHTML = '';
    listaCodigos.innerHTML = '';
    productos().forEach(function (p) {
      var a = document.createElement('option');
      a.value = p.nombre; a.label = p.codigo;
      listaNombres.appendChild(a);
      var b = document.createElement('option');
      b.value = p.codigo; b.label = p.nombre;
      listaCodigos.appendChild(b);
    });
  }

  function estado() {
    var sinProveedor = !proveedor.value;
    nombre.disabled = sinProveedor;
    codigo.disabled = sinProveedor;
    nombre.placeholder = sinProveedor ? 'Seleccione primero un proveedor' : 'Escriba o elija un producto';
    codigo.placeholder = sinProveedor ? 'Seleccione primero un proveedor' : 'Escriba o elija un código';
    if (!sinProveedor && !productos().length) {
      nombre.placeholder = codigo.placeholder = 'Este proveedor no tiene productos disponibles';
    }
  }

  proveedor.addEventListener('change', function () {
    // Si lo escrito no pertenece al nuevo proveedor, se limpia para evitar combinaciones erróneas.
    if (!buscar('nombre', nombre.value) || !buscar('codigo', codigo.value)) {
      nombre.value = ''; codigo.value = '';
    }
    opciones(); estado(); mostrarInfo(null);
  });

  nombre.addEventListener('input', function () {
    var p = buscar('nombre', nombre.value);
    if (p) { codigo.value = p.codigo; }
    mostrarInfo(p);
  });

  codigo.addEventListener('input', function () {
    var p = buscar('codigo', codigo.value);
    if (p) { nombre.value = p.nombre; }
    mostrarInfo(p);
  });

  opciones();
  estado();
  mostrarInfo(buscar('codigo', codigo.value));
})();
