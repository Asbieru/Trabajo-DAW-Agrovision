"""
main.py  -  Servidor Flask  (AgroVision · bd_proyectofinal)
"""

from flask import Flask, render_template, request, redirect, url_for, Response, session

from usuarioAD import (autenticarUsuario, buscarUsuarioPorCorreo, obtenerUsuarios)
from ticketAD import (Ticket, listarTickets, insertarTicket, obtenerTicket, resolverTicket)
from historiasAD import (Historia, listarHistorias, insertarHistoria,
                         actualizarEstadoHistoria, listarTodosSprints)
from proyectoAD import (Proyecto, listarProyectos, insertarProyecto,
                        obtenerProyecto, actualizarProyecto,
                        resumenHistoriasPorProyecto)
from indicadoresAD import (resumenKPI, kpiPorAplicacion, kpiPorPrioridad,
                            kpiPorAgente, kpiPorMes, kpiSprintsActivos)
from reportesAD import (reporteResumen, reporteTicketsPorApp, reporteTicketsPorTipo,
                         reporteStoryPointsPorProgramador, reporteCarryoverPorProgramador,
                         reporteTicketsFiltrados, generarCSV, obtenerAplicaciones)

app = Flask(__name__)
app.secret_key = 'agrovision-clave-secreta-2024'  # necesario para usar session de Flask

# ──────────────────────────────────────────────────────────────
#  RUTA RAIZ
# ──────────────────────────────────────────────────────────────

@app.route('/')
def raiz():
    return redirect(url_for('login'))


# ──────────────────────────────────────────────────────────────
#  LOGIN
# ──────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        correo   = request.form.get('correo', '').strip()
        password = request.form.get('password', '')

        ok, mensaje, datos = autenticarUsuario(correo, password)
        if ok:
            session['usuario'] = datos
            return redirect(url_for('index'))
        else:
            error = mensaje

    return render_template('login.html', error=error)


# ──────────────────────────────────────────────────────────────
#  OLVIDÉ MI CONTRASEÑA
# ──────────────────────────────────────────────────────────────

@app.route('/olvide-contrasena', methods=['GET', 'POST'])
def olvide_contrasena():
    mensaje = None
    tipo    = None   # 'exito' o 'error' (para el color del mensaje)

    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        if buscarUsuarioPorCorreo(correo):
            mensaje = ('Si el correo está registrado, recibirás un enlace '
                       'para restablecer tu contraseña.')
            tipo = 'exito'
        else:
            mensaje = 'No se encontró una cuenta activa con ese correo.'
            tipo = 'error'

    return render_template('olvide_contrasena.html', mensaje=mensaje, tipo=tipo)


# ──────────────────────────────────────────────────────────────
#  LOGOUT
# ──────────────────────────────────────────────────────────────

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))


# ──────────────────────────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────────────────────────

@app.route('/dashboard')
def index():
    return render_template('panelDeControl.html')


# ──────────────────────────────────────────────────────────────
#  TICKETS DE SOPORTE
# ──────────────────────────────────────────────────────────────

@app.route('/ticket/nuevo')
def form_ticket():
    usuarios = obtenerUsuarios()
    return render_template('NuevoTicket.html', usuarios=usuarios)


@app.route('/ticket/guardar', methods=['POST'])
def guardar_ticket():
    try:
        obj = Ticket(
            titulo         = request.form['titulo'],
            tipo           = request.form['tipo'],
            prioridad      = request.form['prioridad'],
            aplicacion     = request.form['aplicacion'],
            id_solicitante = request.form['id_solicitante'],
            sla_horas      = request.form['sla_horas'],
            descripcion    = request.form['descripcion'],
        )
        insertarTicket(obj)
    except Exception as e:
        print(f'Error al procesar el formulario: {e}')
    return redirect(url_for('form_ticket'))


@app.route('/tickets')
def listar_tickets():
    tickets = listarTickets()
    return render_template('GestionIncidencia.html', tickets=tickets)


@app.route('/tickets/resolver')
def resolver_tickets():
    todos = listarTickets()
    pendientes = [t for t in todos if t['estado'] in ('abierto', 'en_progreso')]
    return render_template('resolverTicket.html', tickets_pendientes=pendientes)


@app.route('/ticket/<int:id_ticket>/resolver')
def form_resolver_ticket(id_ticket):
    ticket   = obtenerTicket(id_ticket)
    if not ticket:
        return redirect(url_for('listar_tickets'))
    usuarios = obtenerUsuarios()
    return render_template('resolverTicket.html', ticket=ticket, usuarios=usuarios)


