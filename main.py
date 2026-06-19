"""
main.py  -  Servidor Flask  (AgroVision · bd_proyectofinal)
Sin uso de session ni import json.
"""


from flask import Flask, render_template, request, redirect, url_for, abort, jsonify, make_response
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from usuarioAD import (autenticarUsuario, buscarUsuarioPorCorreo, obtenerUsuarios,
                       listarUsuariosCompleto, obtenerPerfilUsuario,
                       estadisticasUsuario, historialParticipacionUsuario,
                       resumenHistorialUsuario)
from ticketAD import (Ticket, listarTickets, insertarTicket, obtenerTicket,
                      resolverTicket, guardarCalificacionTicket,
                      editarTicket, cancelarTicket, listarAplicaciones,
                      listarAplicacionesActivas,
                      listarPosiblesAgentes, asignarTicket,
                      obtenerAplicacion, calcularSLA,
                      insertarAplicacion, editarAplicacion, eliminarAplicacion,
                      toggleEstadoAplicacion)
from actividadAD import (Actividad, listarActividades, insertarActividad,
                         actualizarEstadoActividad, eliminarActividad,
                         desbloquearActividad,
                         listarTodosSprints, listarAsignadosPorProyecto,
                         resumenActividadesPorProyecto, proximoCodigo)
from proyectoAD import (Proyecto, listarProyectos, insertarProyecto,
                        obtenerProyecto, actualizarProyecto,
                        listarAvances, insertarAvance, eliminarAvance,
                        eliminarProyecto, tieneActividadesPendientes,
                        listarProyectosEnRevision, aprobarProyecto, rechazarProyecto,
                        generarSprintsProyecto, listarSprintsPorProyecto)
from indicadoresAD import (resumenKPI, kpiPorAplicacion, kpiPorPrioridad,
                            kpiPorAgente, kpiPorMes, kpiSprintsActivos,
                            kpiSatisfaccion, comentariosCalificacionesRecientes,
                            kpiProyectosPorEstado, kpiVelocityPorSprint,
                            kpiCargaPorProgramador, kpiTiempoRespuesta,
                            kpiPorIntensidad, kpiSLAPorAgente,
                            kpiProyectosPorSalud, kpiAvancePromedioPorProyecto,
                            kpiTiempoResolucionPorAplicacion,
                            kpiCancelados, kpiRankingAppsProblemáticas,
                            kpiPorTipo, kpiTop5MasLentos,
                            kpiActividadesPorEstado, kpiProgramadoresSinCarga,
                            kpiProyectosVencidos)
from reportesAD import (reporteResumen, reporteTicketsPorApp, reporteTicketsPorTipo,
                         reporteStoryPointsPorProgramador, reporteCarryoverPorProgramador,
                         reporteTicketsFiltrados, obtenerAplicaciones,
                         reporteProyectosPorEstado, reporteProyectosEnRiesgo,
                         reporteRendimientoPorSprint, reporteProyectosFiltrados,
                         obtenerResponsables,
                         reporteActividadesPorProyecto, resumenActividadesReporte,
                         reporteSLAPorAplicacion, reporteTicketsPorEstado,
                         reporteAgentesMetricas, reporteTendenciaPorMes)

app = Flask(__name__)
app.secret_key = 'agrovision-clave-secreta-2024'

# ──────────────────────────────────────────────────────────────
#  MANEJADORES DE ERROR
# ──────────────────────────────────────────────────────────────

@app.errorhandler(400)
def error_400(e):
    return render_template('error400.html'), 400

@app.errorhandler(404)
def error_404(e):
    return render_template('error404.html'), 404

@app.errorhandler(500)
def error_500(e):
    return render_template('error500.html'), 500

@app.route('/error-500')
def pagina_error_500():
    """Ruta directa para redirigir a la página de error 500 desde JS."""
    return render_template('error500.html'), 500

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

        try:
            ok, mensaje, datos = autenticarUsuario(correo, password)
        except Exception as e:
            print(f'Error de conexión al autenticar: {e}')
            abort(500)

        if ok:
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
    tipo    = None

    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        try:
            encontrado = buscarUsuarioPorCorreo(correo)
        except Exception as e:
            print(f'Error de conexión al buscar correo: {e}')
            abort(500)

        if encontrado:
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
    aplicaciones = listarAplicacionesActivas()
    return render_template('NuevoTicket.html', aplicaciones=aplicaciones)


@app.route('/ticket/guardar', methods=['POST'])
def guardar_ticket():
    try:
        obj = Ticket(
            titulo                = request.form['titulo'],
            tipo                  = request.form['tipo'],
            id_solicitante        = request.form['id_solicitante'],
            id_aplicacion         = request.form['id_aplicacion'],
            descripcion           = request.form['descripcion'],
            link_img_descripcion  = request.form.get('link_img_descripcion', '').strip() or None,
        )
        insertarTicket(obj)
    except KeyError:
        abort(400)
    except Exception as e:
        print(f'Error al guardar ticket: {e}')
        abort(500)
    return redirect(url_for('form_ticket') + '?ticket_creado=1')


@app.route('/tickets')
def listar_tickets():
    try:
        tickets = listarTickets()
    except Exception as e:
        print(f'Error al listar tickets: {e}')
        abort(500)
    return render_template('gestionTicket.html', tickets=tickets)


@app.route('/tickets/resolver')
def resolver_tickets():
    todos = listarTickets()
    pendientes = [t for t in todos if t['estado'] == 'en_progreso']
    return render_template('resolverTicket.html', tickets_pendientes=pendientes)


@app.route('/ticket/<int:id_ticket>')
def ver_ticket(id_ticket):
    ticket = obtenerTicket(id_ticket)
    if not ticket:
        abort(404)
    return render_template('verTicket.html', ticket=ticket)


@app.route('/ticket/<int:id_ticket>/resolver')
def form_resolver_ticket(id_ticket):
    ticket   = obtenerTicket(id_ticket)
    if not ticket or ticket['estado'] != 'en_progreso':
        return redirect(url_for('listar_tickets'))
    usuarios = obtenerUsuarios()
    aplicaciones = listarAplicaciones()
    return render_template('resolverTicket.html', ticket=ticket, usuarios=usuarios, aplicaciones=aplicaciones)


@app.route('/ticket/<int:id_ticket>/resolver', methods=['POST'])
def guardar_resolucion(id_ticket):
    id_agente            = request.form.get('id_agente')
    notas                = request.form.get('notas_resolucion', '').strip()
    link_img_resolucion  = request.form.get('link_img_resolucion', '').strip() or None
    resolverTicket(id_ticket, id_agente, 'resuelto', notas, link_img_resolucion)
    return redirect(url_for('listar_tickets'))


