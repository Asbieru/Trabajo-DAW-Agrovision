// ── INDICADORES.JS  –  AgroVisión ──
// Lee datos de Jinja desde data- attributes y dibuja los gráficos

(function () {
    var contenedor = document.getElementById('datos-graficos');
    if (!contenedor) return;

    var porApp       = JSON.parse(contenedor.getAttribute('data-app'));
    var porPrioridad = JSON.parse(contenedor.getAttribute('data-prioridad'));
    var porMes       = JSON.parse(contenedor.getAttribute('data-mes'));

    // ── BARRAS DE SPRINTS (ancho en % desde data-ancho) ──
    document.querySelectorAll('.kpi-sprint-progress-relleno').forEach(function (el) {
        el.style.width = el.getAttribute('data-ancho') + '%';
    });

    // ── GRÁFICO BARRAS HORIZONTALES: Tickets por aplicación ──
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

    // ── GRÁFICO DONA: Distribución por prioridad ──
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
                        'rgba(39, 174, 96, 0.8)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { font: { size: 12 } } }
                }
            }
        });
    }

    // ── GRÁFICO BARRAS: Tendencia mensual ──
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
                plugins: {
                    legend: { position: 'top', labels: { font: { size: 12 } } }
                },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }

})();