@app.route('/ticket/<int:id_ticket>/resolver', methods=['POST'])
def guardar_resolucion(id_ticket):
    id_agente = request.form.get('id_agente')
    estado    = request.form.get('estado')
    notas     = request.form.get('notas_resolucion', '').strip()
    resolverTicket(id_ticket, id_agente, estado, notas)
    return redirect(url_for('listar_tickets'))


# ──────────────────────────────────────────────────────────────
#  PROYECTOS DE SOFTWARE
# ──────────────────────────────────────────────────────────────

@app.route('/proyecto/nuevo')
def form_proyecto():
    responsables = obtenerUsuarios()
    return render_template('nuevoProyecto.html', responsables=responsables)


@app.route('/proyecto/guardar', methods=['POST'])
def guardar_proyecto():
    try:
        obj = Proyecto(
            nombre         = request.form['nombre'],
            id_responsable = request.form['id_responsable'],
            estado         = request.form['estado'],
            fecha_inicio   = request.form['fecha_inicio'],
            fecha_fin_plan = request.form['fecha_fin_plan'],
            descripcion    = request.form['descripcion'],
        )
        insertarProyecto(obj)
    except Exception as e:
        print(f'Error al procesar el formulario: {e}')
    return redirect(url_for('form_proyecto'))


@app.route('/proyectos')
def listar_proyectos():
    proyectos = listarProyectos()
    return render_template('GestionIncidencia.html', proyectos=proyectos)


@app.route('/proyecto/<int:id_proyecto>/gestion')
def gestion_proyecto(id_proyecto):
    proyecto     = obtenerProyecto(id_proyecto)
    if not proyecto:
        return redirect(url_for('listar_proyectos'))

    responsables = obtenerUsuarios()
    resumen      = resumenHistoriasPorProyecto()

    # Progreso del proyecto actual
    fila_actual = None
    for r in resumen:
        if r['id_proyecto'] == id_proyecto:
            fila_actual = r
            break

    historias_total       = int(fila_actual['total']       or 0) if fila_actual else 0
    historias_completadas = int(fila_actual['completadas'] or 0) if fila_actual else 0
    pct_completado = round(historias_completadas * 100 / historias_total) if historias_total else 0

    # Badge de riesgo: fecha de fin pasada y no está completado
    fecha_fin = proyecto['fecha_fin_plan']
    from datetime import date
    hoy       = date.today()
    en_riesgo = (fecha_fin < hoy) and (proyecto['estado'] != 'completado')

    return render_template(
        'gestionProyecto.html',
        proyecto              = proyecto,
        responsables          = responsables,
        resumen               = resumen,
        historias_total       = historias_total,
        historias_completadas = historias_completadas,
        pct_completado        = pct_completado,
        en_riesgo             = en_riesgo,
    )


@app.route('/proyecto/<int:id_proyecto>/actualizar', methods=['POST'])
def actualizar_proyecto(id_proyecto):
    nombre         = request.form.get('nombre', '').strip()
    id_responsable = request.form.get('id_responsable')
    estado         = request.form.get('estado')
    descripcion    = request.form.get('descripcion', '').strip()

    ok = actualizarProyecto(id_proyecto, nombre, id_responsable, estado, descripcion)

    if ok:
        mensaje = '✅ Proyecto actualizado correctamente. Los cambios ya se reflejan en Ver proyectos.'
        tipo    = 'exito'
    else:
        mensaje = '❌ Ocurrió un error al actualizar. Intenta de nuevo.'
        tipo    = 'error'

    proyecto     = obtenerProyecto(id_proyecto)
    responsables = obtenerUsuarios()
    resumen      = resumenHistoriasPorProyecto()

    fila_actual = None
    for r in resumen:
        if r['id_proyecto'] == id_proyecto:
            fila_actual = r
            break

    historias_total       = int(fila_actual['total']       or 0) if fila_actual else 0
    historias_completadas = int(fila_actual['completadas'] or 0) if fila_actual else 0
    pct_completado = round(historias_completadas * 100 / historias_total) if historias_total else 0

    fecha_fin = proyecto['fecha_fin_plan']
    from datetime import date
    hoy       = date.today()
    en_riesgo = (fecha_fin < hoy) and (proyecto['estado'] != 'completado')

    return render_template(
        'gestionProyecto.html',
        proyecto              = proyecto,
        responsables          = responsables,
        resumen               = resumen,
        historias_total       = historias_total,
        historias_completadas = historias_completadas,
        pct_completado        = pct_completado,
        en_riesgo             = en_riesgo,
        mensaje               = mensaje,
        tipo                  = tipo,
    )


# ──────────────────────────────────────────────────────────────
#  INDICADORES DE SOPORTE
# ──────────────────────────────────────────────────────────────