@app.route('/ticket/<int:id_ticket>/calificar', methods=['GET', 'POST'])
def calificar_ticket(id_ticket):
    ticket = obtenerTicket(id_ticket)
    if not ticket:
        abort(404)

    if ticket['estado'] != 'resuelto':
        abort(400)

    mensaje = None
    tipo = None

    if request.method == 'POST':
        estrellas_raw = request.form.get('estrellas', '').strip()
        observacion = request.form.get('observacion', '').strip()

        try:
            estrellas = int(estrellas_raw)
        except (TypeError, ValueError):
            estrellas = None

        if estrellas not in (1, 2, 3, 4, 5):
            mensaje = 'Selecciona una calificación válida entre 1 y 5 estrellas.'
            tipo = 'error'
        else:
            guardarCalificacionTicket(id_ticket, estrellas, observacion)
            ticket = obtenerTicket(id_ticket)
            mensaje = 'Gracias. Tu calificación fue registrada correctamente.'
            tipo = 'exito'

    return render_template('calificarTicket.html',
                           ticket=ticket,
                           mensaje=mensaje,
                           tipo=tipo)


# ── EDITAR TICKET (solicitado o en_progreso) ──────────────────────────────────
@app.route('/ticket/<int:id_ticket>/editar', methods=['GET'])
def form_editar_ticket(id_ticket):
    ticket = obtenerTicket(id_ticket)
    if not ticket or ticket['estado'] != 'solicitado':
        return redirect(url_for('listar_tickets'))
    aplicaciones = listarAplicaciones()
    return render_template('editarTicket.html', ticket=ticket, aplicaciones=aplicaciones)


@app.route('/ticket/<int:id_ticket>/editar', methods=['POST'])
def guardar_edicion_ticket(id_ticket):
    ticket = obtenerTicket(id_ticket)
    if not ticket or ticket['estado'] != 'solicitado':
        return redirect(url_for('listar_tickets'))

    titulo                = request.form.get('titulo', '').strip()
    tipo                  = request.form.get('tipo', '')
    id_aplicacion         = request.form.get('id_aplicacion', '')
    descripcion           = request.form.get('descripcion', '').strip()
    link_img_descripcion  = request.form.get('link_img_descripcion', '').strip() or None

    if not titulo:
        return redirect(url_for('form_editar_ticket', id_ticket=id_ticket))

    editarTicket(id_ticket, titulo, tipo, id_aplicacion, descripcion, link_img_descripcion)
    return redirect(url_for('listar_tickets'))


# ── CANCELAR TICKET ───────────────────────────────────────────────────────────
@app.route('/ticket/<int:id_ticket>/cancelar', methods=['POST'])
def cancelar_ticket(id_ticket):
    cancelarTicket(id_ticket)
    return redirect(url_for('listar_tickets'))


# ── ASIGNAR AGENTE ────────────────────────────────────────────────────────────
@app.route('/ticket/<int:id_ticket>/asignar')
def form_asignar_ticket(id_ticket):
    ticket = obtenerTicket(id_ticket)
    if not ticket or ticket['estado'] != 'solicitado':
        return redirect(url_for('listar_tickets'))
    agentes = listarPosiblesAgentes()
    aplicaciones = listarAplicaciones()
    return render_template('asignarTicket.html', ticket=ticket, agentes=agentes, aplicaciones=aplicaciones)


@app.route('/ticket/<int:id_ticket>/asignar', methods=['POST'])
def guardar_asignacion(id_ticket):
    id_agente = request.form.get('id_agente')
    if not id_agente:
        return redirect(url_for('form_asignar_ticket', id_ticket=id_ticket))
    prioridad     = request.form.get('prioridad', 'media')
    intensidad    = request.form.get('intensidad', 'media')
    sla_raw       = request.form.get('sla_horas', '').strip()
    if sla_raw:
        sla_horas = int(sla_raw)
    else:
        id_app = request.form.get('id_aplicacion_hidden', '')
        app_data = obtenerAplicacion(int(id_app)) if id_app else None
        sla_horas = calcularSLA(prioridad, intensidad,
                                app_data['peso'] if app_data else 3,
                                app_data['participantes_promedio'] if app_data else 5)
    try:
        asignarTicket(id_ticket, int(id_agente), prioridad, intensidad, sla_horas)
    except ValueError:
        return redirect(url_for('listar_tickets'))
    except Exception as e:
        print(f'Error al asignar ticket: {e}')
        abort(500)
    return redirect(url_for('listar_tickets'))


# ──────────────────────────────────────────────────────────────
#  APLICACIONES CRUD  (solo admin)
# ──────────────────────────────────────────────────────────────

@app.route('/aplicaciones')
def listar_aplicaciones():
    aplicaciones = listarAplicaciones()
    return render_template('gestionAplicaciones.html', aplicaciones=aplicaciones)


@app.route('/aplicacion/nueva', methods=['GET', 'POST'])
def nueva_aplicacion():
    if request.method == 'POST':
        nombre                = request.form.get('nombre', '').strip()
        peso                  = request.form.get('peso', 3)
        descripcion           = request.form.get('descripcion', '').strip()
        participantes_promedio = request.form.get('participantes_promedio', 5)
        if nombre:
            insertarAplicacion(nombre, peso, descripcion, participantes_promedio)
            return redirect(url_for('listar_aplicaciones') + '?creada=1')
    return render_template('formularioAplicacion.html', aplicacion=None)


@app.route('/aplicacion/<int:id_aplicacion>/editar', methods=['GET', 'POST'])
def editar_aplicacion_route(id_aplicacion):
    app = obtenerAplicacion(id_aplicacion)
    if not app:
        abort(404)
    if request.method == 'POST':
        nombre                = request.form.get('nombre', '').strip()
        peso                  = request.form.get('peso', 3)
        descripcion           = request.form.get('descripcion', '').strip()
        participantes_promedio = request.form.get('participantes_promedio', 5)
        if nombre:
            editarAplicacion(id_aplicacion, nombre, peso, descripcion, participantes_promedio)
            return redirect(url_for('listar_aplicaciones') + '?editada=1')
    return render_template('formularioAplicacion.html', aplicacion=app)


@app.route('/aplicacion/<int:id_aplicacion>/eliminar', methods=['POST'])
def eliminar_aplicacion_route(id_aplicacion):
    eliminarAplicacion(id_aplicacion)
    return redirect(url_for('listar_aplicaciones') + '?eliminada=1')


@app.route('/aplicacion/<int:id_aplicacion>/toggle-estado', methods=['POST'])
def toggle_estado_aplicacion(id_aplicacion):
    toggleEstadoAplicacion(id_aplicacion)
    return redirect(url_for('listar_aplicaciones'))


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
        from datetime import date
        ids_responsables = request.form.getlist('responsables')
        if not ids_responsables:
            abort(400)
        obj = Proyecto(
            nombre           = request.form['nombre'],
            ids_responsables = ids_responsables,
            estado           = 'en_revision',
            fecha_inicio     = date.today().strftime('%Y-%m-%d'),
            fecha_fin_plan   = request.form['fecha_fin_plan'],
            problematica     = request.form.get('problematica', '').strip() or None,
            justificacion    = request.form.get('justificacion', '').strip() or None,
            beneficios       = request.form.get('beneficios', '').strip() or None,
            descripcion      = request.form['descripcion'],
        )
        insertarProyecto(obj)
    except KeyError:
        abort(400)
    except Exception as e:
        print(f'Error al guardar proyecto: {e}')
        abort(500)
    return redirect(url_for('form_proyecto') + '?creado=1')


