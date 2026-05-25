/* ============================================================
   main.js  –  AgroVisión · Script unificado
   ============================================================
   Organización por página:
     1. GLOBAL      → base.html        (todas las páginas)
     2. LOGIN       → login.html
     3. INDICADORES → indicadores.html
     4. GESTIÓN     → GestionIncidencia.html
     5. REPORTES    → reportes.html
     6. GESTIÓN DE PROYECTO → gestionProyecto.html
     7. PERFIL DE USUARIO  → perfilUsuario.html
     8. HISTORIAL DE USUARIO → historialUsuario.html
   ============================================================ */


/* ============================================================
   1. GLOBAL – base.html
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
   ============================================================ */

function mostrarTab(tab, btn) {
    document.querySelectorAll('.tab-panel').forEach(function (p) {
        p.classList.remove('activo');
    });
    document.querySelectorAll('.tab-btn').forEach(function (b) {
        b.classList.remove('activo');
    });
    document.getElementById('panel-' + tab).classList.add('activo');
    btn.classList.add('activo');
}

(function iniciarLogin() {
    if (!document.getElementById('panel-registro')) return;

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
    var proyectosEst = JSON.parse(contenedor.getAttribute('data-proyectos-estado') || '[]');
    var velocity     = JSON.parse(contenedor.getAttribute('data-velocity') || '[]');

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

    // NUEVO: Gráfico proyectos por estado (indicadores)
    if (document.getElementById('grafico-ind-proyectos') && proyectosEst.length) {
        var canvasProyInd = document.getElementById('grafico-ind-proyectos');
        canvasProyInd.style.height = '320px';
        new Chart(canvasProyInd, {
            type: 'doughnut',
            data: {
                labels: proyectosEst.map(function(e){ return e.estado.replace('_',' '); }),
                datasets: [{
                    data: proyectosEst.map(function(e){ return e.total; }),
                    backgroundColor: [
                        'rgba(30,95,168,0.8)',
                        'rgba(26,122,74,0.8)',
                        'rgba(241,196,15,0.8)',
                        'rgba(192,57,43,0.8)',
                        'rgba(149,165,166,0.8)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    // NUEVO: Gráfico velocity por sprint (indicadores)
    if (document.getElementById('grafico-velocity') && velocity.length) {
        var canvasVel = document.getElementById('grafico-velocity');
        canvasVel.style.height = '350px';
        new Chart(canvasVel, {
            type: 'bar',
            data: {
                labels: velocity.map(function(s){ return s.sprint; }),
                datasets: [
                    {
                        label: 'Capacidad',
                        data: velocity.map(function(s){ return s.capacidad_pts; }),
                        backgroundColor: 'rgba(149,165,166,0.5)',
                        borderRadius: 4
                    },
                    {
                        label: 'Completados',
                        data: velocity.map(function(s){ return s.pts_completados; }),
                        backgroundColor: 'rgba(26,122,74,0.8)',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }

})();

/* ============================================================
   4. GESTIÓN DE INCIDENCIAS – gestionTicket.html
   ============================================================ */

function filtrarTickets() {
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

/* ============================================================
   5. REPORTES – reportes.html
   ============================================================ */
(function iniciarReportes() {
    var contenedor = document.getElementById('datos-reportes');
    if (!contenedor) return;

    var porApp          = JSON.parse(contenedor.getAttribute('data-app'));
    var porTipo         = JSON.parse(contenedor.getAttribute('data-tipo'));
    var storyPoints     = JSON.parse(contenedor.getAttribute('data-sp'));
    var carryover       = JSON.parse(contenedor.getAttribute('data-carryover'));
    var proyectosEstado = JSON.parse(contenedor.getAttribute('data-proyectos-estado') || '[]');

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
        canvasTipo.style.height = '400px';
        new Chart(canvasTipo, {
            type: 'doughnut',
            data: {
                labels: porTipo.map(function (t) { return t.tipo; }),
                datasets: [{ data: porTipo.map(function (t) { return t.total; }),
                    backgroundColor: ['rgba(192, 57, 43, 0.8)', 'rgba(26, 122, 74, 0.8)', 'rgba(30, 95, 168, 0.8)'],
                    borderWidth: 2 }]
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
                datasets: [{ label: 'Pts carryover', data: carryover.map(function (c) { return c.pts_carryover; }),
                    backgroundColor: 'rgba(240, 165, 0, 0.8)', borderRadius: 4 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
    }

    // NUEVO: Gráfico proyectos por estado (reportes)
    if (document.getElementById('grafico-proyectos-estado') && proyectosEstado.length) {
        var canvasProy = document.getElementById('grafico-proyectos-estado');
        canvasProy.style.height = '320px';
        new Chart(canvasProy, {
            type: 'doughnut',
            data: {
                labels: proyectosEstado.map(function(e){ return e.estado.replace('_',' '); }),
                datasets: [{
                    data: proyectosEstado.map(function(e){ return e.total; }),
                    backgroundColor: [
                        'rgba(30,95,168,0.8)',
                        'rgba(26,122,74,0.8)',
                        'rgba(241,196,15,0.8)',
                        'rgba(192,57,43,0.8)',
                        'rgba(149,165,166,0.8)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
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

    var canvas = document.getElementById('grafico-historias');
    if (!canvas) return;

    var contenedor = document.getElementById('datos-gestion');
    if (!contenedor) return;

    var resumen  = JSON.parse(contenedor.getAttribute('data-resumen'));
    var idActual = parseInt(contenedor.getAttribute('data-id-actual'), 10);

    var labels  = resumen.map(function (r) { return r.nombre_proyecto; });
    var totales = resumen.map(function (r) { return r.total; });

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

/* ============================================================
   7. PERFIL DE USUARIO – perfilUsuario.html
   ============================================================ */

(function iniciarPerfilUsuario() {
    var contenedor = document.getElementById('datos-perfil-usuario');
    if (!contenedor) return;

    var ticketsTipo  = JSON.parse(contenedor.getAttribute('data-tickets'));
    var proyectosEst = JSON.parse(contenedor.getAttribute('data-proyectos'));

    var coloresTicket = {
        'incidencia': 'rgba(192,57,43,0.8)',
        'peticion':   'rgba(26,122,74,0.8)',
        'consulta':   'rgba(30,95,168,0.8)'
    };
    var coloresProyecto = {
        'planificado':   'rgba(30,95,168,0.8)',
        'en_desarrollo': 'rgba(240,165,0,0.8)',
        'qa':            'rgba(26,122,74,0.5)',
        'completado':    'rgba(26,122,74,0.9)',
        'pausado':       'rgba(192,57,43,0.8)'
    };

    if (document.getElementById('grafico-perfil-tickets') && ticketsTipo.length) {
        var c1 = document.getElementById('grafico-perfil-tickets');
        c1.style.height = '220px';
        new Chart(c1, {
            type: 'doughnut',
            data: {
                labels: ticketsTipo.map(function(t){ return t.tipo; }),
                datasets: [{
                    data: ticketsTipo.map(function(t){ return t.total; }),
                    backgroundColor: ticketsTipo.map(function(t){
                        return coloresTicket[t.tipo] || 'rgba(108,117,125,0.7)';
                    }),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } }
            }
        });
    }

    if (document.getElementById('grafico-perfil-proyectos') && proyectosEst.length) {
        var c2 = document.getElementById('grafico-perfil-proyectos');
        c2.style.height = '220px';
        new Chart(c2, {
            type: 'doughnut',
            data: {
                labels: proyectosEst.map(function(p){ return p.estado; }),
                datasets: [{
                    data: proyectosEst.map(function(p){ return p.total; }),
                    backgroundColor: proyectosEst.map(function(p){
                        return coloresProyecto[p.estado] || 'rgba(108,117,125,0.7)';
                    }),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } }
            }
        });
    }
})();


/* ============================================================
   8. HISTORIAL DE USUARIO – historialUsuario.html
   ============================================================ */

var tipoActivo = 'todos';

function filtrarHistorial() {
    var texto = (document.getElementById('buscar-historial').value || '').toLowerCase().trim();
    var cards = document.querySelectorAll('.historial-card');

    cards.forEach(function(card) {
        var okTipo  = tipoActivo === 'todos' || card.dataset.tipo === tipoActivo;
        var okTexto = !texto || card.dataset.titulo.includes(texto);
        card.style.display = (okTipo && okTexto) ? '' : 'none';
    });

    document.querySelectorAll('.columna-kanban').forEach(function(col) {
        var visibles = col.querySelectorAll('.historial-card:not([style*="display: none"])').length;
        var colVacia = col.querySelector('.col-vacia');
        if (colVacia) colVacia.style.display = visibles === 0 ? 'block' : 'none';
    });
}

function setTipo(btn, tipo) {
    tipoActivo = tipo;
    document.querySelectorAll('.filtro-tipo').forEach(function(b) {
        b.classList.remove('btn-verde');
        b.classList.add('btn-outline');
    });
    btn.classList.remove('btn-outline');
    btn.classList.add('btn-verde');
    filtrarHistorial();
}

/* ============================================================
   SELECTOR DE SECCIÓN – reportes.html
   ============================================================ */
function mostrarSeccion(seccion) {
    document.getElementById('seccion-tickets').style.display   = seccion === 'tickets'   ? '' : 'none';
    document.getElementById('seccion-proyectos').style.display = seccion === 'proyectos' ? '' : 'none';
    document.getElementById('tab-tickets').className   = seccion === 'tickets'   ? 'btn btn-verde' : 'btn btn-outline';
    document.getElementById('tab-proyectos').className = seccion === 'proyectos' ? 'btn btn-verde' : 'btn btn-outline';

    if (seccion === 'proyectos') {
        renderGraficoProyectosReportes();
    }
}

function renderGraficoProyectosReportes() {
    var contenedor = document.getElementById('datos-reportes');
    if (!contenedor) return;
    var datosEstado = JSON.parse(contenedor.getAttribute('data-proyectos-estado') || '[]');
    var canvas = document.getElementById('grafico-proyectos-estado');
    if (canvas && datosEstado.length && !canvas._chartCreado) {
        canvas._chartCreado = true;
        canvas.style.height = '450px';
        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: datosEstado.map(function(e){ return e.estado.replace('_',' '); }),
                datasets: [{ data: datosEstado.map(function(e){ return e.total; }),
                    backgroundColor: ['rgba(30,95,168,0.8)','rgba(26,122,74,0.8)',
                        'rgba(241,196,15,0.8)','rgba(192,57,43,0.8)','rgba(149,165,166,0.8)'],
                    borderWidth: 2 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } } }
        });
    }
}

// Al cargar la página de reportes, leer _tab de la URL
(function iniciarTabReportes() {
    if (!document.getElementById('seccion-tickets')) return;
    var params = new URLSearchParams(window.location.search);
    var tab = params.get('_tab') || 'tickets';
    mostrarSeccion(tab);
})();

/* ============================================================
   SELECTOR DE SECCIÓN – indicadores.html
   ============================================================ */
function mostrarSeccionInd(seccion) {
    document.getElementById('seccion-ind-tickets').style.display   = seccion === 'tickets'   ? '' : 'none';
    document.getElementById('seccion-ind-proyectos').style.display = seccion === 'proyectos' ? '' : 'none';
    document.getElementById('tab-tickets').className   = seccion === 'tickets'   ? 'btn btn-verde' : 'btn btn-outline';
    document.getElementById('tab-proyectos').className = seccion === 'proyectos' ? 'btn btn-verde' : 'btn btn-outline';

    if (seccion === 'proyectos') {
        renderGraficosIndicadoresProyectos();
    }
}

function renderGraficosIndicadoresProyectos() {
    var contenedor = document.getElementById('datos-graficos');
    if (!contenedor) return;
    var datosProyectos = JSON.parse(contenedor.getAttribute('data-proyectos-estado') || '[]');
    var datosVelocity  = JSON.parse(contenedor.getAttribute('data-velocity') || '[]');

    document.querySelectorAll('.sprint-barra-relleno').forEach(function(el) {
        el.style.width = el.getAttribute('data-ancho') + '%';
    });

    var canvasProy = document.getElementById('grafico-ind-proyectos');
    if (canvasProy && datosProyectos.length && !canvasProy._chartCreado) {
        canvasProy._chartCreado = true;
        canvasProy.style.height = '320px';
        new Chart(canvasProy, {
            type: 'doughnut',
            data: {
                labels: datosProyectos.map(function(e){ return e.estado.replace('_',' '); }),
                datasets: [{ data: datosProyectos.map(function(e){ return e.total; }),
                    backgroundColor: ['rgba(30,95,168,0.8)','rgba(26,122,74,0.8)',
                        'rgba(241,196,15,0.8)','rgba(192,57,43,0.8)','rgba(149,165,166,0.8)'],
                    borderWidth: 2 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } } }
        });
    }

    var canvasVel = document.getElementById('grafico-velocity');
    if (canvasVel && datosVelocity.length && !canvasVel._chartCreado) {
        canvasVel._chartCreado = true;
        canvasVel.style.height = '350px';
        new Chart(canvasVel, {
            type: 'bar',
            data: {
                labels: datosVelocity.map(function(s){ return s.sprint; }),
                datasets: [
                    { label: 'Capacidad',   data: datosVelocity.map(function(s){ return s.capacidad_pts; }),   backgroundColor: 'rgba(149,165,166,0.5)', borderRadius: 4 },
                    { label: 'Completados', data: datosVelocity.map(function(s){ return s.pts_completados; }), backgroundColor: 'rgba(26,122,74,0.8)',    borderRadius: 4 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
    }
}

// Al cargar la página de indicadores, leer _tab de la URL
(function iniciarTabIndicadores() {
    if (!document.getElementById('seccion-ind-tickets')) return;
    var params = new URLSearchParams(window.location.search);
    var tab = params.get('_tab') || 'tickets';
    mostrarSeccionInd(tab);
})();

/* ============================================================
   LIMPIAR FILTROS PROYECTOS
   ============================================================ */
function limpiarFiltrosProyecto() {
    var url = window.location.pathname + '?_tab=proyectos';
    window.location.href = url;
}

function filtrarProyectos() {
    var estado      = document.getElementById('filtro-estado-proy');
    var responsable = document.getElementById('filtro-responsable-proy');
    if (!estado || !responsable) return;

    var valEstado      = estado.value.toLowerCase().trim();
    var valResponsable = responsable.value.toLowerCase().trim();

    var filas    = document.querySelectorAll('#tbody-proyectos tr');
    var visibles = 0;

    filas.forEach(function(fila) {
        var fEstado      = (fila.dataset.estado      || '').toLowerCase();
        var fResponsable = (fila.dataset.responsable || '').toLowerCase();

        var ok = true;
        if (valEstado      && fEstado !== valEstado)               ok = false;
        if (valResponsable && !fResponsable.includes(valResponsable)) ok = false;

        fila.style.display = ok ? '' : 'none';
        if (ok) visibles++;
    });

    var contador = document.getElementById('contador-proyectos');
    if (contador) contador.textContent = visibles + ' resultado' + (visibles !== 1 ? 's' : '');

    var sinRes = document.getElementById('sin-resultados-proyectos');
    if (sinRes) sinRes.style.display = visibles === 0 ? 'block' : 'none';
}

function limpiarFiltrosProyecto() {
    var estado      = document.getElementById('filtro-estado-proy');
    var responsable = document.getElementById('filtro-responsable-proy');
    if (estado)      estado.value      = '';
    if (responsable) responsable.value = '';
    filtrarProyectos();
}

function limpiarFiltrosProyectoInd() {
    window.location.href = window.location.pathname + '?_tab=proyectos';
}