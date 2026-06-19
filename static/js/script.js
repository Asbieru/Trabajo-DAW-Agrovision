/* ============================================================
   script.js  –  AgroVisión · Script unificado
   ============================================================
   Organización por página:
     1. GLOBAL        → base.html              (todas las páginas)
     2. LOGIN         → login.html
     3. INDICADORES   → indicadores.html
     4. GESTIÓN       → gestionTicket.html
     5. REPORTES      → reportes.html
     6. GESTIÓN DE PROYECTO → gestionProyecto.html
        6.1  Días restantes y gráfico de historias
        6.2  Cambiar estado de actividad (Kanban)
     7. NUEVA ACTIVIDAD → nuevaActividad.html
     8. PERFIL DE USUARIO  → perfilUsuario.html
     9. HISTORIAL DE USUARIO → historialUsuario.html
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

// 2.1  Tabs de la vista login (si existieran)
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

// 2.2  Autenticación: hacerLogin() y chequeo de sesión
(function iniciarLoginAuth() {
    if (!document.getElementById('btn-ingresar')) return;

    // Si ya hay sesión guardada, ir directo al dashboard
    if (localStorage.getItem('usuario') && typeof URL_INDEX !== 'undefined') {
        window.location.href = URL_INDEX;
        return;
    }

    // Listener Enter en los campos correo y password
    function attachEnter() {
        ['correo', 'password'].forEach(function (id) {
            var el = document.getElementById(id);
            if (el) {
                el.addEventListener('keydown', function (e) {
                    if (e.key === 'Enter') hacerLogin();
                });
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attachEnter);
    } else {
        attachEnter();
    }
})();

function hacerLogin() {
    var correo   = document.getElementById('correo').value.trim();
    var password = document.getElementById('password').value;
    var msgError = document.getElementById('msg-error');
    var btn      = document.getElementById('btn-ingresar');

    msgError.style.display = 'none';

    if (!correo || !password) {
        msgError.textContent   = ' Completa todos los campos.';
        msgError.style.display = 'block';
        return;
    }

    btn.textContent = 'Verificando…';
    btn.disabled    = true;

    fetch(URL_AUTH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: correo, password: password })
    })
    .then(function (r) {
        if (!r.ok) throw new Error('Credenciales inválidas');
        return r.json();
    })
    .then(function (data) {
        var token = data.access_token;
        localStorage.setItem('jwt_token', token);
        try {
            var payload = JSON.parse(atob(token.split('.')[1]));
            var userId = payload.identity;
            return fetch(URL_USUARIO_ME + '?id_usuario=' + userId, {
                headers: { 'Authorization': 'JWT ' + token }
            }).then(function (r) { return r.json(); }).then(function (userData) {
                if (userData.ok) {
                    localStorage.setItem('usuario', JSON.stringify(userData.usuario));
                    window.location.href = URL_INDEX;
                } else {
                    throw new Error(userData.mensaje || 'Error al obtener usuario');
                }
            });
        } catch (e) {
            throw new Error('Error al procesar la sesión');
        }
    })
    .catch(function (err) {
        msgError.textContent = ' ' + err.message;
        msgError.style.display = 'block';
        btn.textContent = 'Ingresar al sistema';
        btn.disabled    = false;
    });
}


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

    var porApp        = JSON.parse(contenedor.getAttribute('data-app'));
    var porPrioridad  = JSON.parse(contenedor.getAttribute('data-prioridad'));
    var porIntensidad = JSON.parse(contenedor.getAttribute('data-intensidad') || '[]');
    var porTipoInd    = JSON.parse(contenedor.getAttribute('data-tipo') || '[]');
    var rankingApps   = JSON.parse(contenedor.getAttribute('data-ranking-apps') || '[]');
    var actEstado     = JSON.parse(contenedor.getAttribute('data-act-estado') || '[]');
    var porMes        = JSON.parse(contenedor.getAttribute('data-mes'));
    var proyectosEst  = JSON.parse(contenedor.getAttribute('data-proyectos-estado') || '[]');
    var velocity      = JSON.parse(contenedor.getAttribute('data-velocity') || '[]');

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

    if (document.getElementById('grafico-intensidad') && porIntensidad.length) {
        var canvasIntensidad = document.getElementById('grafico-intensidad');
        canvasIntensidad.style.height = '400px';
        new Chart(canvasIntensidad, {
            type: 'doughnut',
            data: {
                labels: porIntensidad.map(function (p) { return p.intensidad; }),
                datasets: [{ data: porIntensidad.map(function (p) { return p.total; }),
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

    // Tipo de ticket (indicadores)
    if (document.getElementById('grafico-tipo') && porTipoInd.length) {
        var canvasTipoInd = document.getElementById('grafico-tipo');
        canvasTipoInd.style.height = '360px';
        new Chart(canvasTipoInd, {
            type: 'doughnut',
            data: {
                labels: porTipoInd.map(function(t){ return t.tipo + ' (' + t.pct + '%)'; }),
                datasets: [{ data: porTipoInd.map(function(t){ return t.total; }),
                    backgroundColor: ['rgba(192,57,43,0.8)','rgba(26,122,74,0.8)','rgba(30,95,168,0.8)'],
                    borderWidth: 2 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } } }
        });
    }

    // Ranking apps problemáticas
    if (document.getElementById('grafico-ranking-apps') && rankingApps.length) {
        var canvasRanking = document.getElementById('grafico-ranking-apps');
        canvasRanking.style.height = Math.max(300, rankingApps.length * 55) + 'px';
        new Chart(canvasRanking, {
            type: 'bar',
            data: {
                labels: rankingApps.map(function(a){ return a.aplicacion; }),
                datasets: [
                    { label: 'Total incidencias', data: rankingApps.map(function(a){ return a.total_incidencias; }),
                      backgroundColor: 'rgba(149,165,166,0.5)', borderRadius: 4 },
                    { label: 'Alta prioridad', data: rankingApps.map(function(a){ return a.alta_prioridad; }),
                      backgroundColor: 'rgba(192,57,43,0.8)', borderRadius: 4 }
                ]
            },
            options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
    }

    // Actividades por estado (proyectos)
    if (document.getElementById('grafico-act-estado') && actEstado.length) {
        var canvasActEst = document.getElementById('grafico-act-estado');
        canvasActEst.style.height = '320px';
        var coloresAct = { 'en_progreso': 'rgba(30,95,168,0.8)', 'por_hacer': 'rgba(241,196,15,0.8)',
            'backlog': 'rgba(149,165,166,0.6)', 'completada': 'rgba(26,122,74,0.8)',
            'cancelada': 'rgba(192,57,43,0.5)', 'bloqueado': 'rgba(120,40,40,0.8)' };
        new Chart(canvasActEst, {
            type: 'doughnut',
            data: {
                labels: actEstado.map(function(a){ return a.estado.replace(/_/g,' ') + ' (' + a.total + ')'; }),
                datasets: [{ data: actEstado.map(function(a){ return a.total; }),
                    backgroundColor: actEstado.map(function(a){ return coloresAct[a.estado] || 'rgba(100,100,100,0.6)'; }),
                    borderWidth: 2 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } } }
        });
    }

    // Gráfica de tiempo promedio resolución por aplicación
    var panelTiempoApp = document.querySelector('[data-tiempo-app]');
    if (panelTiempoApp && document.getElementById('grafico-tiempo-app')) {
        var tiempoApp = JSON.parse(panelTiempoApp.getAttribute('data-tiempo-app'));
        if (tiempoApp.length) {
            var canvasTiempoApp = document.getElementById('grafico-tiempo-app');
            canvasTiempoApp.style.height = Math.max(300, tiempoApp.length * 55) + 'px';
            new Chart(canvasTiempoApp, {
                type: 'bar',
                data: {
                    labels: tiempoApp.map(function(a){ return a.aplicacion; }),
                    datasets: [
                        {
                            label: 'Promedio (h)',
                            data: tiempoApp.map(function(a){ return a.promedio_horas; }),
                            backgroundColor: tiempoApp.map(function(a){
                                return a.promedio_horas <= 8
                                    ? 'rgba(26,122,74,0.8)'
                                    : a.promedio_horas <= 24
                                        ? 'rgba(230,126,34,0.8)'
                                        : 'rgba(192,57,43,0.8)';
                            }),
                            borderRadius: 4
                        },
                        {
                            label: 'Mínimo (h)',
                            data: tiempoApp.map(function(a){ return a.minimo_horas; }),
                            backgroundColor: 'rgba(52,152,219,0.5)',
                            borderRadius: 4
                        },
                        {
                            label: 'Máximo (h)',
                            data: tiempoApp.map(function(a){ return a.maximo_horas; }),
                            backgroundColor: 'rgba(149,165,166,0.4)',
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    return ctx.dataset.label + ': ' + ctx.parsed.x + 'h';
                                }
                            }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true, ticks: { callback: function(v){ return v + 'h'; } } }
                    }
                }
            });
        }
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
    var form = document.getElementById('form-filtro-reportes');
    if (form) form.reset();
    var filas = document.querySelectorAll('#tabla-reporte tbody tr');
    filas.forEach(function(fila) { fila.style.display = ''; });
    var badge = document.querySelector('#tabla-reporte .rep-badge-total');
    if (badge) badge.textContent = filas.length + ' resultado' + (filas.length !== 1 ? 's' : '');
}

/* ════════════════════════════════════════════════════
   EXPORTAR PDF — jsPDF + autoTable (sin html2canvas)
   ════════════════════════════════════════════════════ */