@app.route('/indicadores')
def indicadores_soporte():
    resumen       = resumenKPI()
    por_app       = kpiPorAplicacion()
    por_prioridad = kpiPorPrioridad()
    por_agente    = kpiPorAgente()
    por_mes       = kpiPorMes()
    sprint_activo = kpiSprintsActivos()
    return render_template('indicadores.html',
                           resumen=resumen,
                           por_app=por_app,
                           por_prioridad=por_prioridad,
                           por_agente=por_agente,
                           por_mes=por_mes,
                           sprint_activo=sprint_activo)


# ──────────────────────────────────────────────────────────────
#  REPORTES
# ──────────────────────────────────────────────────────────────

def limpiar(valor):
    """Convierte string vacío a None, limpia espacios."""
    if valor is None:
        return None
    valor = valor.strip()
    return valor if valor else None

@app.route('/reportes')
def gestion_reportes():
    fecha_inicio = limpiar(request.args.get('fecha_inicio', ''))
    fecha_fin    = limpiar(request.args.get('fecha_fin', ''))
    aplicacion   = limpiar(request.args.get('aplicacion', ''))
    estado       = limpiar(request.args.get('estado', ''))
    prioridad    = limpiar(request.args.get('prioridad', ''))

    resumen           = reporteResumen()
    tickets_app       = reporteTicketsPorApp()
    tickets_tipo      = reporteTicketsPorTipo()
    story_points      = reporteStoryPointsPorProgramador()
    carryover         = reporteCarryoverPorProgramador()
    aplicaciones      = obtenerAplicaciones()
    tickets_filtrados = reporteTicketsFiltrados(
        fecha_inicio, fecha_fin, aplicacion, estado, prioridad
    )

    return render_template('reportes.html',
                           resumen=resumen,
                           tickets_app=tickets_app,
                           tickets_tipo=tickets_tipo,
                           story_points=story_points,
                           carryover=carryover,
                           aplicaciones=aplicaciones,
                           tickets_filtrados=tickets_filtrados,
                           fecha_inicio=fecha_inicio or '',
                           fecha_fin=fecha_fin       or '',
                           aplicacion=aplicacion     or '',
                           estado=estado             or '',
                           prioridad=prioridad       or '')


@app.route('/reportes/exportar-csv')
def exportar_csv():
    fecha_inicio = limpiar(request.args.get('fecha_inicio', ''))
    fecha_fin    = limpiar(request.args.get('fecha_fin', ''))
    aplicacion   = limpiar(request.args.get('aplicacion', ''))
    estado       = limpiar(request.args.get('estado', ''))
    prioridad    = limpiar(request.args.get('prioridad', ''))

    tickets  = reporteTicketsFiltrados(
        fecha_inicio, fecha_fin, aplicacion, estado, prioridad
    )
    csv_data = generarCSV(tickets)
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=reporte_tickets.csv'}
    )


@app.route('/historias')
def listar_historias():
    id_proyecto = request.args.get('id_proyecto', type=int)
    historias   = listarHistorias(id_proyecto)
    proyectos   = listarProyectos()
    return render_template('gestionHistorias.html',
                           historias=historias,
                           proyectos=proyectos,
                           id_proyecto_sel=id_proyecto)


@app.route('/historia/nueva')
def form_historia():
    id_proyecto_pre = request.args.get('id_proyecto', type=int)
    proyectos       = listarProyectos()
    sprints         = listarTodosSprints()
    usuarios        = obtenerUsuarios()
    return render_template('nuevaHistoria.html',
                           proyectos=proyectos,
                           sprints=sprints,
                           usuarios=usuarios,
                           id_proyecto_pre=id_proyecto_pre)


@app.route('/historia/guardar', methods=['POST'])
def guardar_historia():
    try:
        obj = Historia(
            id_proyecto  = request.form['id_proyecto'],
            id_sprint    = request.form.get('id_sprint') or None,
            id_asignado  = request.form.get('id_asignado') or None,
            codigo       = request.form['codigo'],
            titulo       = request.form['titulo'],
            tipo         = request.form['tipo'],
            prioridad    = request.form['prioridad'],
            estado       = request.form['estado'],
            story_points = request.form.get('story_points') or 0,
        )
        insertarHistoria(obj)
    except Exception as e:
        print(f'Error al guardar historia: {e}')
    return redirect(url_for('listar_historias'))


@app.route('/historia/<int:id_historia>/estado', methods=['POST'])
def cambiar_estado_historia(id_historia):
    nuevo_estado = request.form.get('estado')
    actualizarEstadoHistoria(id_historia, nuevo_estado)
    return redirect(request.referrer or url_for('listar_historias'))

# ──────────────────────────────────────────────────────────────
#  ARRANQUE
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)