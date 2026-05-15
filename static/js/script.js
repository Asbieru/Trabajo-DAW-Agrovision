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
   ============================================================ */
    (function iniciarIndicadores() {
    var contenedor = document.getElementById('datos-graficos');
    if (!contenedor) return;

    // Barras de sprints
    document.querySelectorAll('.sprint-barra-relleno').forEach(function (el) {
        el.style.width = el.getAttribute('data-ancho') + '%';
    });

    // Barras horizontales .barra-w (si las usas en otro lugar)
    document.querySelectorAll('.barra-w').forEach(function (el) {
        el.style.height       = '100%';
        el.style.borderRadius = '20px';
        el.style.background   = 'var(--azul)';
        el.style.width        = el.getAttribute('data-pct') + '%';
    });
    document.querySelectorAll('.barra-h').forEach(function (el) {
        el.style.height = el.getAttribute('data-h') + 'px';
    });

    var porApp       = JSON.parse(contenedor.getAttribute('data-app'));
    var porPrioridad = JSON.parse(contenedor.getAttribute('data-prioridad'));
    var porMes       = JSON.parse(contenedor.getAttribute('data-mes'));

        if (document.getElementById('grafico-app') && porApp.length) {
        var canvasApp = document.getElementById('grafico-app');
        canvasApp.style.height = '400px';
        new Chart(canvasApp, {
            type: 'bar',
            data: {
                labels: porApp.map(function (a) { return a.aplicacion; }),
                datasets: [{ label: 'Tickets', data: porApp.map(function (a) { return a.total; }),
                    backgroundColor: 'rgba(30,95,168,0.7)', borderColor: 'rgba(30,95,168,1)',
                    borderWidth: 1, borderRadius: 4 }]
            },
            options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
    }

    if (document.getElementById('grafico-prioridad') && porPrioridad.length) {
        var canvasPrioridad = document.getElementById('grafico-prioridad');
        canvasPrioridad.style.height = '400px';
        new Chart(canvasPrioridad, {
            type: 'doughnut',
            data: {
                labels: porPrioridad.map(function (p) { return p.prioridad; }),
                datasets: [{ data: porPrioridad.map(function (p) { return p.total; }),
                    backgroundColor: ['rgba(192,57,43,0.8)','rgba(230,126,34,0.8)',
                                    'rgba(241,196,15,0.8)','rgba(26,122,74,0.8)'],
                    borderWidth: 2 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } } }
        });
    }

    if (document.getElementById('grafico-tendencia') && porMes.length) {
    var canvasTendencia = document.getElementById('grafico-tendencia');
    canvasTendencia.style.height = '600px';
    new Chart(canvasTendencia, {
        type: 'bar',
        data: {
            labels: porMes.map(function (m) { return m.mes_label; }),
            datasets: [
                { label: 'Apertura',  data: porMes.map(function (m) { return m.total; }),
                  backgroundColor: 'rgba(30,95,168,0.7)', borderRadius: 4 },
                { label: 'Resueltos', data: porMes.map(function (m) { return m.resueltos; }),
                  backgroundColor: 'rgba(26,122,74,0.7)', borderRadius: 4 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'top', labels: { font: { size: 12 } } } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
    });
}
})();

/* ============================================================
   4. GESTIÓN DE INCIDENCIAS – GestionIncidencia.html
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

function limpiarFiltros() {
    document.getElementById('form-filtro-reportes').reset();
    document.querySelectorAll('#tabla-reporte tbody tr').forEach(function(fila) {
        fila.style.display = '';
    });
}

function imprimirReporte() {
    window.print();
}
 
(function iniciarReportes() {
    var contenedor = document.getElementById('datos-reportes');
    if (!contenedor) return;
 
    var porApp      = JSON.parse(contenedor.getAttribute('data-app'));
    var porTipo     = JSON.parse(contenedor.getAttribute('data-tipo'));
    var storyPoints = JSON.parse(contenedor.getAttribute('data-sp'));
    var carryover   = JSON.parse(contenedor.getAttribute('data-carryover'));
 

    if (document.getElementById('grafico-reporte-app') && porApp.length) {
        var canvasApp = document.getElementById('grafico-reporte-app');
        canvasApp.style.height = (porApp.length * 50) + 'px';
        new Chart(canvasApp, {
            type: 'bar',
            data: {
                labels: porApp.map(function (a) { return a.aplicacion; }),
                datasets: [
                    { label: 'Pendientes', data: porApp.map(function (a) { return a.pendientes; }), backgroundColor: 'rgba(192, 57, 43, 0.7)', borderRadius: 4 },
                    { label: 'Cerrados',   data: porApp.map(function (a) { return a.cerrados; }),   backgroundColor: 'rgba(26, 122, 74, 0.7)',  borderRadius: 4 }
                ]
            },
            options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
    }

    if (document.getElementById('grafico-reporte-tipo') && porTipo.length) {
        var canvasTipo = document.getElementById('grafico-reporte-tipo');
        canvasTipo.style.height = '400px'
        new Chart(canvasTipo, {
            type: 'doughnut',
            data: {
                labels: porTipo.map(function (t) { return t.tipo; }),
                datasets: [{ data: porTipo.map(function (t) { return t.total; }), backgroundColor: ['rgba(192, 57, 43, 0.8)', 'rgba(26, 122, 74, 0.8)', 'rgba(30, 95, 168, 0.8)'], borderWidth: 2 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } } }
        });
    }

    if (document.getElementById('grafico-reporte-sp') && storyPoints.length) {
        var canvasSp = document.getElementById('grafico-reporte-sp');
        canvasSp.style.height = '400px';
        new Chart(canvasSp, {
            type: 'bar',
            data: {
                labels: storyPoints.map(function (p) { return p.programador; }),
                datasets: [
                    { label: 'Asignados',   data: storyPoints.map(function (p) { return p.pts_asignados; }),   backgroundColor: 'rgba(30, 95, 168, 0.5)', borderRadius: 4 },
                    { label: 'Completados', data: storyPoints.map(function (p) { return p.pts_completados; }), backgroundColor: 'rgba(26, 122, 74, 0.8)',  borderRadius: 4 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false,
            layout: { padding: { bottom: 20 } },
            plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } } }
        });
    }

    if (document.getElementById('grafico-reporte-carryover') && carryover.length) {
        var canvasCarry = document.getElementById('grafico-reporte-carryover');
        canvasCarry.style.height = '400px';
        new Chart(canvasCarry, {
            type: 'bar',
            data: {
                labels: carryover.map(function (c) { return c.programador; }),
                datasets: [{ label: 'Pts carryover', data: carryover.map(function (c) { return c.pts_carryover; }), backgroundColor: 'rgba(240, 165, 0, 0.8)', borderRadius: 4 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
    }
})();

function filtrarReportes() {
    var fechaInicio = document.querySelector('[name="fecha_inicio"]').value;
    var fechaFin    = document.querySelector('[name="fecha_fin"]').value;
    var aplicacion  = document.querySelector('[name="aplicacion"]').value.toLowerCase().trim();
    var estado      = document.querySelector('[name="estado"]').value.toLowerCase().trim();
    var prioridad   = document.querySelector('[name="prioridad"]').value.toLowerCase().trim();

    var filas = document.querySelectorAll('#tabla-reporte tbody tr');

    filas.forEach(function(fila) {
        var celdas      = fila.querySelectorAll('td');
        var fAplicacion = celdas[2].textContent.trim().toLowerCase();
        var fEstado     = celdas[5].textContent.trim().toLowerCase();
        var fPrioridad  = celdas[4].textContent.trim().toLowerCase();
        var fFecha      = celdas[7].textContent.trim();

        var ok = true;

        if (aplicacion && !fAplicacion.includes(aplicacion)) ok = false;
        if (estado     && !fEstado.includes(estado.replace('_', ' '))) ok = false;
        if (prioridad  && !fPrioridad.includes(prioridad))   ok = false;

        if (fechaInicio || fechaFin) {
            var partes    = fFecha.split('/');
            var fechaFila = partes[2] + '-' + partes[1] + '-' + partes[0];
            if (fechaInicio && fechaFila < fechaInicio) ok = false;
            if (fechaFin    && fechaFila > fechaFin)    ok = false;
        }

        fila.style.display = ok ? '' : 'none';
    });
}

/* ============================================================
   6. GESTIÓN DE PROYECTO – gestionProyecto.html
   ============================================================ */

(function iniciarGestionProyecto() {

    // ── Días restantes (se recalcula cada vez que se carga la página) ──
    var divDias = document.getElementById('dias-restantes');
    if (divDias) {
        var fechaFin = divDias.getAttribute('data-fecha-fin');
        if (fechaFin) {
            var partes = fechaFin.split('-');
            var fin    = new Date(partes[0], partes[1] - 1, partes[2]);
            var hoy    = new Date();
            hoy.setHours(0, 0, 0, 0);
            var diffMs = fin - hoy;
            var dias   = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

            if (dias > 0) {
                divDias.textContent = dias + ' día' + (dias !== 1 ? 's' : '');
            } else if (dias === 0) {
                divDias.textContent  = 'Vence hoy';
                divDias.style.color  = 'var(--acento)';
            } else {
                divDias.textContent  = Math.abs(dias) + ' día' + (Math.abs(dias) !== 1 ? 's' : '') + ' vencido';
                divDias.style.color  = 'var(--rojo)';
            }
        }
    }

    // ── Gráfico de barras: historias por proyecto ──
    var canvas = document.getElementById('grafico-historias');
    if (!canvas) return;

    var contenedor = document.getElementById('datos-gestion');
    if (!contenedor) return;

    var resumen  = JSON.parse(contenedor.getAttribute('data-resumen'));
    var idActual = parseInt(contenedor.getAttribute('data-id-actual'), 10);

    var labels  = resumen.map(function (r) { return r.nombre_proyecto; });
    var totales = resumen.map(function (r) { return r.total; });

    // Barra verde para el proyecto actual, gris para el resto
    var colores = resumen.map(function (r) {
        return r.id_proyecto === idActual
            ? 'rgba(26, 122, 74, 0.85)'
            : 'rgba(200, 200, 200, 0.6)';
    });
    var bordes = resumen.map(function (r) {
        return r.id_proyecto === idActual
            ? 'rgba(15, 79, 46, 1)'
            : 'rgba(180, 180, 180, 1)';
    });

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total de historias',
                data: totales,
                backgroundColor: colores,
                borderColor: bordes,
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            return ' ' + ctx.parsed.y + ' historias';
                        }
                    }
                }
            },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });

})();