@app.route('/proyecto/<int:id_proyecto>/editar')
def form_editar_proyecto(id_proyecto):
    proyecto = obtenerProyecto(id_proyecto)
    if not proyecto:
        abort(404)
    responsables = obtenerUsuarios()
    from proyectoAD import obtenerResponsablesProyecto
    ids_responsables_actuales = obtenerResponsablesProyecto(id_proyecto)
    return render_template('editarProyecto.html',
                           proyecto=proyecto,
                           responsables=responsables,
                           ids_responsables_actuales=ids_responsables_actuales)


@app.route('/proyecto/<int:id_proyecto>/editar', methods=['POST'])
def guardar_edicion_proyecto(id_proyecto):
    try:
        from proyectoAD import actualizarProyectoCompleto
        ids_responsables = request.form.getlist('responsables')
        if not ids_responsables:
            abort(400)
        nombre         = request.form['nombre']
        estado         = request.form['estado']
        fecha_fin_plan = request.form['fecha_fin_plan']
        descripcion    = request.form['descripcion']
        actualizarProyectoCompleto(id_proyecto, nombre, ids_responsables, estado,
                                   fecha_fin_plan, descripcion)
    except KeyError:
        abort(400)
    except Exception as e:
        print(f'Error al editar proyecto: {e}')
        abort(500)
    return redirect(url_for('form_editar_proyecto', id_proyecto=id_proyecto) + '?editado=1')


@app.route('/proyectos')
def listar_proyectos():
    try:
        proyectos = listarProyectos()
    except Exception as e:
        print(f'Error al listar proyectos: {e}')
        abort(500)
    return render_template('listaProyectos.html', proyectos=proyectos)

@app.route('/api/proyecto/<int:id_proyecto>/eliminar', methods=['POST'])
def api_eliminar_proyecto(id_proyecto):
    if tieneActividadesPendientes(id_proyecto):
        return jsonify({'ok': False, 'mensaje': 'No se puede eliminar: el proyecto tiene actividades pendientes.'})
    ok = eliminarProyecto(id_proyecto)
    if ok:
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'mensaje': 'No se pudo eliminar el proyecto.'})


@app.route('/api/reporte/proyecto/<int:id_proyecto>/actividades')
def api_reporte_actividades(id_proyecto):
    actividades = reporteActividadesPorProyecto(id_proyecto)
    resumen     = resumenActividadesReporte(id_proyecto)
    return jsonify({'ok': True, 'actividades': actividades, 'resumen': resumen})


@app.route('/proyecto/<int:id_proyecto>/gestion')
def gestion_proyecto(id_proyecto):
    proyecto = obtenerProyecto(id_proyecto)
    if not proyecto:
        abort(404)

    actividades     = listarActividades(id_proyecto)
    todos_proyectos = listarProyectos()

    fecha_fin = proyecto['fecha_fin_plan']
    from datetime import date
    hoy       = date.today()
    en_riesgo = (fecha_fin < hoy) and (proyecto['estado'] != 'completado')

    return render_template(
        'gestionProyecto.html',
        proyecto        = proyecto,
        actividades     = actividades,
        todos_proyectos = todos_proyectos,
        en_riesgo       = en_riesgo,
    )


@app.route('/proyecto/<int:id_proyecto>/avances')
def historial_avances(id_proyecto):
    proyecto = obtenerProyecto(id_proyecto)
    if not proyecto:
        abort(404)
    avances = listarAvances(id_proyecto)

    # Datos cronológicos para el gráfico (listas Python puras, sin json.dumps)
    avances_cronologicos = list(reversed(avances))
    fechas_grafico      = [av['fecha_reporte'].strftime('%d/%m') for av in avances_cronologicos] if avances else []
    porcentajes_grafico = [float(av['porcentaje_avance']) for av in avances_cronologicos]         if avances else []

    return render_template('avancesProyecto.html',
                           proyecto=proyecto,
                           avances=avances,
                           fechas_grafico=fechas_grafico,
                           porcentajes_grafico=porcentajes_grafico)


@app.route('/proyecto/<int:id_proyecto>/avances/nuevo', methods=['GET', 'POST'])
def nuevo_avance(id_proyecto):
    proyecto = obtenerProyecto(id_proyecto)
    if not proyecto:
        abort(404)

    resumen     = resumenActividadesPorProyecto()
    fila_actual = next((r for r in resumen
                        if (r['id_proyecto'] if isinstance(r, dict) else r[0]) == id_proyecto), None)

    if fila_actual:
        if isinstance(fila_actual, dict):
            valor_raw = fila_actual.get('porcentaje_avance_real')
        else:
            valor_raw = fila_actual[3]
        pct_calculado = round(float(valor_raw)) if valor_raw is not None else 0
    else:
        pct_calculado = 0

    if proyecto.get('estado') == 'completado':
        pct_calculado = 100

    from datetime import date
    hoy_mostrar = date.today().strftime('%d/%m/%Y')

    if request.method == 'POST':
        hoy_db          = date.today().strftime('%Y-%m-%d')
        estado_salud    = request.form['estado_salud']
        logros_periodo  = request.form['logros_periodo'].strip()
        pendientes_next = request.form.get('pendientes_next', '').strip()
        id_autor        = request.form.get('id_autor')

        if id_autor:
            insertarAvance(id_proyecto, id_autor, hoy_db, pct_calculado,
                           estado_salud, logros_periodo, pendientes_next)

        return redirect(url_for('historial_avances', id_proyecto=id_proyecto))

    usuarios = obtenerUsuarios()
    return render_template('nuevoAvance.html',
                           proyecto=proyecto,
                           hoy_mostrar=hoy_mostrar,
                           pct_calculado=pct_calculado,
                           usuarios=usuarios)


@app.route('/proyecto/<int:id_proyecto>/avances/eliminar/<int:id_avance>', methods=['POST'])
def eliminar_avance_ruta(id_proyecto, id_avance):
    eliminarAvance(id_avance)
    return redirect(url_for('historial_avances', id_proyecto=id_proyecto))


# ──────────────────────────────────────────────────────────────
#  INDICADORES DE SOPORTE
# ──────────────────────────────────────────────────────────────

