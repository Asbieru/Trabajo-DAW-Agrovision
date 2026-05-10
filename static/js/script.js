/* ============================================================
   main.js  –  AgroVisión · Script unificado
   ============================================================
   Organización por página:
     1. GLOBAL      → base.html        (todas las páginas)
     2. LOGIN       → login.html
     3. INDICADORES → indicadores.html
     4. GESTIÓN     → GestionIncidencia.html
   ============================================================ */


/* ============================================================
   1. GLOBAL – base.html
      Menú desplegable del avatar (aplica en todas las páginas
      que extienden base.html).
   ============================================================ */

function toggleMenu() {
    document.getElementById('dropdown-menu').classList.toggle('abierto');
}

document.addEventListener('click', function (e) {
    const menu = document.getElementById('dropdown-menu');
    if (menu && !e.target.closest('.avatar-menu')) {
        menu.classList.remove('abierto');
    }
});


/* ============================================================
   2. LOGIN – login.html
      Manejo de pestañas "Ingresar / Registrarse" y apertura
      automática del panel de registro cuando Flask redirige
      con ?tab=registro en la URL.
   ============================================================ */

function mostrarTab(tab, btn) {
    // Ocultar todos los paneles y desactivar todos los botones
    document.querySelectorAll('.tab-panel').forEach(function (p) {
        p.classList.remove('activo');
    });
    document.querySelectorAll('.tab-btn').forEach(function (b) {
        b.classList.remove('activo');
    });
    // Mostrar el panel seleccionado y marcar el botón activo
    document.getElementById('panel-' + tab).classList.add('activo');
    btn.classList.add('activo');
}

// Inicialización de login: abrir pestaña de registro si Flask
// redirigió con ?tab=registro (solo se ejecuta en login.html,
// donde existe el elemento #panel-registro).
(function iniciarLogin() {
    if (!document.getElementById('panel-registro')) return; // no es login.html

    const params = new URLSearchParams(window.location.search);
    if (params.get('tab') === 'registro') {
        var botonesTab = document.querySelectorAll('.tab-btn');
        if (botonesTab.length >= 2) {
            botonesTab[1].click();
        }
    }
})();


/* ============================================================
   3. INDICADORES – indicadores.html
      Animación / dimensionado de barras de progreso y de
      tendencia (barra-w = ancho en %, barra-h = alto en px).
      Solo se ejecuta cuando existen estos elementos en el DOM.
   ============================================================ */

(function iniciarIndicadores() {
    var barrasAncho = document.querySelectorAll('.barra-w');
    if (!barrasAncho.length) return; // no es indicadores.html

    // Barras horizontales – ancho porcentual leído de data-pct
    barrasAncho.forEach(function (el) {
        el.style.height       = '100%';
        el.style.borderRadius = '20px';
        el.style.background   = 'var(--azul)';
        el.style.width        = el.getAttribute('data-pct') + '%';
    });

    // Barras verticales de tendencia – alto en píxeles leído de data-h
    document.querySelectorAll('.barra-h').forEach(function (el) {
        el.style.height = el.getAttribute('data-h') + 'px';
    });
})();


/* ============================================================
   4. GESTIÓN DE INCIDENCIAS – GestionIncidencia.html
      Filtrado en tiempo real de la tabla de tickets por texto
      libre y por estado (Pendiente / En proceso / Resuelto).
      Solo se ejecuta cuando existe #tbody-tickets en el DOM.
   ============================================================ */

function filtrarTickets() {
    // Solo actúa si la tabla de tickets está presente
    if (!document.getElementById('tbody-tickets')) return;

    const texto   = document.getElementById('buscar-ticket').value.toLowerCase().trim();
    const estado  = document.getElementById('filtro-estado').value;
    const filas   = document.querySelectorAll('#tbody-tickets tr[data-texto]');
    let   visibles = 0;

    filas.forEach(function (fila) {
        const okTexto  = !texto  || fila.dataset.texto.includes(texto);
        const okEstado = !estado || fila.dataset.estado === estado;
        fila.style.display = (okTexto && okEstado) ? '' : 'none';
        if (okTexto && okEstado) visibles++;
    });

    document.getElementById('sin-resultados').style.display =
        visibles === 0 ? 'block' : 'none';
}