/* Inserta un canvas de Chart.js como imagen en el PDF */
function _pdfGrafica(doc, canvasId, tituloGraf, x, y, w, h) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    try {
        var imgData = canvas.toDataURL('image/png');
        var pageW = doc.internal.pageSize.getWidth();
        // Barra titulo de la grafica
        doc.setFillColor(50, 50, 50);
        doc.rect(x, y, w, 6, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(7);
        doc.setFont('helvetica', 'bold');
        // limpiar titulo
        var t = '';
        for (var i = 0; i < tituloGraf.length; i++) {
            var code = tituloGraf.charCodeAt(i);
            if (code >= 32 && code <= 126) t += tituloGraf[i];
            else if (code === 243) t += 'o';
            else if (code === 233) t += 'e';
            else if (code === 237) t += 'i';
            else if (code === 225) t += 'a';
            else if (code === 250) t += 'u';
            else if (code === 241) t += 'n';
        }
        doc.text(t, x + 2, y + 4.2);
        doc.setTextColor(26, 30, 36);
        // Imagen del canvas
        doc.addImage(imgData, 'PNG', x, y + 6, w, h);
    } catch(e) { /* canvas no disponible */ }
}

/* Limpia texto para jsPDF: quita emojis y caracteres no latin */
function _limpiarTexto(txt) {
    if (!txt) return '';
    var resultado = '';
    var str = txt.trim();
    for (var i = 0; i < str.length; i++) {
        var code = str.charCodeAt(i);
        if (code >= 32 && code <= 126) { resultado += str[i]; }
        else if (code === 225) { resultado += 'a'; }
        else if (code === 233) { resultado += 'e'; }
        else if (code === 237) { resultado += 'i'; }
        else if (code === 243) { resultado += 'o'; }
        else if (code === 250) { resultado += 'u'; }
        else if (code === 241) { resultado += 'n'; }
        else if (code === 193) { resultado += 'A'; }
        else if (code === 201) { resultado += 'E'; }
        else if (code === 205) { resultado += 'I'; }
        else if (code === 211) { resultado += 'O'; }
        else if (code === 218) { resultado += 'U'; }
        else if (code === 209) { resultado += 'N'; }
        else if (code === 252) { resultado += 'u'; }  // u diéresis
        else if (code === 191) { resultado += '?'; }  // ¿
        else if (code === 161) { resultado += '!'; }  // ¡
        // emojis y otros caracteres especiales: ignorar
    }
    // limpiar espacios múltiples
    return resultado.replace(/\s+/g, ' ').trim();
}

function _getjsPDF() {
    if (window.jspdf && window.jspdf.jsPDF) return window.jspdf.jsPDF;
    if (window.jsPDF) return window.jsPDF;
    return null;
}