@app.route('/indicadores')
def indicadores_soporte():
    mes_inicio  = request.args.get('mes_inicio', '')  or None
    anio_inicio = request.args.get('anio_inicio', '') or None
    mes_fin     = request.args.get('mes_fin', '')     or None
    anio_fin    = request.args.get('anio_fin', '')    or None

    resumen           = resumenKPI()
    por_app           = kpiPorAplicacion()
    por_prioridad     = kpiPorPrioridad()
    por_agente        = kpiPorAgente()
    por_mes           = kpiPorMes()
    sprint_activo     = kpiSprintsActivos()
    satisfaccion      = kpiSatisfaccion()
    comentarios       = comentariosCalificacionesRecientes()
    proyectos_estado  = kpiProyectosPorEstado()
    velocity_sprints  = kpiVelocityPorSprint()
    carga_programador = kpiCargaPorProgramador()
    tiempo_respuesta  = kpiTiempoRespuesta()
    por_intensidad    = kpiPorIntensidad()
    sla_por_agente    = kpiSLAPorAgente()
    salud_proyectos   = kpiProyectosPorSalud()
    avance_proyectos  = kpiAvancePromedioPorProyecto()
    tiempo_por_app    = kpiTiempoResolucionPorAplicacion()
    cancelados        = kpiCancelados()
    ranking_apps      = kpiRankingAppsProblemáticas()
    por_tipo          = kpiPorTipo()
    top5_lentos       = kpiTop5MasLentos()
    act_por_estado    = kpiActividadesPorEstado()
    sin_carga         = kpiProgramadoresSinCarga()
    proy_vencidos     = kpiProyectosVencidos()

    return render_template('indicadores.html',
                           resumen=resumen,
                           por_app=por_app,
                           por_prioridad=por_prioridad,
                           por_agente=por_agente,
                           por_mes=por_mes,
                           sprint_activo=sprint_activo,
                           satisfaccion=satisfaccion,
                           comentarios=comentarios,
                           proyectos_estado=proyectos_estado,
                           velocity_sprints=velocity_sprints,
                           carga_programador=carga_programador,
                           tiempo_respuesta=tiempo_respuesta,
                           por_intensidad=por_intensidad,
                           sla_por_agente=sla_por_agente,
                           salud_proyectos=salud_proyectos,
                           avance_proyectos=avance_proyectos,
                           tiempo_por_app=tiempo_por_app,
                           cancelados=cancelados,
                           ranking_apps=ranking_apps,
                           por_tipo=por_tipo,
                           top5_lentos=top5_lentos,
                           act_por_estado=act_por_estado,
                           sin_carga=sin_carga,
                           proy_vencidos=proy_vencidos,
                           mes_inicio=mes_inicio   or '',
                           anio_inicio=anio_inicio or '',
                           mes_fin=mes_fin         or '',
                           anio_fin=anio_fin       or '')


# ──────────────────────────────────────────────────────────────
#  REPORTES
# ──────────────────────────────────────────────────────────────

def limpiar(valor):
    if valor is None:
        return None
    valor = valor.strip()
    return valor if valor else None


@app.route('/reportes')
def gestion_reportes():
    fecha_inicio  = limpiar(request.args.get('fecha_inicio', ''))
    fecha_fin     = limpiar(request.args.get('fecha_fin', ''))
    id_aplicacion = limpiar(request.args.get('id_aplicacion', ''))
    estado        = limpiar(request.args.get('estado', ''))
    prioridad     = limpiar(request.args.get('prioridad', ''))

    resumen             = reporteResumen()
    tickets_app         = reporteTicketsPorApp()
    tickets_tipo        = reporteTicketsPorTipo()
    story_points        = reporteStoryPointsPorProgramador()
    carryover           = reporteCarryoverPorProgramador()
    aplicaciones        = obtenerAplicaciones()
    tickets_filtrados   = reporteTicketsFiltrados(fecha_inicio, fecha_fin,
                                                  id_aplicacion, estado, prioridad)
    proyectos_estado    = reporteProyectosPorEstado()
    proyectos_riesgo    = reporteProyectosEnRiesgo()
    rendimiento_sprint  = reporteRendimientoPorSprint()
    proyectos_filtrados = reporteProyectosFiltrados()
    responsables        = obtenerResponsables()
    sla_por_app         = reporteSLAPorAplicacion()
    tickets_por_estado  = reporteTicketsPorEstado()
    agentes_metricas    = reporteAgentesMetricas()
    tendencia_mes       = reporteTendenciaPorMes()

    return render_template('reportes.html',
                           resumen=resumen,
                           tickets_app=tickets_app,
                           tickets_tipo=tickets_tipo,
                           story_points=story_points,
                           carryover=carryover,
                           aplicaciones=aplicaciones,
                           tickets_filtrados=tickets_filtrados,
                           proyectos_estado=proyectos_estado,
                           proyectos_riesgo=proyectos_riesgo,
                           rendimiento_sprint=rendimiento_sprint,
                           proyectos_filtrados=proyectos_filtrados,
                           responsables=responsables,
                           sla_por_app=sla_por_app,
                           tickets_por_estado=tickets_por_estado,
                           agentes_metricas=agentes_metricas,
                           tendencia_mes=tendencia_mes,
                           fecha_inicio=fecha_inicio   or '',
                           fecha_fin=fecha_fin         or '',
                           id_aplicacion=id_aplicacion or '',
                           estado=estado               or '',
                           prioridad=prioridad         or '')


# ──────────────────────────────────────────────────────────────
#  EXPORTAR EXCEL
# ──────────────────────────────────────────────────────────────

def _estilo_cabecera(ws, fila, columnas, color_hex="1a5276"):
    """Aplica estilo de cabecera a una fila del worksheet."""
    fill   = PatternFill("solid", fgColor=color_hex)
    fuente = Font(bold=True, color="FFFFFF", size=10)
    borde  = Border(
        bottom=Side(style='medium', color='FFFFFF'),
        right =Side(style='thin',   color='FFFFFF')
    )
    for col_idx, titulo in enumerate(columnas, 1):
        cell = ws.cell(row=fila, column=col_idx, value=titulo)
        cell.fill      = fill
        cell.font      = fuente
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border    = borde

def _autowidth(ws, extra=4):
    """Ajusta el ancho de columnas automáticamente."""
    for col in ws.columns:
        max_len = max((len(str(c.value)) if c.value else 0) for c in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + extra, 50)

def _fila_alterna(ws, fila, n_cols, par=True):
    color = "EBF5FB" if par else "FFFFFF"
    fill  = PatternFill("solid", fgColor=color)
    for c in range(1, n_cols + 1):
        ws.cell(row=fila, column=c).fill = fill

