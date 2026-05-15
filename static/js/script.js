/* ============================================================
   1. GLOBAL – base.html
   ============================================================ */

function toggleMenu() {
    document.getElementById('dropdown-menu').classList.toggle('abierto');
}

document.addEventListener('click', function (e) {
    var menu = document.getElementById('dropdown-menu');
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
    var params = new URLSearchParams(window.location.search);
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
    var barrasAncho = document.querySelectorAll('.barra-w');
    if (barrasAncho.length) {
        barrasAncho.forEach(function (el) {
            el.style.height       = '100%';
            el.style.borderRadius = '20px';
            el.style.background   = 'var(--azul)';
            el.style.width        = el.getAttribute('data-pct') + '%';
        });
        document.querySelectorAll('.barra-h').forEach(function (el) {
            el.style.height = el.getAttribute('data-h') + 'px';
        });
    }

    var contenedor = document.getElementById('datos-graficos');
    if (!contenedor) return;

    var porApp       = JSON.parse(contenedor.getAttribute('data-app'));
    var porPrioridad = JSON.parse(contenedor.getAttribute('data-prioridad'));
    var porMes       = JSON.parse(contenedor.getAttribute('data-mes'));

    document.querySelectorAll('.sprint-barra-relleno').forEach(function (el) {
        el.style.width = el.getAttribute('data-ancho') + '%';
    });

    if (document.getElementById('grafico-app') && porApp.length) {
        new Chart(document.getElementById('grafico-app'), {
            type: 'bar',
            data: {
                labels: porApp.map(function (a) { return a.aplicacion; }),
                datasets: [{
                    label: 'Tickets',
                    data: porApp.map(function (a) { return a.total; }),
                    backgroundColor: 'rgba(30, 95, 168, 0.7)',
                    borderColor: 'rgba(30, 95, 168, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }

    if (document.getElementById('grafico-prioridad') && porPrioridad.length) {
        new Chart(document.getElementById('grafico-prioridad'), {
            type: 'doughnut',
            data: {
                labels: porPrioridad.map(function (p) { return p.prioridad; }),
                datasets: [{
                    data: porPrioridad.map(function (p) { return p.total; }),
                    backgroundColor: [
                        'rgba(192, 57, 43, 0.8)',
                        'rgba(230, 126, 34, 0.8)',
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(26, 122, 74, 0.8)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } }
            }
        });
    }

    if (document.getElementById('grafico-tendencia') && porMes.length) {
        new Chart(document.getElementById('grafico-tendencia'), {
            type: 'bar',
            data: {
                labels: porMes.map(function (m) { return m.mes_label; }),
                datasets: [
                    {
                        label: 'Apertura',
                        data: porMes.map(function (m) { return m.total; }),
                        backgroundColor: 'rgba(30, 95, 168, 0.7)',
                        borderColor: 'rgba(30, 95, 168, 1)',
                        borderWidth: 1,
                        borderRadius: 4
                    },
                    {
                        label: 'Resueltos',
                        data: porMes.map(function (m) { return m.resueltos; }),
                        backgroundColor: 'rgba(26, 122, 74, 0.7)',
                        borderColor: 'rgba(26, 122, 74, 1)',
                        borderWidth: 1,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'top', labels: { font: { size: 12 } } } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }
})();


/* ============================================================
   4. GESTIÓN DE INCIDENCIAS – GestionIncidencia.html
   ============================================================ */

function filtrarTickets() {
    if (!document.getElementById('tbody-tickets')) return;
 
    var texto    = document.getElementById('buscar-ticket').value.toLowerCase().trim();
    var estado   = document.getElementById('filtro-estado').value;
    var filas    = document.querySelectorAll('#tbody-tickets tr[data-texto]');
    var visibles = 0;
 
    filas.forEach(function (fila) {
        var okTexto  = !texto  || fila.dataset.texto.includes(texto);
        var okEstado = !estado || fila.dataset.estado === estado;
        fila.style.display = (okTexto && okEstado) ? '' : 'none';
        if (okTexto && okEstado) visibles++;
    });
 
    document.getElementById('sin-resultados').style.display =
        visibles === 0 ? 'block' : 'none';
}


/* ============================================================
   5. REPORTES – reportes.html
   ============================================================ */

(function iniciarReportes() {
    var formFiltro = document.getElementById('form-filtro-reportes');
    if (!formFiltro) return;
 
    formFiltro.addEventListener('submit', function (e) {
        e.preventDefault();
 
        var params = new URLSearchParams(new FormData(formFiltro));
        var url    = formFiltro.getAttribute('action') + '?' + params.toString();
 
        fetch(url)
            .then(function (resp) { return resp.text(); })
            .then(function (html) {
                var doc         = new DOMParser().parseFromString(html, 'text/html');
                var nuevaTabla  = doc.getElementById('tabla-reporte');
                var tablaActual = document.getElementById('tabla-reporte');
                if (nuevaTabla && tablaActual) {
                    tablaActual.innerHTML = nuevaTabla.innerHTML;
                }
            })
            .catch(function (err) {
                console.error('Error al filtrar:', err);
            });
    });
})();

(function iniciarReportesGraficos() {
    var contenedor = document.getElementById('datos-reportes');
    if (!contenedor) return;

    var ticketsApp  = JSON.parse(contenedor.getAttribute('data-app'));
    var ticketsTipo = JSON.parse(contenedor.getAttribute('data-tipo'));
    var storyPoints = JSON.parse(contenedor.getAttribute('data-sp'));
    var carryover   = JSON.parse(contenedor.getAttribute('data-carryover'));

    // Tickets por aplicación (barras horizontales)
    if (document.getElementById('grafico-reporte-app') && ticketsApp.length) {
        new Chart(document.getElementById('grafico-reporte-app'), {
            type: 'bar',
            data: {
                labels: ticketsApp.map(function(a) { return a.aplicacion; }),
                datasets: [
                    {
                        label: 'Pendientes',
                        data: ticketsApp.map(function(a) { return a.pendientes; }),
                        backgroundColor: 'rgba(192, 57, 43, 0.7)',
                        borderRadius: 4
                    },
                    {
                        label: 'Cerrados',
                        data: ticketsApp.map(function(a) { return a.cerrados; }),
                        backgroundColor: 'rgba(26, 122, 74, 0.7)',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: { legend: { position: 'top' } },
                scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }

    // Tickets por tipo (dona)
    if (document.getElementById('grafico-reporte-tipo') && ticketsTipo.length) {
        new Chart(document.getElementById('grafico-reporte-tipo'), {
            type: 'doughnut',
            data: {
                labels: ticketsTipo.map(function(t) { return t.tipo; }),
                datasets: [{
                    data: ticketsTipo.map(function(t) { return t.total; }),
                    backgroundColor: [
                        'rgba(192, 57, 43, 0.8)',
                        'rgba(26, 122, 74, 0.8)',
                        'rgba(30, 95, 168, 0.8)',
                        'rgba(240, 165, 0, 0.8)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } },
                cutout: '60%'
            }
        });
    }

    // Story points por programador (barras)
    if (document.getElementById('grafico-reporte-sp') && storyPoints.length) {
        new Chart(document.getElementById('grafico-reporte-sp'), {
            type: 'bar',
            data: {
                labels: storyPoints.map(function(p) { return p.programador; }),
                datasets: [
                    {
                        label: 'Completados',
                        data: storyPoints.map(function(p) { return p.pts_completados; }),
                        backgroundColor: 'rgba(26, 122, 74, 0.7)',
                        borderRadius: 4
                    },
                    {
                        label: 'Asignados',
                        data: storyPoints.map(function(p) { return p.pts_asignados; }),
                        backgroundColor: 'rgba(30, 95, 168, 0.4)',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'top' } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }

    // Carryover por programador (barras)
    if (document.getElementById('grafico-reporte-carryover') && carryover.length) {
        new Chart(document.getElementById('grafico-reporte-carryover'), {
            type: 'bar',
            data: {
                labels: carryover.map(function(c) { return c.programador; }),
                datasets: [{
                    label: 'Pts carryover',
                    data: carryover.map(function(c) { return c.pts_carryover; }),
                    backgroundColor: 'rgba(240, 165, 0, 0.8)',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }
})();

function limpiarFiltros() {
    var form = document.getElementById('form-filtro-reportes');
    if (!form) return;
    form.querySelectorAll('input, select').forEach(function(el) {
        el.value = '';
    });
    form.dispatchEvent(new Event('submit'));
}

function imprimirReporte() {
    window.print();
}