/* Cabecera común en el doc */
function _pdfHeader(doc, titulo, subtitulo) {
    doc.setFillColor(26, 122, 74);
    doc.rect(0, 0, 297, 18, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.text(titulo, 10, 11);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.text(subtitulo, 10, 16);
    doc.setTextColor(26, 30, 36);
    return 24; // y de inicio de contenido
}

/* KPI boxes en una fila */
function _pdfKPIs(doc, kpis, y) {
    var boxW = (277 / kpis.length);
    kpis.forEach(function(k, i) {
        var x = 10 + i * boxW;
        var colors = { negro:[26,30,36], rojo:[192,57,43], verde:[26,122,74], azul:[30,95,168], acento:[240,165,0] };
        var c = colors[k.color] || colors.negro;
        // borde izquierdo
        doc.setFillColor(c[0], c[1], c[2]);
        doc.rect(x, y, 2, 22, 'F');
        // fondo card
        doc.setFillColor(255, 255, 255);
        doc.setDrawColor(226, 230, 234);
        doc.rect(x + 2, y, boxW - 4, 22, 'FD');
        // label
        doc.setFontSize(6);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(108, 117, 125);
        doc.text(k.label.toUpperCase(), x + 5, y + 7);
        // número
        doc.setFontSize(18);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(c[0], c[1], c[2]);
        doc.text(String(k.num), x + 5, y + 18);
    });
    return y + 28;
}

/* Tabla con autoTable */
function _pdfAutoTable(doc, titulo, hdrs, filas, y) {
    if (filas.length === 0) return y;
    // Dibujar barra de titulo antes de la tabla — solo ASCII puro
    var t = '';
    for (var i = 0; i < titulo.length; i++) {
        var code = titulo.charCodeAt(i);
        if (code >= 32 && code <= 126) t += titulo[i]; // solo ASCII imprimible
        else if (code === 243) t += 'o';  // o con tilde
        else if (code === 233) t += 'e';  // e con tilde
        else if (code === 237) t += 'i';  // i con tilde
        else if (code === 225) t += 'a';  // a con tilde
        else if (code === 250) t += 'u';  // u con tilde
        else if (code === 241) t += 'n';  // n tilde
    }
    var pageW = doc.internal.pageSize.getWidth();
    doc.setFillColor(50, 50, 50);
    doc.rect(10, y, pageW - 20, 6, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.text(t, 13, y + 4.2);
    doc.setTextColor(26, 30, 36);
    doc.autoTable({
        startY: y + 6,
        head: [hdrs],
        body: filas,
        theme: 'grid',
        headStyles: { fillColor: [26, 122, 74], textColor: 255, fontSize: 7, fontStyle: 'bold', cellPadding: 3 },
        bodyStyles: { fontSize: 7, cellPadding: 3, textColor: [26, 30, 36] },
        alternateRowStyles: { fillColor: [245, 246, 248] },
        margin: { left: 10, right: 10 },
        tableWidth: 'auto',
        styles: { overflow: 'linebreak' }
    });
    return doc.lastAutoTable.finalY + 10;
}

/* ══════════════════════════════════════════════════
   exportarTabla() — solo la tabla filtrada
   ══════════════════════════════════════════════════ */
function exportarTabla() {
    var jsPDF = _getjsPDF();
    if (!jsPDF) { showAlert('Error: librería PDF no cargada.', 'error'); return; }

    var secProy = document.getElementById('seccion-proyectos');
    var esProyectos = secProy && secProy.style.display !== 'none';
    var fecha = new Date().toLocaleDateString('es-PE');
    var doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'letter' });

    var y = _pdfHeader(doc,
        (esProyectos ? 'Proyectos' : 'Tickets') + ' · AgroVisión',
        'Tabla filtrada · Generado el: ' + fecha
    );

    if (!esProyectos) {
        var todas = Array.from(document.querySelectorAll('#tabla-reporte tbody tr'));
        var hayFiltro = todas.some(function(f) { return f.style.display === 'none'; });
        var visibles = hayFiltro ? todas.filter(function(f) { return f.style.display !== 'none'; }) : todas;

        var hdrs = ['#','Título','Aplicación','Tipo','Prioridad','Estado','Solicitante','Fecha'];
        var filas = [];
        visibles.forEach(function(fila) {
            var celdas = fila.querySelectorAll('td');
            if (celdas.length < 8) return;
            filas.push([
                _limpiarTexto(celdas[0].textContent),
                _limpiarTexto(celdas[1].textContent),
                _limpiarTexto(celdas[2].textContent),
                _limpiarTexto(celdas[3].textContent),
                _limpiarTexto(celdas[4].textContent),
                _limpiarTexto(celdas[5].textContent),
                _limpiarTexto(celdas[6].textContent),
                _limpiarTexto(celdas[7].textContent)
            ]);
        });

        if (filas.length === 0) { showAlert('No hay tickets para exportar.', 'info'); return; }
        _pdfAutoTable(doc, 'Tickets (' + filas.length + ' registros)', hdrs, filas, y);

    } else {
        // Solo filas de proyectos (fila-proy-X), NO los paneles de actividades
        var todasP = Array.from(document.querySelectorAll('#tbody-proyectos tr[id^="fila-proy-"]'));
        var hayFiltroP = todasP.some(function(f) { return f.style.display === 'none'; });
        var visiblesP = hayFiltroP ? todasP.filter(function(f) { return f.style.display !== 'none'; }) : todasP;

        var hdrsP = ['#','Proyecto','Responsable','Estado','Inicio','Fecha fin','Avance','Salud'];
        var filasP = [];
        visiblesP.forEach(function(fila) {
            var celdas = fila.querySelectorAll('td');
            if (celdas.length < 9) return; // 8 datos + 1 boton
            var eliminado = fila.classList.contains('rep-fila-eliminada') ? ' [Eliminado]' : '';
            filasP.push([
                _limpiarTexto(celdas[0].textContent),
                _limpiarTexto(celdas[1].textContent) + eliminado,
                _limpiarTexto(celdas[2].textContent),
                _limpiarTexto(celdas[3].textContent),
                _limpiarTexto(celdas[4].textContent),
                _limpiarTexto(celdas[5].textContent),
                _limpiarTexto(celdas[6].textContent),
                _limpiarTexto(celdas[7].textContent)
            ]);
        });

        if (filasP.length === 0) { showAlert('No hay proyectos para exportar.', 'info'); return; }

        // Barra titulo
        var pageWP = doc.internal.pageSize.getWidth();
        doc.setFillColor(50, 50, 50);
        doc.rect(10, y, pageWP - 20, 6, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(7);
        doc.setFont('helvetica', 'bold');
        doc.text('Proyectos (' + filasP.length + ' registros)', 13, y + 4.2);
        doc.setTextColor(26, 30, 36);
        y += 6;

        doc.autoTable({
            startY: y,
            head: [hdrsP],
            body: filasP,
            theme: 'grid',
            headStyles: { fillColor: [26, 122, 74], textColor: 255, fontSize: 7, fontStyle: 'bold', cellPadding: 3 },
            bodyStyles: { fontSize: 7, cellPadding: 3, textColor: [26, 30, 36] },
            alternateRowStyles: { fillColor: [245, 246, 248] },
            margin: { left: 10, right: 10 },
            columnStyles: {
                0: { cellWidth: 12, fontStyle: 'bold', textColor: [108, 117, 125] },
                3: { cellWidth: 28 },
                4: { cellWidth: 22 },
                5: { cellWidth: 22 },
                6: { cellWidth: 18, halign: 'center' },
                7: { cellWidth: 22 }
            },
            didParseCell: function(data) {
                if (data.section === 'body' && data.column.index === 7) {
                    var salud = data.cell.raw;
                    if (salud === 'Completado' || salud === 'OK') { data.cell.styles.textColor = [26, 122, 74]; data.cell.styles.fontStyle = 'bold'; }
                    if (salud === 'Vencido')    { data.cell.styles.textColor = [192, 57, 43]; data.cell.styles.fontStyle = 'bold'; }
                    if (salud === 'Por vencer') { data.cell.styles.textColor = [240, 165, 0]; data.cell.styles.fontStyle = 'bold'; }
                    if (salud === 'Eliminado')  { data.cell.styles.textColor = [150, 150, 150]; }
                }
                if (data.section === 'body' && data.column.index === 3) {
                    var est = data.cell.raw;
                    if (est === 'Completado')   { data.cell.styles.textColor = [26, 122, 74]; data.cell.styles.fontStyle = 'bold'; }
                    if (est === 'En desarrollo') { data.cell.styles.textColor = [30, 95, 168]; data.cell.styles.fontStyle = 'bold'; }
                    if (est === 'Pausado')       { data.cell.styles.textColor = [192, 57, 43]; }
                }
                // Filas eliminadas en gris
                if (data.section === 'body') {
                    var txt = filasP[data.row.index] ? filasP[data.row.index][1] : '';
                    if (txt && txt.indexOf('[Eliminado]') !== -1) {
                        data.cell.styles.textColor = [150, 150, 150];
                    }
                }
            }
        });
    }

    doc.save('Tabla_' + (esProyectos ? 'Proyectos' : 'Tickets') + '_AgroVision.pdf');
}

/* ══════════════════════════════════════════════════
   exportarResumen() — KPIs + datos de gráficas
   ══════════════════════════════════════════════════ */
function exportarResumen() {
    var jsPDF = _getjsPDF();
    if (!jsPDF) { showAlert('Error: librería PDF no cargada.', 'error'); return; }

    var secProy = document.getElementById('seccion-proyectos');
    var esProyectos = secProy && secProy.style.display !== 'none';
    var fecha = new Date().toLocaleDateString('es-PE');
    var doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'letter' });

    var y = _pdfHeader(doc,
        'Resumen de Reportes · AgroVisión',
        'Sección: ' + (esProyectos ? 'Proyectos' : 'Tickets') + ' · Generado el: ' + fecha
    );

    var c = document.getElementById('datos-reportes');

    if (!esProyectos) {
        // KPIs
        var cards = document.querySelectorAll('#seccion-tickets .rep-resumen-card');
        var kpis = [];
        cards.forEach(function(card) {
            var num   = card.querySelector('.rep-rc-num')   ? card.querySelector('.rep-rc-num').textContent.trim()   : '0';
            var label = card.querySelector('.rep-rc-label') ? card.querySelector('.rep-rc-label').textContent.trim() : '';
            var color = card.classList.contains('rep-rc-total') ? 'negro'
                      : card.classList.contains('rep-rc-pendiente') ? 'rojo'
                      : card.classList.contains('rep-rc-resuelto')  ? 'verde' : 'azul';
            kpis.push({ num: num, label: label, color: color });
        });
        y = _pdfKPIs(doc, kpis, y);

        // Graficas + tablas de datos
        if (c) {
            var porApp  = JSON.parse(c.getAttribute('data-app')       || '[]');
            var porTipo = JSON.parse(c.getAttribute('data-tipo')      || '[]');
            var sp      = JSON.parse(c.getAttribute('data-sp')        || '[]');
            var carry   = JSON.parse(c.getAttribute('data-carryover') || '[]');
            var pageW   = doc.internal.pageSize.getWidth();
            var halfW   = (pageW - 20) / 2;
            var grafH   = 55; // altura de cada grafica en mm

            // Fila 1: grafica app + grafica tipo (lado a lado)
            var yGraf1 = y;
            _pdfGrafica(doc, 'grafico-reporte-app',  'Tickets por aplicacion', 10,          yGraf1, halfW - 2, grafH);
            _pdfGrafica(doc, 'grafico-reporte-tipo',  'Tickets por tipo',       12 + halfW,  yGraf1, halfW - 2, grafH);
            y = yGraf1 + grafH + 8;

            // Tabla app + tabla tipo (lado a lado usando autoTable con columnStyles)
            if (porApp.length) {
                y = _pdfAutoTable(doc, 'Datos: Tickets por aplicacion',
                    ['Aplicacion','Pendientes','Cerrados','Total'],
                    porApp.map(function(a){ return [a.aplicacion, a.pendientes||0, a.cerrados||0, a.total]; }), y);
            }
            if (porTipo.length) {
                y = _pdfAutoTable(doc, 'Datos: Tickets por tipo',
                    ['Tipo','Total'],
                    porTipo.map(function(t){ return [t.tipo, t.total]; }), y);
            }

            // Nueva pagina para graficas 2
            doc.addPage();
            y = _pdfHeader(doc, 'Resumen de Reportes - Productividad', 'AgroVision');

            // Fila 2: grafica sp + grafica carryover
            _pdfGrafica(doc, 'grafico-reporte-sp',       'Story points por programador', 10,         y, halfW - 2, grafH);
            _pdfGrafica(doc, 'grafico-reporte-carryover', 'Carryover por programador',   12 + halfW, y, halfW - 2, grafH);
            y = y + grafH + 8;

            if (sp.length) {
                y = _pdfAutoTable(doc, 'Datos: Story points por programador',
                    ['Programador','Asignados','Completados'],
                    sp.map(function(p){ return [p.programador, p.pts_asignados, p.pts_completados]; }), y);
            }
            if (carry.length) {
                _pdfAutoTable(doc, 'Datos: Carryover por programador',
                    ['Programador','Sprints con carryover','Pts carryover'],
                    carry.map(function(cc){ return [cc.programador, cc.sprints_con_carryover, cc.pts_carryover]; }), y);
            }
        }

    } else {
        // KPIs proyectos
        var cardsP = document.querySelectorAll('#seccion-proyectos .rep-resumen-card');
        var kpisP = [];
        cardsP.forEach(function(card) {
            var num   = card.querySelector('.rep-rc-num')   ? card.querySelector('.rep-rc-num').textContent.trim()   : '0';
            var label = card.querySelector('.rep-rc-label') ? card.querySelector('.rep-rc-label').textContent.trim() : '';
            var color = card.classList.contains('rep-rc-pendiente') ? 'rojo'
                      : card.classList.contains('rep-rc-resuelto')  ? 'verde' : 'azul';
            kpisP.push({ num: num, label: label, color: color });
        });
        y = _pdfKPIs(doc, kpisP, y);

        // Grafica proyectos por estado
        var pageWP = doc.internal.pageSize.getWidth();
        _pdfGrafica(doc, 'grafico-proyectos-estado', 'Proyectos por estado', 10, y, pageWP - 20, 60);
        y = y + 68;

        // Tablas de proyectos
        document.querySelectorAll('#seccion-proyectos .rep-tabla').forEach(function(tabla) {
            var tituloEl = tabla.closest('.rep-panel') ? tabla.closest('.rep-panel').querySelector('.rep-panel-titulo') : null;
            var tit = tituloEl ? tituloEl.textContent.trim().replace(/[^\x00-\x7F]/g, '').trim() : 'Tabla';
            var hdrs = [];
            tabla.querySelectorAll('thead th').forEach(function(th) { hdrs.push(th.textContent.trim()); });
            var filas = [];
            tabla.querySelectorAll('tbody tr').forEach(function(tr) {
                var fila = [];
                tr.querySelectorAll('td').forEach(function(td) { fila.push(td.textContent.trim()); });
                if (fila.length) filas.push(fila);
            });
            if (filas.length) y = _pdfAutoTable(doc, tit, hdrs, filas, y);
        });
    }

    doc.save('Resumen_' + (esProyectos ? 'Proyectos' : 'Tickets') + '_AgroVision.pdf');
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
    var ticketsEstado   = JSON.parse(contenedor.getAttribute('data-tickets-estado') || '[]');
    var tendencia       = JSON.parse(contenedor.getAttribute('data-tendencia') || '[]');
    var slaApp          = JSON.parse(contenedor.getAttribute('data-sla-app') || '[]');

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

    // Tickets por estado
    if (document.getElementById('grafico-tickets-estado') && ticketsEstado.length) {
        var canvasEst = document.getElementById('grafico-tickets-estado');
        canvasEst.style.height = '350px';
        var coloresEst = ticketsEstado.map(function(e) {
            if (e.estado === 'resuelto')    return 'rgba(26,122,74,0.8)';    // verde oscuro
            if (e.estado === 'cerrado')     return 'rgba(88,214,141,0.8)';   // verde claro
            if (e.estado === 'en_progreso') return 'rgba(30,95,168,0.8)';    // azul
            if (e.estado === 'solicitado')  return 'rgba(241,196,15,0.8)';   // amarillo
            if (e.estado === 'cancelado')   return 'rgba(149,165,166,0.8)';  // gris
            return 'rgba(192,57,43,0.8)';                                     // rojo
        });
        new Chart(canvasEst, {
            type: 'doughnut',
            data: {
                labels: ticketsEstado.map(function(e){ return e.estado.replace(/_/g,' '); }),
                datasets: [{ data: ticketsEstado.map(function(e){ return e.total; }),
                    backgroundColor: coloresEst, borderWidth: 2 }]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } } }
        });
    }

    // Tendencia por mes
    if (document.getElementById('grafico-rep-tendencia') && tendencia.length) {
        var canvasTend = document.getElementById('grafico-rep-tendencia');
        canvasTend.style.height = '350px';
        new Chart(canvasTend, {
            type: 'bar',
            data: {
                labels: tendencia.map(function(m){ return m.mes_label; }),
                datasets: [
                    { label: 'Total', data: tendencia.map(function(m){ return m.total; }),
                      backgroundColor: 'rgba(30,95,168,0.6)', borderRadius: 4 },
                    { label: 'Resueltos', data: tendencia.map(function(m){ return m.resueltos; }),
                      backgroundColor: 'rgba(26,122,74,0.8)', borderRadius: 4 },
                    { label: 'Cancelados', data: tendencia.map(function(m){ return m.cancelados; }),
                      backgroundColor: 'rgba(149,165,166,0.7)', borderRadius: 4 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
    }

    // SLA por aplicación (barras apiladas OK vs KO)
    if (document.getElementById('grafico-sla-app') && slaApp.length) {
        var canvasSlaApp = document.getElementById('grafico-sla-app');
        canvasSlaApp.style.height = Math.max(300, slaApp.length * 55) + 'px';
        new Chart(canvasSlaApp, {
            type: 'bar',
            data: {
                labels: slaApp.map(function(a){ return a.aplicacion; }),
                datasets: [
                    { label: 'SLA cumplido', data: slaApp.map(function(a){ return a.sla_ok; }),
                      backgroundColor: 'rgba(26,122,74,0.8)', borderRadius: 4 },
                    { label: 'SLA excedido', data: slaApp.map(function(a){ return a.sla_ko; }),
                      backgroundColor: 'rgba(192,57,43,0.8)', borderRadius: 4 }
                ]
            },
            options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: { x: { beginAtZero: true, stacked: true }, y: { stacked: true } } }
        });
    }

})();

function filtrarReportes() {
    // Scopear al form correcto para no agarrar inputs de otras paginas
    var form = document.getElementById('form-filtro-reportes');
    if (!form) return;

    var fechaInicio   = form.querySelector('[name="fecha_inicio"]').value;
    var fechaFin      = form.querySelector('[name="fecha_fin"]').value;
    // El select ahora envía id_aplicacion; para filtrar visualmente usamos el texto del option
    var selApp        = form.querySelector('[name="id_aplicacion"]');
    var aplicacion    = selApp ? selApp.options[selApp.selectedIndex].text.toLowerCase().trim() : '';
    if (selApp && selApp.value === '') aplicacion = '';
    var estado        = form.querySelector('[name="estado"]').value.toLowerCase().trim();
    var prioridad     = form.querySelector('[name="prioridad"]').value.toLowerCase().trim();

    var filas    = document.querySelectorAll('#tabla-reporte tbody tr');
    var visibles = 0;

    // Índices de columna (0-based) en la nueva tabla:
    // 0:#  1:Título  2:Aplicación  3:Tipo  4:Prioridad  5:Intensidad
    // 6:Estado  7:Solicitante  8:Agente  9:Apertura  10:Solución
    // 11:Tiempo  12:SLA  13:⭐
    filas.forEach(function(fila) {
        var celdas = fila.querySelectorAll('td');
        if (celdas.length < 10) return;

        var fAplicacion = celdas[2].textContent.trim().toLowerCase();
        var fPrioridad  = celdas[4].textContent.trim().toLowerCase();
        var fEstado     = celdas[6].textContent.trim().toLowerCase();
        var fFecha      = celdas[9].textContent.trim(); // fecha apertura dd/mm/yyyy hh:mm

        var ok = true;

        if (aplicacion && !fAplicacion.includes(aplicacion)) ok = false;
        if (estado     && !fEstado.includes(estado.replace(/_/g, ' '))) ok = false;
        if (prioridad  && !fPrioridad.includes(prioridad))              ok = false;

        if (fechaInicio || fechaFin) {
            // La fecha puede tener hora: "12/06/2025 09:00", tomamos solo la parte de fecha
            var soloFecha = fFecha.split(' ')[0];
            var partes    = soloFecha.split('/');
            if (partes.length === 3) {
                var fechaFila = partes[2] + '-' + partes[1] + '-' + partes[0];
                if (fechaInicio && fechaFila < fechaInicio) ok = false;
                if (fechaFin    && fechaFila > fechaFin)    ok = false;
            }
        }

        fila.style.display = ok ? '' : 'none';
        if (ok) visibles++;
    });

    // Actualizar badge contador
    var badge = document.querySelector('#tabla-reporte .rep-badge-total');
    if (badge) badge.textContent = visibles + ' resultado' + (visibles !== 1 ? 's' : '');

    // Mostrar mensaje si no hay resultados
    var sinDatos = document.querySelector('#tabla-reporte .rep-sin-datos');
    if (sinDatos) sinDatos.style.display = visibles === 0 ? 'block' : 'none';
}

/* ============================================================
   EXPORTAR EXCEL — reportes.html
   Redirige a la ruta Flask con los filtros activos del form.
   El servidor genera y devuelve el .xlsx directamente.
   ============================================================ */
function exportarExcel() {
    var form = document.getElementById('form-filtro-reportes');
    if (!form) return;

    var params = new URLSearchParams();

    var fechaInicio = form.querySelector('[name="fecha_inicio"]').value;
    var fechaFin    = form.querySelector('[name="fecha_fin"]').value;
    var selApp      = form.querySelector('[name="id_aplicacion"]');
    var idAplicacion = selApp ? selApp.value : '';
    var estado      = form.querySelector('[name="estado"]').value;
    var prioridad   = form.querySelector('[name="prioridad"]').value;

    if (fechaInicio)  params.append('fecha_inicio',  fechaInicio);
    if (fechaFin)     params.append('fecha_fin',     fechaFin);
    if (idAplicacion) params.append('id_aplicacion', idAplicacion);
    if (estado)       params.append('estado',        estado);
    if (prioridad)    params.append('prioridad',     prioridad);

    window.location.href = '/reportes/exportar-excel?' + params.toString();
}

function exportarExcelProyectos() {
    var estado       = document.getElementById('filtro-estado-proy') ? document.getElementById('filtro-estado-proy').value : '';
    var responsable  = document.getElementById('filtro-responsable-proy') ? document.getElementById('filtro-responsable-proy').value : '';

    var params = new URLSearchParams();
    if (estado)      params.append('estado',          estado);
    if (responsable) params.append('id_responsable',  responsable);

    window.location.href = '/reportes/exportar-excel-proyectos?' + params.toString();
}

/* ============================================================
   SELECTOR DE SECCIÓN – reportes.html
   ============================================================ */
function mostrarSeccion(seccion) {
    document.getElementById('seccion-tickets').style.display   = seccion === 'tickets'   ? '' : 'none';
    document.getElementById('seccion-proyectos').style.display = seccion === 'proyectos' ? '' : 'none';
    document.getElementById('tab-tickets').className   = seccion === 'tickets'   ? 'rep-tab rep-tab-activo' : 'rep-tab';
    document.getElementById('tab-proyectos').className = seccion === 'proyectos' ? 'rep-tab rep-tab-activo' : 'rep-tab';

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
   6. GESTIÓN DE PROYECTO – gestionProyecto.html
   ============================================================ */

/* -- 6.1  Días restantes y gráfico de historias por proyecto -- */
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

/* -- 6.2  Cambiar estado de actividad via fetch (tablero Kanban) -- */
var ORDEN_ESTADOS = ['backlog', 'por_hacer', 'en_progreso', 'completada'];

function avanzarEstadoActividad(idActividad, estadoActual, btn) {
    var idx = ORDEN_ESTADOS.indexOf(estadoActual);
    if (idx === -1 || idx >= ORDEN_ESTADOS.length - 1) return;
    var nuevoEstado = ORDEN_ESTADOS[idx + 1];

    btn.textContent = '…';
    btn.disabled    = true;

    apiFetch('/api/actividad/' + idActividad + '/estado', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ estado: nuevoEstado })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.ok) {
            location.reload();
        } else {
            showAlert('Error al cambiar estado.', 'error');
            btn.textContent = '→';
            btn.disabled    = false;
        }
    })
    .catch(function () {
        showAlert('Error de conexión.', 'error');
        btn.textContent = '→';
        btn.disabled    = false;
    });
}