@app.route('/reportes/exportar-excel')
def exportar_excel():
    fecha_inicio  = limpiar(request.args.get('fecha_inicio', ''))
    fecha_fin     = limpiar(request.args.get('fecha_fin', ''))
    id_aplicacion = limpiar(request.args.get('id_aplicacion', ''))
    estado        = limpiar(request.args.get('estado', ''))
    prioridad     = limpiar(request.args.get('prioridad', ''))

    tickets        = reporteTicketsFiltrados(fecha_inicio, fecha_fin, id_aplicacion, estado, prioridad)
    resumen        = reporteResumen()
    tickets_app    = reporteTicketsPorApp()
    sprints        = reporteRendimientoPorSprint()
    story_pts      = reporteStoryPointsPorProgramador()
    carryover      = reporteCarryoverPorProgramador()
    proyectos      = reporteProyectosFiltrados()
    tiempo_res     = kpiPorAgente()          # promedio horas resolución por agente

    wb = Workbook()

    # ── HOJA 1: Tickets filtrados ──────────────────────────────
    ws1 = wb.active
    ws1.title = "Tickets"
    ws1.row_dimensions[1].height = 30

    cabeceras_t = [
        "#", "Título", "Aplicación", "Tipo", "Prioridad", "Intensidad",
        "Estado", "Solicitante", "Agente", "Fecha Apertura", "Fecha Asignación",
        "Fecha Solución", "Fecha Cierre", "SLA (h)", "Tiempo resolución",
        "SLA cumplido", "Calificación", "Observación"
    ]
    _estilo_cabecera(ws1, 1, cabeceras_t, "1a5276")

    for i, t in enumerate(tickets, 2):
        mins = t.get('minutos_resolucion')
        if mins is not None:
            horas, resto = divmod(int(mins), 60)
            tiempo_str   = f"{horas}h {resto}m"
        else:
            tiempo_str = "—"

        fila = [
            t.get('id_ticket'),
            t.get('titulo'),
            t.get('aplicacion'),
            t.get('tipo', '').capitalize(),
            t.get('prioridad', '').capitalize(),
            t.get('intensidad', '').capitalize(),
            (t.get('estado') or '').replace('_', ' ').capitalize(),
            t.get('solicitante'),
            t.get('agente') or '—',
            t.get('fecha_apertura') or '—',
            t.get('fecha_asignacion') or '—',
            t.get('fecha_solucion') or '—',
            t.get('fecha_cierre') or '—',
            t.get('sla_horas') or '—',
            tiempo_str,
            t.get('sla_cumplido') or '—',
            t.get('calificacion') or '—',
            t.get('obs_calificacion') or '—',
        ]
        for col_idx, valor in enumerate(fila, 1):
            cell = ws1.cell(row=i, column=col_idx, value=valor)
            cell.alignment = Alignment(vertical='center', wrap_text=True)
            # Color SLA
            if col_idx == 16:
                if valor == 'SI':
                    cell.font = Font(color="1E8449", bold=True)
                elif valor == 'NO':
                    cell.font = Font(color="C0392B", bold=True)
        _fila_alterna(ws1, i, len(cabeceras_t), i % 2 == 0)
        ws1.row_dimensions[i].height = 18
    _autowidth(ws1)
    ws1.freeze_panes = "A2"

    # ── HOJA 2: Tickets por Aplicación ────────────────────────
    ws2 = wb.create_sheet("Por Aplicación")
    _estilo_cabecera(ws2, 1, ["Aplicación", "Total", "Pendientes", "Cerrados"], "1f618d")
    for i, r in enumerate(tickets_app, 2):
        r = dict(r)
        ws2.cell(row=i, column=1, value=r.get('aplicacion'))
        ws2.cell(row=i, column=2, value=r.get('total'))
        ws2.cell(row=i, column=3, value=r.get('pendientes') or 0)
        ws2.cell(row=i, column=4, value=r.get('cerrados') or 0)
        _fila_alterna(ws2, i, 4, i % 2 == 0)
    _autowidth(ws2)
    ws2.freeze_panes = "A2"

    # ── HOJA 3: Rendimiento por Sprint ────────────────────────
    ws3 = wb.create_sheet("Sprints")
    _estilo_cabecera(ws3, 1,
        ["Sprint", "Proyecto", "Capacidad (pts)", "Completados (pts)", "Pendientes (pts)",
         "% Completado", "Estado"], "1b4f72")
    for i, s in enumerate(sprints, 2):
        s = dict(s)
        cap  = s.get('capacidad_pts') or 0
        comp = s.get('pts_completados') or 0
        pct  = round(comp / cap * 100, 1) if cap else 0
        ws3.cell(row=i, column=1, value=s.get('sprint'))
        ws3.cell(row=i, column=2, value=s.get('proyecto'))
        ws3.cell(row=i, column=3, value=cap)
        ws3.cell(row=i, column=4, value=comp)
        ws3.cell(row=i, column=5, value=s.get('pts_pendientes') or 0)
        ws3.cell(row=i, column=6, value=pct)
        ws3.cell(row=i, column=7, value=(s.get('estado_sprint') or '').capitalize())
        _fila_alterna(ws3, i, 7, i % 2 == 0)
    _autowidth(ws3)
    ws3.freeze_panes = "A2"

    # ── HOJA 4: Story Points por Programador ──────────────────
    ws4 = wb.create_sheet("Story Points")
    _estilo_cabecera(ws4, 1,
        ["Programador", "Pts Completados", "Pts Asignados", "% Completado"], "145a32")
    for i, r in enumerate(story_pts, 2):
        r = dict(r)
        asig = r.get('pts_asignados') or 0
        comp = r.get('pts_completados') or 0
        pct  = round(comp / asig * 100, 1) if asig else 0
        ws4.cell(row=i, column=1, value=r.get('programador'))
        ws4.cell(row=i, column=2, value=comp)
        ws4.cell(row=i, column=3, value=asig)
        ws4.cell(row=i, column=4, value=pct)
        _fila_alterna(ws4, i, 4, i % 2 == 0)
    _autowidth(ws4)
    ws4.freeze_panes = "A2"

    # ── HOJA 5: Carryover ─────────────────────────────────────
    ws5 = wb.create_sheet("Carryover")
    _estilo_cabecera(ws5, 1,
        ["Programador", "Sprints con Carryover", "Pts Carryover"], "6e2f1a")
    for i, r in enumerate(carryover, 2):
        r = dict(r)
        ws5.cell(row=i, column=1, value=r.get('programador'))
        ws5.cell(row=i, column=2, value=r.get('sprints_con_carryover'))
        ws5.cell(row=i, column=3, value=r.get('pts_carryover'))
        _fila_alterna(ws5, i, 3, i % 2 == 0)
    _autowidth(ws5)
    ws5.freeze_panes = "A2"

    # ── HOJA 6: Proyectos ─────────────────────────────────────
    ws6 = wb.create_sheet("Proyectos")
    _estilo_cabecera(ws6, 1,
        ["#", "Proyecto", "Responsable", "Estado", "Inicio", "Fecha Fin",
         "Días restantes", "Salud"], "1b2631")
    for i, p in enumerate(proyectos, 2):
        p = dict(p)
        salud_map = {'completado': 'Completado', 'vencido': 'Vencido',
                     'por_vencer': 'Por vencer', 'ok': 'OK'}
        ws6.cell(row=i, column=1, value=p.get('id_proyecto'))
        ws6.cell(row=i, column=2, value=p.get('nombre'))
        ws6.cell(row=i, column=3, value=p.get('responsable'))
        ws6.cell(row=i, column=4, value=(p.get('estado') or '').replace('_', ' ').capitalize())
        ws6.cell(row=i, column=5, value=str(p.get('fecha_inicio') or '—'))
        ws6.cell(row=i, column=6, value=str(p.get('fecha_fin_plan') or '—'))
        ws6.cell(row=i, column=7, value=p.get('dias_restantes'))
        ws6.cell(row=i, column=8, value=salud_map.get(p.get('salud'), '—'))
        # Color en columna Salud
        salud_cell = ws6.cell(row=i, column=8)
        if p.get('salud') == 'vencido':
            salud_cell.font = Font(color="C0392B", bold=True)
        elif p.get('salud') == 'por_vencer':
            salud_cell.font = Font(color="D68910", bold=True)
        elif p.get('salud') == 'ok':
            salud_cell.font = Font(color="1E8449", bold=True)
        _fila_alterna(ws6, i, 8, i % 2 == 0)
    _autowidth(ws6)
    ws6.freeze_panes = "A2"

    # ── HOJA 7: Tiempo de resolución por agente ───────────────
    ws7 = wb.create_sheet("Tiempo Resolución")
    _estilo_cabecera(ws7, 1,
        ["Agente", "Tickets atendidos", "Resueltos",
         "Promedio resolución (h)", "Cumplimiento SLA (%)"], "4a235a")
    for i, a in enumerate(tiempo_res, 2):
        a = dict(a)
        # Buscar pct_sla del agente en sla_por_agente si existe
        ws7.cell(row=i, column=1, value=a.get('agente'))
        ws7.cell(row=i, column=2, value=a.get('total_atendidos'))
        ws7.cell(row=i, column=3, value=a.get('resueltos') or 0)
        ws7.cell(row=i, column=4, value=a.get('promedio_horas') or '—')
        _fila_alterna(ws7, i, 5, i % 2 == 0)
    _autowidth(ws7)
    ws7.freeze_panes = "A2"

    # ── Enviar el archivo ──────────────────────────────────────
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = make_response(output.read())
    response.headers['Content-Type']        = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=reporte_agrovision.xlsx'
    return response


@app.route('/reportes/exportar-excel-proyectos')
def exportar_excel_proyectos():
    estado        = limpiar(request.args.get('estado', ''))
    id_responsable = limpiar(request.args.get('id_responsable', ''))

    proyectos    = reporteProyectosFiltrados(estado or None, id_responsable or None)
    sprints      = reporteRendimientoPorSprint()

    wb = Workbook()

    # ── HOJA 1: Proyectos ─────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Proyectos"
    ws1.row_dimensions[1].height = 30
    _estilo_cabecera(ws1, 1,
        ["#", "Proyecto", "Responsable", "Estado", "Inicio", "Fecha Fin",
         "Días restantes", "Salud"], "1b2631")
    for i, p in enumerate(proyectos, 2):
        p = dict(p)
        salud_map = {'completado': 'Completado', 'vencido': 'Vencido',
                     'por_vencer': 'Por vencer', 'ok': 'OK'}
        ws1.cell(row=i, column=1, value=p.get('id_proyecto'))
        ws1.cell(row=i, column=2, value=p.get('nombre'))
        ws1.cell(row=i, column=3, value=p.get('responsable'))
        ws1.cell(row=i, column=4, value=(p.get('estado') or '').replace('_', ' ').capitalize())
        ws1.cell(row=i, column=5, value=str(p.get('fecha_inicio') or '—'))
        ws1.cell(row=i, column=6, value=str(p.get('fecha_fin_plan') or '—'))
        ws1.cell(row=i, column=7, value=p.get('dias_restantes'))
        ws1.cell(row=i, column=8, value=salud_map.get(p.get('salud'), '—'))
        salud_cell = ws1.cell(row=i, column=8)
        if p.get('salud') == 'vencido':
            salud_cell.font = Font(color="C0392B", bold=True)
        elif p.get('salud') == 'por_vencer':
            salud_cell.font = Font(color="D68910", bold=True)
        elif p.get('salud') == 'ok':
            salud_cell.font = Font(color="1E8449", bold=True)
        _fila_alterna(ws1, i, 8, i % 2 == 0)
        ws1.row_dimensions[i].height = 18
    _autowidth(ws1)
    ws1.freeze_panes = "A2"

    # ── HOJA 2: Rendimiento por Sprint ────────────────────────
    ws2 = wb.create_sheet("Sprints")
    _estilo_cabecera(ws2, 1,
        ["Sprint", "Proyecto", "Capacidad (pts)", "Completados (pts)",
         "Pendientes (pts)", "% Completado", "Estado"], "1b4f72")
    for i, s in enumerate(sprints, 2):
        s = dict(s)
        cap  = s.get('capacidad_pts') or 0
        comp = s.get('pts_completados') or 0
        pct  = round(comp / cap * 100, 1) if cap else 0
        ws2.cell(row=i, column=1, value=s.get('sprint'))
        ws2.cell(row=i, column=2, value=s.get('proyecto'))
        ws2.cell(row=i, column=3, value=cap)
        ws2.cell(row=i, column=4, value=comp)
        ws2.cell(row=i, column=5, value=s.get('pts_pendientes') or 0)
        ws2.cell(row=i, column=6, value=pct)
        ws2.cell(row=i, column=7, value=(s.get('estado_sprint') or '').capitalize())
        _fila_alterna(ws2, i, 7, i % 2 == 0)
    _autowidth(ws2)
    ws2.freeze_panes = "A2"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = make_response(output.read())
    response.headers['Content-Type']        = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=reporte_proyectos.xlsx'
    return response


# ──────────────────────────────────────────────────────────────
#  ACTIVIDADES
# ──────────────────────────────────────────────────────────────

@app.route('/actividad/nueva')
def form_actividad():
    id_proyecto_pre = request.args.get('id_proyecto', type=int)
    proyectos       = listarProyectos()
    sprints         = listarTodosSprints()
    proximo_codigo  = proximoCodigo()

    # Dict {id_proyecto: [lista de asignados]} — se pasa como dict Python normal
    asignados_json = {}
    for p in proyectos:
        pid   = p['id_proyecto']
        lista = listarAsignadosPorProyecto(pid)
        asignados_json[pid] = [{'id_usuario': u['id_usuario'],
                                'nombre_completo': u['nombre_completo']}
                               for u in lista]

    return render_template('nuevaActividad.html',
                           proyectos=proyectos,
                           sprints=sprints,
                           proximo_codigo=proximo_codigo,
                           asignados_json=asignados_json,
                           id_proyecto_pre=id_proyecto_pre)