function cancelarActividad(idActividad, btn) {
    btn.textContent = '…';
    btn.disabled    = true;

    apiFetch('/api/actividad/' + idActividad + '/estado', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ estado: 'cancelada' })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.ok) {
            location.reload();
        } else {
            showAlert('Error al cancelar actividad.', 'error');
            btn.textContent = 'Cancelar';
            btn.disabled    = false;
        }
    })
    .catch(function () {
        showAlert('Error de conexión.', 'error');
        btn.textContent = 'Cancelar';
        btn.disabled    = false;
    });
}

function bloquearActividad(idActividad, btn) {
    btn.textContent = '…';
    btn.disabled    = true;

    apiFetch('/api/actividad/' + idActividad + '/estado', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ estado: 'bloqueado' })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.ok) {
            location.reload();
        } else {
            showAlert('Error al bloquear actividad.', 'error');
            btn.textContent = '🔒 Bloquear';
            btn.disabled    = false;
        }
    })
    .catch(function () {
        showAlert('Error de conexión.', 'error');
        btn.textContent = '🔒 Bloquear';
        btn.disabled    = false;
    });
}

function desbloquearActividad(idActividad, btn) {
    btn.textContent = '…';
    btn.disabled    = true;

    apiFetch('/api/actividad/' + idActividad + '/desbloquear', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.ok) {
            location.reload();
        } else {
            showAlert('Error al desbloquear actividad.', 'error');
            btn.textContent = '🔓 Desbloquear';
            btn.disabled    = false;
        }
    })
    .catch(function () {
        showAlert('Error de conexión.', 'error');
        btn.textContent = '🔓 Desbloquear';
        btn.disabled    = false;
    });
}