@app.route('/actividad/guardar', methods=['POST'])
def guardar_actividad():
    try:
        id_proyecto = request.form['id_proyecto']
        obj = Actividad(
            id_proyecto  = id_proyecto,
            id_sprint    = request.form.get('id_sprint') or None,
            id_asignado  = request.form.get('id_asignado') or None,
            titulo       = request.form['titulo'],
            prioridad    = request.form['prioridad'],
            estado       = request.form['estado'],
            story_points = request.form.get('story_points') or 0,
        )
        insertarActividad(obj)
    except KeyError:
        abort(400)
    except Exception as e:
        print(f'Error al guardar actividad: {e}')
        abort(500)
    return redirect(url_for('form_actividad', id_proyecto=id_proyecto) + '&actividad_creada=1')


@app.route('/actividad/<int:id_actividad>/editar')
def form_editar_actividad(id_actividad):
    from actividadAD import obtenerActividad
    actividad = obtenerActividad(id_actividad)
    if not actividad:
        abort(404)
    proyectos  = listarProyectos()
    sprints    = listarTodosSprints()
    asignados_json = {}
    for p in proyectos:
        pid   = p['id_proyecto']
        lista = listarAsignadosPorProyecto(pid)
        asignados_json[pid] = [{'id_usuario': u['id_usuario'],
                                'nombre_completo': u['nombre_completo']}
                               for u in lista]
    return render_template('editarActividad.html',
                           actividad=actividad,
                           proyectos=proyectos,
                           sprints=sprints,
                           asignados_json=asignados_json)


@app.route('/actividad/<int:id_actividad>/editar', methods=['POST'])
def guardar_edicion_actividad(id_actividad):
    try:
        from actividadAD import actualizarActividad
        actualizarActividad(
            id_actividad = id_actividad,
            id_proyecto  = request.form['id_proyecto'],
            id_sprint    = request.form.get('id_sprint') or None,
            id_asignado  = request.form.get('id_asignado') or None,
            titulo       = request.form['titulo'],
            prioridad    = request.form['prioridad'],
            estado       = request.form['estado'],
            story_points = request.form.get('story_points') or 0,
        )
    except KeyError:
        abort(400)
    except Exception as e:
        print(f'Error al editar actividad: {e}')
        abort(500)
    return redirect(url_for('form_editar_actividad', id_actividad=id_actividad) + '?editado=1')


@app.route('/actividad/<int:id_actividad>/estado', methods=['POST'])
def cambiar_estado_actividad(id_actividad):
    nuevo_estado = request.form.get('estado')
    actualizarEstadoActividad(id_actividad, nuevo_estado)
    return redirect(request.referrer or url_for('listar_proyectos'))


# ──────────────────────────────────────────────────────────────
#  USUARIOS · Lista, Perfil e Historial
# ──────────────────────────────────────────────────────────────

@app.route('/usuarios')
def lista_usuarios():
    nombre   = request.args.get('nombre', '').strip()
    try:
        usuarios = listarUsuariosCompleto()
    except Exception as e:
        print(f'Error al listar usuarios: {e}')
        abort(500)
    if nombre:
        nombre_lower = nombre.lower()
        usuarios = [u for u in usuarios
                    if nombre_lower in u['nombre_completo'].lower()
                    or (u['apellido'] and nombre_lower in u['apellido'].lower())]
    return render_template('listaUsuarios.html', usuarios=usuarios, nombre_busqueda=nombre)


@app.route('/usuario/<int:id_usuario>/perfil')
def perfil_usuario(id_usuario):
    usuario = obtenerPerfilUsuario(id_usuario)
    if not usuario:
        abort(404)
    stats = estadisticasUsuario(id_usuario)

    # Listas Python puras — el template las serializa con el filtro tojson de Jinja2
    tickets_json   = [dict(t) for t in stats['tickets_por_tipo']]
    proyectos_json = [dict(p) for p in stats['proyectos_por_estado']]

    return render_template('perfilUsuario.html',
                           usuario=usuario,
                           stats=stats,
                           tickets_json=tickets_json,
                           proyectos_json=proyectos_json)


@app.route('/usuario/<int:id_usuario>/historial')
def historial_usuario(id_usuario):
    usuario = obtenerPerfilUsuario(id_usuario)
    if not usuario:
        abort(404)
    items   = historialParticipacionUsuario(id_usuario)
    resumen = resumenHistorialUsuario(id_usuario)
    return render_template('historialUsuario.html',
                           usuario=usuario,
                           items=items,
                           resumen=resumen)


# ──────────────────────────────────────────────────────────────
#  API JSON  (jsonify)
# ──────────────────────────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
def api_login():
    correo   = request.form.get('correo', '').strip()
    password = request.form.get('password', '')
    try:
        ok, mensaje, datos = autenticarUsuario(correo, password)
    except Exception as e:
        print(f'Error de conexión al autenticar: {e}')
        return jsonify({'ok': False, 'mensaje': 'Error de conexión con la base de datos.',
                        'error_servidor': True}), 500
    if ok:
        return jsonify({'ok': True, 'usuario': datos})
    return jsonify({'ok': False, 'mensaje': mensaje})


@app.route('/api/usuario/me')
def api_usuario_me():
    id_usuario = request.args.get('id_usuario', type=int)
    if not id_usuario:
        return jsonify({'ok': False, 'mensaje': 'Se requiere id_usuario'}), 401
    usuario = obtenerPerfilUsuario(id_usuario)
    if not usuario or not usuario.get('activo'):
        return jsonify({'ok': False, 'mensaje': 'Usuario no encontrado o inactivo'}), 404
    return jsonify({
        'ok': True,
        'usuario': {
            'id_usuario'     : usuario['id_usuario'],
            'nombre_completo': usuario['nombre_completo'],
            'correo'         : usuario['correo'],
            'rol'            : usuario['rol'],
        }
    })


@app.route('/api/indicadores')
def api_indicadores():
    return jsonify({
        'por_app':       kpiPorAplicacion(),
        'por_prioridad': kpiPorPrioridad(),
        'por_mes':       kpiPorMes(),
    })


@app.route('/api/tickets')
def api_tickets():
    estado = request.args.get('estado', '') or None
    texto  = request.args.get('texto',  '') or None
    todos  = listarTickets()
    if estado:
        todos = [t for t in todos if t['estado'] == estado]
    if texto:
        texto = texto.lower()
        todos = [t for t in todos if texto in (t['titulo'] or '').lower()
                                  or texto in (t['nombre_aplicacion'] or '').lower()
                                  or texto in (t['nombre_solicitante'] or '').lower()]
    # Convertir fechas a string para que jsonify las serialice
    for t in todos:
        for k, v in t.items():
            if hasattr(v, 'isoformat'):
                t[k] = v.isoformat()
    return jsonify(todos)