// Variable para almacenar el botón y el id al confirmar eliminación de actividad
var _elimActividadId  = null;
var _elimActividadBtn = null;

function confirmarEliminarActividad(idActividad, btn) {
    _elimActividadId  = idActividad;
    _elimActividadBtn = btn;
    var modal = document.getElementById('modal-eliminar-actividad');
    if (modal) modal.style.display = 'flex';
}

function cerrarModalEliminarActividad() {
    var modal = document.getElementById('modal-eliminar-actividad');
    if (modal) modal.style.display = 'none';
    _elimActividadId  = null;
    _elimActividadBtn = null;
}

(function bindEliminarActividadSi() {
    document.addEventListener('DOMContentLoaded', function () {
        var btnSi = document.getElementById('modal-elim-act-si');
        if (!btnSi) return;
        btnSi.addEventListener('click', function () {
            if (!_elimActividadId) return;
            var idParaEliminar = _elimActividadId;   // guardar antes de cerrar
            var btn = _elimActividadBtn;
            if (btn) { btn.textContent = '…'; btn.disabled = true; }

            // cerrar modal manualmente sin limpiar la variable todavía
            var modal = document.getElementById('modal-eliminar-actividad');
            if (modal) modal.style.display = 'none';

            apiFetch('/api/actividad/' + idParaEliminar + '/eliminar', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.ok) {
                    location.reload();
                } else {
                    mostrarModalAviso(data.mensaje || 'Error al eliminar actividad.');
                    if (btn) { btn.textContent = '🗑 Eliminar'; btn.disabled = false; }
                }
            })
            .catch(function () {
                mostrarModalAviso('Error de conexión.');
                if (btn) { btn.textContent = '🗑 Eliminar'; btn.disabled = false; }
            });

            _elimActividadId  = null;
            _elimActividadBtn = null;
        });
    });
})();

function eliminarActividad(idActividad, btn) {
    // Compatibilidad: redirige a la función con modal
    confirmarEliminarActividad(idActividad, btn);
}


/* ============================================================
   7. NUEVA ACTIVIDAD – nuevaActividad.html
   ============================================================ */

/**
 * Carga los sprints del proyecto seleccionado vía AJAX.
 * @param {string|number} proyectoId  - id del proyecto
 * @param {string|number} [sprintSeleccionado] - id del sprint a pre-seleccionar (edición)
 */
function cargarSprintsAjax(proyectoId, sprintSeleccionado) {
    var sprintSel = document.getElementById('id_sprint');
    if (!sprintSel) return;

    // Resetear combo
    sprintSel.innerHTML = '<option value="">— Sin sprint asignado —</option>';

    if (!proyectoId) {
        sprintSel.disabled = true;
        return;
    }

    apiFetch('/api/proyecto/' + proyectoId + '/sprints')
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            if (!data.ok || !data.sprints || data.sprints.length === 0) {
                // Proyecto sin sprints (duración < 1 semana → Kanban)
                sprintSel.disabled = false;
                return;
            }
            data.sprints.forEach(function(s) {
                var op = document.createElement('option');
                op.value = s.id_sprint;
                op.textContent = s.nombre + ' (' + s.fecha_inicio + ' → ' + s.fecha_fin + ')';
                if (sprintSeleccionado && s.id_sprint == sprintSeleccionado) {
                    op.selected = true;
                }
                sprintSel.appendChild(op);
            });
            sprintSel.disabled = false;
        })
        .catch(function() {
            sprintSel.disabled = false;
        });
}

/* Mantiene compatibilidad: al cambiar proyecto en nueva actividad llama a AJAX */
function filtrarSprints() {
    var proyectoId = document.getElementById('id_proyecto') ?
                     document.getElementById('id_proyecto').value : '';
    cargarSprintsAjax(proyectoId);
}

function cargarAsignados() {
    var proyectoId = document.getElementById('id_proyecto').value;
    var sel = document.getElementById('id_asignado');
    if (!sel) return;
    sel.innerHTML = '';

    if (!proyectoId) {
        sel.innerHTML = '<option value="">— Selecciona primero un proyecto —</option>';
        return;
    }

    var lista = (typeof asignadosPorProyecto !== 'undefined' && asignadosPorProyecto[proyectoId]) || [];
    if (lista.length === 0) {
        sel.innerHTML = '<option value="">— Sin responsables asignados —</option>';
        return;
    }

    var opDefault = document.createElement('option');
    opDefault.value = '';
    opDefault.textContent = '— Selecciona encargado —';
    sel.appendChild(opDefault);

    lista.forEach(function (u) {
        var op = document.createElement('option');
        op.value = u.id_usuario;
        op.textContent = u.nombre_completo;
        sel.appendChild(op);
    });
}

(function iniciarNuevaActividad() {
    if (!document.getElementById('id_proyecto')) return;

    function arrancar() {
        var proyectoId = document.getElementById('id_proyecto').value;
        cargarSprintsAjax(proyectoId);
        cargarAsignados();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', arrancar);
    } else {
        arrancar();
    }
})();


/* ============================================================
   8. PERFIL DE USUARIO – perfilUsuario.html
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
   9. HISTORIAL DE USUARIO – historialUsuario.html
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
   SELECTOR DE SECCIÓN – indicadores.html
   ============================================================ */
function mostrarSeccionInd(seccion) {
    document.getElementById('seccion-ind-tickets').style.display   = seccion === 'tickets'   ? '' : 'none';
    document.getElementById('seccion-ind-proyectos').style.display = seccion === 'proyectos' ? '' : 'none';
    document.getElementById('tab-tickets').className   = seccion === 'tickets'   ? 'ind-tab ind-tab-activo' : 'ind-tab';
    document.getElementById('tab-proyectos').className = seccion === 'proyectos' ? 'ind-tab ind-tab-activo' : 'ind-tab';

    // Actualizar hero según sección activa
    var btn  = document.getElementById('ind-hero-btn');
    var tit  = document.getElementById('ind-hero-titulo');
    var sub  = document.getElementById('ind-hero-sub');
    if (btn && tit && sub) {
        if (seccion === 'proyectos') {
            tit.innerHTML = 'Indicadores<br><span>de Proyectos</span>';
            sub.textContent = 'KPIs · Gestión de Proyectos · AgroVisión';
            btn.textContent = 'Ver proyectos';
            btn.href = btn.getAttribute('data-url-proyectos');
        } else {
            tit.innerHTML = 'Indicadores<br><span>de Soporte</span>';
            sub.textContent = 'KPIs · Área de Sistemas · AgroVisión';
            btn.textContent = 'Ver tickets';
            btn.href = btn.getAttribute('data-url-tickets');
        }
    }

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
   FILTROS DE PROYECTOS – listaProyectos.html / indicadores.html
   ============================================================ */

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
        if (valEstado      && fEstado !== valEstado)                  ok = false;
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

/* ============================================================
   10. MODALES PROYECTOS – listaProyectos.html
   ============================================================ */

/* Modal de aviso genérico (reemplaza alert nativo) */
function mostrarModalAviso(mensaje) {
    var overlay = document.getElementById('modal-aviso-global');
    var txt     = document.getElementById('modal-aviso-mensaje');
    if (!overlay || !txt) {
        // Fallback si la plantilla no tiene el modal aún
        showAlert(mensaje, 'error');
        return;
    }
    txt.textContent = mensaje;
    overlay.style.display = 'flex';
}

function cerrarModalAviso() {
    var overlay = document.getElementById('modal-aviso-global');
    if (overlay) overlay.style.display = 'none';
}

var _elimProyectoId = null;

function confirmarEliminarProyecto(idProyecto, nombreProyecto) {
    _elimProyectoId = idProyecto;
    var modal = document.getElementById('modal-eliminar-proyecto');
    var lbl   = document.getElementById('modal-elim-nombre-proy');
    if (lbl) lbl.textContent = nombreProyecto;
    if (modal) modal.style.display = 'flex';
}

function cerrarModalEliminarProyecto() {
    var modal = document.getElementById('modal-eliminar-proyecto');
    if (modal) modal.style.display = 'none';
    _elimProyectoId = null;
}

(function bindEliminarProyectoSi() {
    document.addEventListener('DOMContentLoaded', function () {
        var btnSi = document.getElementById('modal-elim-si');
        if (!btnSi) return;
        btnSi.addEventListener('click', function () {
            if (!_elimProyectoId) return;
            var idParaEliminar = _elimProyectoId;   // guardar antes de cerrar
            btnSi.textContent = '…';
            btnSi.disabled    = true;

            // cerrar modal manualmente sin limpiar la variable todavía
            var modal = document.getElementById('modal-eliminar-proyecto');
            if (modal) modal.style.display = 'none';

            apiFetch('/api/proyecto/' + idParaEliminar + '/eliminar', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.ok) {
                    location.reload();
                } else {
                    mostrarModalAviso(data.mensaje || 'No se pudo eliminar el proyecto.');
                    btnSi.textContent = 'Sí, eliminar';
                    btnSi.disabled    = false;
                }
            })
            .catch(function () {
                mostrarModalAviso('Error de conexión.');
                btnSi.textContent = 'Sí, eliminar';
                btnSi.disabled    = false;
            });

            _elimProyectoId = null;
        });
    });
})();


/* ============================================================
   11. MODAL ACTIVIDAD CREADA – nuevaActividad.html
   ============================================================ */

function cerrarModalActividadCreada() {
    var modal = document.getElementById('modal-actividad-creada');
    if (modal) modal.style.display = 'none';
    var url = window.location.pathname + window.location.search.replace(/[?&]actividad_creada=1/, '');
    window.history.replaceState({}, '', url);
}

(function chequearActividadCreada() {
    document.addEventListener('DOMContentLoaded', function () {
        var params = new URLSearchParams(window.location.search);
        if (params.get('actividad_creada') === '1') {
            var modal = document.getElementById('modal-actividad-creada');
            if (modal) modal.style.display = 'flex';
        }
    });
})();

/* ============================================================
   12. MODAL TICKET CREADO – NuevoTicket.html
   ============================================================ */

function cerrarModalTicketCreado() {
    var modal = document.getElementById('modal-ticket-creado');
    if (modal) modal.style.display = 'none';
    var url = window.location.pathname + window.location.search.replace(/[?&]ticket_creado=1/, '');
    window.history.replaceState({}, '', url);
}

(function chequearTicketCreado() {
    document.addEventListener('DOMContentLoaded', function () {
        var params = new URLSearchParams(window.location.search);
        if (params.get('ticket_creado') === '1') {
            var modal = document.getElementById('modal-ticket-creado');
            if (modal) modal.style.display = 'flex';
        }
    });
})();

/* ============================================================
   13. MODAL CONFIRMAR ELIMINAR TICKET – gestionTicket.html
   ============================================================ */

var _ticketAEliminar = null;

function mostrarModalEliminarTicket(idTicket, titulo) {
    _ticketAEliminar = idTicket;
    var msg = document.getElementById('modal-eliminar-ticket-msg');
    if (msg) {
        var txt = '¿Eliminar permanentemente el ticket SD-' + idTicket;
        if (titulo) txt += ' (' + titulo + ')';
        txt += '? Esta acci\u00f3n no se puede deshacer.';
        msg.textContent = txt;
    }
    var form = document.getElementById('form-eliminar-ticket-modal');
    if (form) {
        form.action = '/ticket/' + idTicket + '/eliminar';
    }
    var modal = document.getElementById('modal-confirmar-eliminar-ticket');
    if (modal) modal.style.display = 'flex';
}

function cerrarModalEliminarTicket() {
    var modal = document.getElementById('modal-confirmar-eliminar-ticket');
    if (modal) modal.style.display = 'none';
    _ticketAEliminar = null;
}


/* ============================================================
   REPORTES — ACTIVIDADES POR PROYECTO
   ============================================================ */

var _actividadesCargadas = {}; // cache: id_proyecto → {actividades, resumen}

/* Chips de estado/prioridad para actividades */
function _chipEstadoAct(estado) {
    var map = {
        'completada':  'rep-chip-verde',
        'en_progreso': 'rep-chip-azul',
        'por_hacer':   'rep-chip-naranja',
        'backlog':     'rep-chip-gris',
        'cancelada':   'rep-chip-rojo'
    };
    return '<span class="rep-chip ' + (map[estado] || 'rep-chip-gris') + '">' + estado.replace('_',' ') + '</span>';
}
function _chipPrioridadAct(prioridad) {
    var map = { 'critica': 'rep-chip-rojo', 'alta': 'rep-chip-rojo', 'media': 'rep-chip-naranja', 'baja': 'rep-chip-gris' };
    return '<span class="rep-chip ' + (map[prioridad] || 'rep-chip-gris') + '">' + prioridad + '</span>';
}

/* Renderiza el panel de actividades de un proyecto */
function _renderActividades(idProyecto, nombreProyecto, data) {
    var r = data.resumen;
    var acts = data.actividades;
    var pctComp = r.total > 0 ? Math.round((r.completadas / r.total) * 100) : 0;

    var html = '<div class="rep-act-titulo">'
             + '<span>Actividades de: <strong>' + nombreProyecto + '</strong></span>'
             + '<span style="font-size:0.75rem;color:var(--gris-texto);">' + r.total + ' actividad' + (r.total !== 1 ? 'es' : '') + ' · ' + pctComp + '% completado</span>'
             + '</div>';

    // KPIs
    html += '<div class="rep-act-kpis">';
    html += '<div class="rep-act-kpi kpi-total"><div class="rep-act-kpi-num">' + r.total + '</div><div class="rep-act-kpi-label">Total</div></div>';
    html += '<div class="rep-act-kpi kpi-completada"><div class="rep-act-kpi-num">' + r.completadas + '</div><div class="rep-act-kpi-label">Completadas</div></div>';
    html += '<div class="rep-act-kpi kpi-progreso"><div class="rep-act-kpi-num">' + r.en_progreso + '</div><div class="rep-act-kpi-label">En progreso</div></div>';
    html += '<div class="rep-act-kpi kpi-pendiente"><div class="rep-act-kpi-num">' + r.pendientes + '</div><div class="rep-act-kpi-label">Pendientes</div></div>';
    html += '<div class="rep-act-kpi kpi-pts"><div class="rep-act-kpi-num">' + r.pts_completados + '/' + r.total_pts + '</div><div class="rep-act-kpi-label">Pts completados</div></div>';
    html += '</div>';

    // Tabla
    if (acts.length === 0) {
        html += '<div class="rep-sin-datos">Este proyecto no tiene actividades registradas.</div>';
    } else {
        html += '<table class="rep-act-tabla">';
        html += '<thead><tr><th>Código</th><th>Título</th><th>Sprint</th><th>Asignado</th><th>Prioridad</th><th>Estado</th><th>Story pts</th></tr></thead>';
        html += '<tbody>';
        acts.forEach(function(a) {
            var eliminada = a.estado2 === 0 ? ' act-eliminada' : '';
            html += '<tr class="' + eliminada + '">';
            html += '<td class="act-codigo">' + a.codigo + '</td>';
            html += '<td>' + a.titulo + (a.estado2 === 0 ? ' <span class="rep-chip rep-chip-eliminado">Eliminada</span>' : '') + '</td>';
            html += '<td>' + a.sprint + '</td>';
            html += '<td>' + a.asignado + '</td>';
            html += '<td>' + _chipPrioridadAct(a.prioridad) + '</td>';
            html += '<td>' + _chipEstadoAct(a.estado) + '</td>';
            html += '<td style="text-align:center;font-weight:700;">' + (a.story_points || 0) + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table>';
    }

    document.getElementById('contenido-act-' + idProyecto).innerHTML = html;
}

/* Toggle expandir/colapsar panel de actividades */
function toggleActividades(btn) {
    var idProyecto = btn.getAttribute('data-id');
    var panel = document.getElementById('panel-act-' + idProyecto);
    if (!panel) return;

    var abierto = panel.style.display !== 'none';
    if (abierto) {
        panel.style.display = 'none';
        btn.textContent = '▼';
        btn.classList.remove('activo');
        return;
    }

    panel.style.display = '';
    btn.textContent = '▲';
    btn.classList.add('activo');

    var nombreProy = document.querySelector('#fila-proy-' + idProyecto + ' td:nth-child(2)');
    var nombre = nombreProy ? nombreProy.textContent.trim() : 'Proyecto';

    if (_actividadesCargadas[idProyecto]) {
        _renderActividades(idProyecto, nombre, _actividadesCargadas[idProyecto]);
        return;
    }

    // Cargar via AJAX
    apiFetch('/api/reporte/proyecto/' + idProyecto + '/actividades')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.ok) {
                _actividadesCargadas[idProyecto] = data;
                _renderActividades(idProyecto, nombre, data);
            } else {
                document.getElementById('contenido-act-' + idProyecto).innerHTML =
                    '<div class="rep-sin-datos">Error al cargar actividades.</div>';
            }
        })
        .catch(function() {
            document.getElementById('contenido-act-' + idProyecto).innerHTML =
                '<div class="rep-sin-datos">Error de conexion.</div>';
        });
}