@app.route('/api/actividad/<int:id_actividad>/estado', methods=['POST'])
def api_estado_actividad(id_actividad):
    data         = request.get_json()
    nuevo_estado = data.get('estado') if data else None
    if not nuevo_estado:
        return jsonify({'ok': False, 'mensaje': 'Estado no enviado'}), 400
    actualizarEstadoActividad(id_actividad, nuevo_estado)
    return jsonify({'ok': True, 'estado': nuevo_estado})


@app.route('/api/actividad/<int:id_actividad>/desbloquear', methods=['POST'])
def api_desbloquear_actividad(id_actividad):
    estado_retorno = desbloquearActividad(id_actividad)
    return jsonify({'ok': True, 'estado': estado_retorno})


@app.route('/api/actividad/<int:id_actividad>/eliminar', methods=['POST'])
def api_eliminar_actividad(id_actividad):
    ok = eliminarActividad(id_actividad)
    if ok:
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'mensaje': 'Solo se pueden eliminar actividades canceladas.'})

@app.route('/api/proyecto/<int:id_proyecto>/porcentaje')
def api_porcentaje_proyecto(id_proyecto):
    resumen     = resumenActividadesPorProyecto()
    fila_actual = next((r for r in resumen
                        if (r['id_proyecto'] if isinstance(r, dict) else r[0]) == id_proyecto), None)
    if fila_actual:
        if isinstance(fila_actual, dict):
            valor_raw = fila_actual.get('porcentaje_avance_real')
        else:
            valor_raw = fila_actual[3]
        pct = round(float(valor_raw)) if valor_raw is not None else 0
    else:
        pct = 0

    proyecto = obtenerProyecto(id_proyecto)
    if proyecto and proyecto.get('estado') == 'completado':
        pct = 100

    return jsonify({'porcentaje': pct})

@app.route('/api/proyecto/<int:id_proyecto>/avances-grafico')
def api_avances_grafico(id_proyecto):
    proyecto = obtenerProyecto(id_proyecto)
    avances = listarAvances(id_proyecto)
    avances_cronologicos = list(reversed(avances))
    
    fechas = []
    porcentajes_reales = []
    porcentajes_estimados = []

    if proyecto and proyecto.get('fecha_inicio') and proyecto.get('fecha_fin_plan'):
        inicio = proyecto['fecha_inicio']
        fin = proyecto['fecha_fin_plan']
        # Calculamos la duración total del proyecto en días
        duracion_total = (fin - inicio).days

        for av in avances_cronologicos:
            fecha_rep = av['fecha_reporte']
            fechas.append(fecha_rep.strftime('%d/%m'))
            porcentajes_reales.append(float(av['porcentaje_avance']))
            
            # Cálculo del Avance Estimado (Lineal / Roadmap)
            if duracion_total > 0:
                dias_transcurridos = (fecha_rep - inicio).days
                esperado = (dias_transcurridos / duracion_total) * 100
                # Evitamos que baje de 0% o pase de 100%
                esperado = max(0, min(100, esperado))
            else:
                esperado = 100
                
            porcentajes_estimados.append(round(esperado, 1))
    else:
        # Fallback de seguridad si el proyecto no tiene fechas
        fechas = [av['fecha_reporte'].strftime('%d/%m') for av in avances_cronologicos]
        porcentajes_reales = [float(av['porcentaje_avance']) for av in avances_cronologicos]
        porcentajes_estimados = [0] * len(avances_cronologicos)

    return jsonify({
        'fechas': fechas,
        'porcentajes': porcentajes_reales,
        'estimados': porcentajes_estimados
    })

@app.route('/api/avance/<int:id_avance>/eliminar', methods=['POST'])
def api_eliminar_avance(id_avance):
    try:
        # Intenta eliminar. Si tu BD tiene restricciones, saltará una excepción
        eliminarAvance(id_avance)
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error de integridad al eliminar avance: {e}")
        return jsonify({'ok': False, 'mensaje': 'No se puede eliminar por restricciones de integridad en la base de datos.'})

# ──────────────────────────────────────────────────────────────
#  APROBACION DE PROYECTOS (GERENTE)
# ──────────────────────────────────────────────────────────────

@app.route('/admin/aprobacion-proyectos')
def aprobacion_proyectos():
    try:
        proyectos = listarProyectosEnRevision()
    except Exception as e:
        print(f'Error al listar proyectos en revision: {e}')
        abort(500)
    return render_template('aprobacionProyectos.html', proyectos=proyectos)


@app.route('/api/proyecto/<int:id_proyecto>/aprobar', methods=['POST'])
def api_aprobar_proyecto(id_proyecto):
    try:
        from datetime import date
        # Obtener datos del proyecto antes de aprobar para calcular sprints
        proyecto = obtenerProyecto(id_proyecto)
        aprobarProyecto(id_proyecto)
        # Generar sprints automáticamente si no los tiene ya
        if proyecto and proyecto.get('fecha_inicio') and proyecto.get('fecha_fin_plan'):
            from proyectoAD import listarSprintsPorProyecto
            sprints_existentes = listarSprintsPorProyecto(id_proyecto)
            if not sprints_existentes:
                generarSprintsProyecto(
                    id_proyecto,
                    proyecto['fecha_inicio'],
                    proyecto['fecha_fin_plan']
                )
        return jsonify({'ok': True})
    except Exception as e:
        print(f'Error al aprobar proyecto: {e}')
        return jsonify({'ok': False, 'mensaje': 'Error al aprobar el proyecto.'})


@app.route('/api/proyecto/<int:id_proyecto>/sprints')
def api_sprints_por_proyecto(id_proyecto):
    """Devuelve los sprints de un proyecto en JSON para el combo dinámico."""
    try:
        sprints = listarSprintsPorProyecto(id_proyecto)
        resultado = [
            {
                'id_sprint': s['id_sprint'],
                'nombre':    s['nombre'],
                'estado':    s['estado'],
                'fecha_inicio': str(s['fecha_inicio']),
                'fecha_fin':    str(s['fecha_fin']),
            }
            for s in sprints
        ]
        return jsonify({'ok': True, 'sprints': resultado})
    except Exception as e:
        print(f'Error al obtener sprints: {e}')
        return jsonify({'ok': False, 'sprints': []})


@app.route('/api/proyecto/<int:id_proyecto>/rechazar', methods=['POST'])
def api_rechazar_proyecto(id_proyecto):
    try:
        rechazarProyecto(id_proyecto)
        return jsonify({'ok': True})
    except Exception as e:
        print(f'Error al rechazar proyecto: {e}')
        return jsonify({'ok': False, 'mensaje': 'Error al rechazar el proyecto.'})

# ──────────────────────────────────────────────────────────────
#  ARRANQUE
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)