/* Exportar proyectos + sus actividades a PDF */
function exportarConActividades() {
    var jsPDF = _getjsPDF();
    if (!jsPDF) { showAlert('Error: libreria PDF no cargada.', 'error'); return; }

    var filasP   = Array.from(document.querySelectorAll('#tbody-proyectos tr[id^="fila-proy-"]'));
    var hayFiltro = filasP.some(function(f) { return f.style.display === 'none'; });
    var visibles  = hayFiltro ? filasP.filter(function(f) { return f.style.display !== 'none'; }) : filasP;

    if (visibles.length === 0) { showAlert('No hay proyectos para exportar.', 'info'); return; }

    var fecha = new Date().toLocaleDateString('es-PE');
    var ids   = visibles.map(function(tr) { return tr.id.replace('fila-proy-', ''); });
    var pendientes = ids.filter(function(id) { return !_actividadesCargadas[id]; });

    function generarPDF() {
        var doc   = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'letter' });
        var y     = _pdfHeader(doc, 'Proyectos con Actividades', 'AgroVision · ' + fecha);
        var pageW = doc.internal.pageSize.getWidth();
        var primera = true;

        visibles.forEach(function(filaTr) {
            var id     = filaTr.id.replace('fila-proy-', '');
            var celdas = filaTr.querySelectorAll('td');
            if (celdas.length < 9) return;

            if (!primera) {
                doc.addPage();
                y = _pdfHeader(doc, 'Proyectos con Actividades (cont.)', 'AgroVision · ' + fecha);
            }
            primera = false;

            var nombre    = _limpiarTexto(celdas[1].textContent);
            var eliminado = filaTr.classList.contains('rep-fila-eliminada');

            // Barra azul/gris con nombre del proyecto
            doc.setFillColor(eliminado ? 100 : 30, eliminado ? 100 : 95, eliminado ? 100 : 168);
            doc.rect(10, y, pageW - 20, 9, 'F');
            doc.setTextColor(255, 255, 255);
            doc.setFontSize(10);
            doc.setFont('helvetica', 'bold');
            doc.text('#' + id + ' - ' + nombre + (eliminado ? '  [ELIMINADO]' : ''), 13, y + 6.2);
            doc.setTextColor(26, 30, 36);
            y += 11;

            // Info del proyecto como tabla
            var hdrsInfo = ['Responsable', 'Estado', 'Inicio', 'Fecha fin', 'Avance', 'Salud'];
            var filaInfo = [[
                _limpiarTexto(celdas[2].textContent),
                _limpiarTexto(celdas[3].textContent),
                _limpiarTexto(celdas[4].textContent),
                _limpiarTexto(celdas[5].textContent),
                _limpiarTexto(celdas[6].textContent),
                _limpiarTexto(celdas[7].textContent)
            ]];
            doc.autoTable({
                startY: y,
                head: [hdrsInfo],
                body: filaInfo,
                theme: 'grid',
                headStyles: { fillColor: [50, 50, 50], textColor: 255, fontSize: 7, fontStyle: 'bold', cellPadding: 3 },
                bodyStyles: { fontSize: 7, cellPadding: 3, textColor: [26, 30, 36] },
                margin: { left: 10, right: 10 },
                didParseCell: function(data) {
                    if (data.section === 'body') {
                        var val = data.cell.raw;
                        if (data.column.index === 1) {
                            if (val === 'Completado')    { data.cell.styles.textColor = [26, 122, 74];  data.cell.styles.fontStyle = 'bold'; }
                            if (val === 'En desarrollo') { data.cell.styles.textColor = [30, 95, 168];  data.cell.styles.fontStyle = 'bold'; }
                            if (val === 'Pausado')       { data.cell.styles.textColor = [192, 57, 43]; }
                        }
                        if (data.column.index === 5) {
                            if (val === 'Completado' || val === 'OK') { data.cell.styles.textColor = [26, 122, 74]; data.cell.styles.fontStyle = 'bold'; }
                            if (val === 'Vencido')    { data.cell.styles.textColor = [192, 57, 43]; data.cell.styles.fontStyle = 'bold'; }
                            if (val === 'Por vencer') { data.cell.styles.textColor = [240, 165, 0];  data.cell.styles.fontStyle = 'bold'; }
                            if (val === 'Eliminado')  { data.cell.styles.textColor = [150, 150, 150]; }
                        }
                    }
                }
            });
            y = doc.lastAutoTable.finalY + 5;

            // Actividades
            var data = _actividadesCargadas[id];
            if (!data || data.actividades.length === 0) {
                doc.setFontSize(7);
                doc.setTextColor(108, 117, 125);
                doc.text('Sin actividades registradas.', 10, y);
                doc.setTextColor(26, 30, 36);
                y += 8;
                return;
            }

            // KPI resumen
            var r = data.resumen;
            doc.setFont('helvetica', 'bold');
            doc.text(
                'Actividades — Total: ' + r.total +
                '   Completadas: ' + r.completadas +
                '   En progreso: ' + r.en_progreso +
                '   Pendientes: '  + r.pendientes +
                '   Pts: ' + r.pts_completados + '/' + r.total_pts,
                10, y
            );
            doc.setFont('helvetica', 'normal');
            y += 5;

            // Tabla de actividades con colores por estado
            var hdrsAct  = ['Codigo', 'Titulo', 'Sprint', 'Asignado', 'Prioridad', 'Estado', 'Pts'];
            var filasAct = [];
            data.actividades.forEach(function(a) {
                filasAct.push([
                    _limpiarTexto(a.codigo),
                    _limpiarTexto(a.titulo) + (a.estado2 === 0 ? ' [Eliminada]' : ''),
                    _limpiarTexto(a.sprint),
                    _limpiarTexto(a.asignado),
                    _limpiarTexto(a.prioridad),
                    _limpiarTexto(a.estado.replace(/_/g, ' ')),
                    String(a.story_points || 0)
                ]);
            });

            // autoTable con colores por estado en la columna Estado
            doc.autoTable({
                startY: y,
                head: [hdrsAct],
                body: filasAct,
                theme: 'grid',
                headStyles: { fillColor: [26, 122, 74], textColor: 255, fontSize: 7, fontStyle: 'bold', cellPadding: 3 },
                bodyStyles: { fontSize: 7, cellPadding: 3, textColor: [26, 30, 36] },
                alternateRowStyles: { fillColor: [245, 246, 248] },
                margin: { left: 10, right: 10 },
                columnStyles: {
                    0: { cellWidth: 22, fontStyle: 'bold', textColor: [108, 117, 125] },
                    4: { cellWidth: 22 },
                    5: { cellWidth: 28 },
                    6: { cellWidth: 12, halign: 'center', fontStyle: 'bold' }
                },
                didParseCell: function(data) {
                    if (data.section === 'body' && data.column.index === 5) {
                        var est = data.cell.raw;
                        if (est === 'completada')  { data.cell.styles.textColor = [26, 122, 74]; data.cell.styles.fontStyle = 'bold'; }
                        if (est === 'en progreso') { data.cell.styles.textColor = [30, 95, 168]; data.cell.styles.fontStyle = 'bold'; }
                        if (est === 'cancelada')   { data.cell.styles.textColor = [192, 57, 43]; }
                    }
                    if (data.section === 'body' && data.column.index === 4) {
                        var pri = data.cell.raw;
                        if (pri === 'critica' || pri === 'alta') { data.cell.styles.textColor = [192, 57, 43]; data.cell.styles.fontStyle = 'bold'; }
                    }
                }
            });
            y = doc.lastAutoTable.finalY + 10;
        });

        doc.save('Proyectos_con_Actividades_AgroVision.pdf');
    }

    if (pendientes.length === 0) {
        generarPDF();
    } else {
        var promesas = pendientes.map(function(id) {
            return apiFetch('/api/reporte/proyecto/' + id + '/actividades')
                .then(function(r) { return r.json(); })
                .then(function(data) { if (data.ok) _actividadesCargadas[id] = data; });
        });
        Promise.all(promesas).then(generarPDF).catch(generarPDF);
    }
    var _avanceEliminarId = null;

function mostrarModalEliminarAvance(idAvance, fecha) {
    _avanceEliminarId = idAvance;
    document.getElementById('lbl-fecha-avance').textContent = fecha;
    document.getElementById('modal-eliminar-avance').style.display = 'flex';
}

function cerrarModalEliminarAvance() {
    _avanceEliminarId = null;
    document.getElementById('modal-eliminar-avance').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    var btnConf = document.getElementById('btn-confirmar-eliminar-avance');
    if(btnConf) {
        btnConf.addEventListener('click', function() {
            if(!_avanceEliminarId) return;
            btnConf.textContent = 'Eliminando...';
            btnConf.disabled = true;

            apiFetch('/api/avance/' + _avanceEliminarId + '/eliminar', {
                method: 'POST'
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if(data.ok) {
                    location.reload(); // Recarga para actualizar gráficos y tabla
                } else {
                    mostrarModalAviso(data.mensaje || 'Error al eliminar el reporte. Conflicto de integridad.');
                    btnConf.textContent = 'Sí, eliminar';
                    btnConf.disabled = false;
                }
            })
            .catch(function() {
                showAlert('Error de conexión.', 'error');
                btnConf.textContent = 'Sí, eliminar';
                btnConf.disabled = false;
            });
        });
    }
});
}

/* ============================================================
   14. GESTIÓN DE TICKETS – gestionTicket.html
   ============================================================ */

function obtenerUsuarioSesion() {
    try {
        var raw = localStorage.getItem('usuario');
        if (!raw) return null;
        return JSON.parse(raw);
    } catch(e) { return null; }
}

function filtrarBotonesEditarTicket() {
    var usuario = obtenerUsuarioSesion();
    if (!usuario || usuario.id_usuario == null) return;
    var userId = String(usuario.id_usuario).trim();
    document.querySelectorAll('.btn-editar-ticket').forEach(function(btn) {
        var sid = btn.getAttribute('data-id-solicitante');
        if (sid && String(sid).trim() !== userId) {
            btn.style.display = 'none';
        }
    });
}

function usuarioPuedeVerTicket(userId, ticketUserId) {
    var usuario = obtenerUsuarioSesion();
    if (!usuario || usuario.id_usuario == null) return true;
    if (usuario.rol === 'admin') return true;
    return String(ticketUserId).trim() === String(usuario.id_usuario).trim();
}

function filtrarFilasPorRol() {
    var usuario = obtenerUsuarioSesion();
    if (!usuario) return;
    if (usuario.rol === 'admin') return;
    var userId = String(usuario.id_usuario).trim();
    document.querySelectorAll('#tbody-tickets tr').forEach(function(tr) {
        var sid   = tr.getAttribute('data-id-solicitante');
        var aid   = tr.getAttribute('data-id-agente');
        var esSolicitante = sid && String(sid).trim() === userId;
        var esAgente      = aid && String(aid).trim() === userId;
        if (!esSolicitante && !esAgente) {
            tr.style.display = 'none';
        }
    });
}

function filtrarBotonesAccion() {
    var usuario = obtenerUsuarioSesion();
    if (!usuario) return;
    var rol = usuario.rol || '';
    var uid = String(usuario.id_usuario).trim();

    // Resolver: solo visible al agente asignado
    document.querySelectorAll('.btn-resolver').forEach(function(el) {
        var aid = el.getAttribute('data-id-agente');
        if (!aid || String(aid).trim() !== uid) {
            el.style.display = 'none';
        }
    });

    document.querySelectorAll('[data-vis-asignar]').forEach(function(el) {
        var roles = (el.getAttribute('data-vis-asignar') || '').split(' ');
        if (roles.indexOf(rol) === -1) el.style.display = 'none';
    });
}

function filtrarBotonesCalificar() {
    var usuario = obtenerUsuarioSesion();
    if (!usuario || usuario.id_usuario == null) return;
    var uid = String(usuario.id_usuario).trim();
    document.querySelectorAll('.btn-calificar').forEach(function(el) {
        var sid = el.getAttribute('data-id-solicitante');
        if (!sid || String(sid).trim() !== uid) {
            el.style.display = 'none';
        }
    });
}

function renderizarFilas(tickets) {
    var tbody         = document.getElementById('tbody-tickets');
    var sinResultados = document.getElementById('sin-resultados');
    if (!tbody) return;

    if (tickets.length === 0) {
        tbody.innerHTML = '';
        sinResultados.style.display = 'block';
        return;
    }
    sinResultados.style.display = 'none';

    var badgeTipo = { incidencia: 'rojo', peticion: 'azul', consulta: 'gris' };
    var badgePrio = { critica: 'rojo', alta: 'rojo', media: 'acento', baja: 'verde' };
    var labelPrio = { critica: '🚨 Crítica', alta: 'Alta', media: 'Media', baja: 'Baja' };
    var badgeEst  = { solicitado: 'rojo', en_progreso: 'acento', resuelto: 'verde',
                      cerrado: 'gris', cancelado: 'gris' };
    var labelEst  = { solicitado: 'Solicitado', en_progreso: 'En progreso', resuelto: 'Resuelto',
                      cerrado: 'Cerrado', cancelado: 'Cancelado' };

    tbody.innerHTML = tickets.map(function(t) {
        var fecha = t.f_registro ? t.f_registro.replace('T', ' ').slice(0, 16) : '—';

        // Columna acciones
        var accion = '';
        if (t.estado === 'solicitado') {
            accion = '<div class="ticket-actions">' +
                     '<a href="/ticket/' + t.id_ticket + '/asignar" class="btn btn-sm btn-acento" data-vis-asignar="admin soporte">👤 Asignar</a>' +
                     '<a href="/ticket/' + t.id_ticket + '/editar" class="btn btn-sm btn-outline btn-editar-ticket" data-id-solicitante="' + t.id_solicitante + '">✏️ Editar</a>' +
                     '</div>';
        } else if (t.estado === 'en_progreso') {
            accion = '<div class="ticket-actions">' +
                     '<a href="/ticket/' + t.id_ticket + '/resolver" class="btn btn-sm btn-verde btn-resolver" data-id-agente="' + (t.id_agente || '') + '">🔧 Resolver</a>' +
                     '</div>';
        } else if (t.estado === 'resuelto') {
            accion = '<span class="badge badge-verde" style="opacity:.8;">✅ Resuelto</span>';
        } else {
            var isCanc = t.estado === 'cancelado';
            var badgeLabel = isCanc ? '🚫 Cancelado' : '🔒 Cerrado';
            accion = '<span class="badge badge-gris" style="opacity:.8;">' + badgeLabel + '</span>';
        }

        // Columna calificación
        var calCell = '';
        if (t.calificacion_estrellas) {
            calCell = '<span class="badge badge-acento estrella-badge">⭐ ' + t.calificacion_estrellas + '/5</span>';
        } else if (t.estado === 'resuelto') {
            calCell = '<a href="/ticket/' + t.id_ticket + '/calificar" class="btn btn-sm btn-outline btn-calificar" data-id-solicitante="' + t.id_solicitante + '">⭐ Calificar</a>';
        } else {
            calCell = '<span style="color:var(--gris-texto);">—</span>';
        }

        return '<tr data-id-solicitante="' + (t.id_solicitante || '') + '" data-id-agente="' + (t.id_agente || '') + '"' +
            ' data-sort-id_ticket="' + (t.id_ticket || 0) + '"' +
            ' data-sort-prioridad="' + (t.prioridad || 'baja') + '"' +
            ' data-sort-estado="' + (t.estado || '') + '"' +
            ' data-sort-f_registro="' + (t.f_registro || '') + '"' +
            ' data-sort-calificacion_estrellas="' + (t.calificacion_estrellas || 0) + '">' +
            '<td class="td-id ticket-id" data-label="ID"><a href="/ticket/' + t.id_ticket + '" class="ticket-link">SD-' + t.id_ticket + '</a></td>' +
            '<td class="td-titulo" data-label="Título"><a href="/ticket/' + t.id_ticket + '" class="ticket-link"><strong>' + (t.titulo || '') + '</strong></a></td>' +
            '<td data-label="Tipo"><span class="badge badge-' + (badgeTipo[t.tipo] || 'gris') + '">' + (t.tipo || '—') + '</span></td>' +
            '<td data-label="Prioridad"><span class="badge badge-' + (badgePrio[t.prioridad] || 'gris') + '">' + (labelPrio[t.prioridad] || t.prioridad) + '</span></td>' +
            '<td class="col-aplicacion" data-label="Aplicación" style="color:var(--gris-texto);font-size:0.84rem;">' + (t.nombre_aplicacion || '—') + '</td>' +
            '<td data-label="Estado"><span class="badge badge-' + (badgeEst[t.estado] || 'gris') + '">' + (labelEst[t.estado] || t.estado) + '</span></td>' +
            '<td class="col-calificacion" data-label="Calificación">' + calCell + '</td>' +
            '<td data-label="Solicitante">' + (t.nombre_solicitante || '—') + '</td>' +
            '<td class="col-agente" data-label="Agente" style="font-size:0.84rem;color:var(--gris-texto);">' + (t.nombre_agente || '—') + '</td>' +
            '<td class="col-apertura" data-label="Registro" style="font-size:0.8rem;color:var(--gris-texto);">' + fecha + '</td>' +
            '<td class="td-accion">' + accion + '</td>' +
        '</tr>';
    }).join('');
    ordenarTabla();
    filtrarBotonesEditarTicket();
    filtrarFilasPorRol();
    filtrarBotonesAccion();
    filtrarBotonesCalificar();
}

var _timerFiltroTicket = null;

function filtrarTicketsAPI() {
    clearTimeout(_timerFiltroTicket);
    _timerFiltroTicket = setTimeout(function() {
        var texto  = document.getElementById('buscar-ticket').value.trim();
        var estado = document.getElementById('filtro-estado').value;

        var params = new URLSearchParams();
        if (texto)  params.append('texto',  texto);
        if (estado) params.append('estado', estado);

        apiFetch('/api/tickets?' + params.toString())
            .then(function(r) { return r.json(); })
            .then(function(tickets) { renderizarFilas(tickets); });
    }, 300);
}

// ── ORDENAR TABLA ───────────────────────────────────────────────────────────
var _sortState = { key: 'f_registro', dir: 'desc' };
var _sortPriority = { critica: 5, alta: 4, media: 3, baja: 2 };
var _sortEstado   = { solicitado: 1, en_progreso: 2, resuelto: 3, cerrado: 4, cancelado: 5 };

function ordenarTabla() {
    var tbody = document.getElementById('tbody-tickets');
    if (!tbody) return;
    var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
    if (rows.length === 0) return;

    var key = _sortState.key;
    var dir = _sortState.dir === 'asc' ? 1 : -1;
    var type = null;
    var header = document.querySelector('th.sortable[data-sort-key="' + key + '"]');
    if (header) type = header.getAttribute('data-sort-type');

    rows.sort(function(a, b) {
        var va = (a.getAttribute('data-sort-' + key) || a.querySelector('[data-label]') && a.querySelector('[data-label]').textContent.trim() || '').toLowerCase();
        var vb = (b.getAttribute('data-sort-' + key) || b.querySelector('[data-label]') && b.querySelector('[data-label]').textContent.trim() || '').toLowerCase();

        // fallback: buscar texto interno de la celda por índice
        if (!va && !vb) {
            var idx = Array.prototype.indexOf.call(header.parentNode.children, header);
            if (idx >= 0) {
                va = (a.children[idx] && a.children[idx].textContent.trim() || '').toLowerCase();
                vb = (b.children[idx] && b.children[idx].textContent.trim() || '').toLowerCase();
            }
        }

        if (type === 'number') return dir * (parseFloat(va) - parseFloat(vb));
        if (type === 'priority') return dir * ((_sortPriority[va] || 0) - (_sortPriority[vb] || 0));
        if (type === 'date') return dir * (new Date(va) - new Date(vb));

        // Sort estado by custom order
        if (key === 'estado') return dir * ((_sortEstado[va] || 9) - (_sortEstado[vb] || 9));

        return dir * va.localeCompare(vb);
    });

    rows.forEach(function(r) { tbody.appendChild(r); });
}

function inicializarOrdenamiento() {
    document.querySelectorAll('#tabla-tickets th.sortable').forEach(function(th) {
        th.addEventListener('click', function() {
            var key = th.getAttribute('data-sort-key');
            if (_sortState.key === key) {
                _sortState.dir = _sortState.dir === 'asc' ? 'desc' : 'asc';
            } else {
                _sortState.key = key;
                _sortState.dir = 'asc';
            }
            document.querySelectorAll('#tabla-tickets th.sortable').forEach(function(h) {
                h.classList.remove('sort-active', 'sort-asc', 'sort-desc');
            });
            th.classList.add('sort-active', 'sort-' + _sortState.dir);
            ordenarTabla();
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('tabla-tickets')) return;
    inicializarOrdenamiento();
    ordenarTabla();
    filtrarBotonesEditarTicket();
    filtrarFilasPorRol();
    filtrarBotonesAccion();
    filtrarBotonesCalificar();
});