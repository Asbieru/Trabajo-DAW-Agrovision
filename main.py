"""
main.py  -  Servidor Flask  (AgroVision · bd_proyectofinal)
Sin uso de session ni import json.
"""

from flask import Flask, render_template, request, redirect, url_for, abort, jsonify

from usuarioAD import (autenticarUsuario, buscarUsuarioPorCorreo, obtenerUsuarios,
                       listarUsuariosCompleto, obtenerPerfilUsuario,
                       estadisticasUsuario, historialParticipacionUsuario,
                       resumenHistorialUsuario)
from ticketAD import (Ticket, listarTickets, insertarTicket, obtenerTicket,
                      resolverTicket, guardarCalificacionTicket)
from actividadAD import (Actividad, listarActividades, insertarActividad,
                         actualizarEstadoActividad, eliminarActividad,
                         listarTodosSprints,
                         listarAsignadosPorProyecto, resumenActividadesPorProyecto,
                         proximoCodigo)
from proyectoAD import (Proyecto, listarProyectos, insertarProyecto,
                        obtenerProyecto, actualizarProyecto,
                        listarAvances, insertarAvance, eliminarAvance)
from indicadoresAD import (resumenKPI, kpiPorAplicacion, kpiPorPrioridad,
                            kpiPorAgente, kpiPorMes, kpiSprintsActivos,
                            kpiSatisfaccion, comentariosCalificacionesRecientes,
                            kpiProyectosPorEstado, kpiVelocityPorSprint,
                            kpiCargaPorProgramador,
                            kpiProyectosFiltrados, obtenerResponsablesProyecto)                         
from reportesAD import (reporteResumen, reporteTicketsPorApp, reporteTicketsPorTipo,
                         reporteStoryPointsPorProgramador, reporteCarryoverPorProgramador,
                         reporteTicketsFiltrados, obtenerAplicaciones,
                         reporteProyectosPorEstado, reporteProyectosEnRiesgo,
                         reporteRendimientoPorSprint,
                         reporteProyectosFiltrados, obtenerResponsables)                        

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
    except KeyError:
        abort(400)
    except Exception as e:
        print(f'Error al guardar ticket: {e}')
        abort(500)
    return redirect(url_for('form_ticket'))


@app.route('/tickets')
def listar_tickets():
    tickets = listarTickets()
    mensaje = None
    tipo = None
    estado_msg = request.args.get('calificacion', '').strip()

    if estado_msg == 'ok':
        mensaje = 'Gracias. Tu calificación fue registrada correctamente.'
        tipo = 'exito'
    elif estado_msg == 'bloqueada':
        mensaje = 'Este ticket ya fue calificado y no se puede editar la calificación.'
        tipo = 'error'

    return render_template('gestionTicket.html', tickets=tickets, mensaje=mensaje, tipo=tipo)


@app.route('/tickets/resolver')
def resolver_tickets():
    todos = listarTickets()
    pendientes = [t for t in todos if t['estado'] in ('abierto', 'en_progreso')]
    return render_template('resolverTicket.html', tickets_pendientes=pendientes)


@app.route('/ticket/<int:id_ticket>/resolver')
def form_resolver_ticket(id_ticket):
    ticket   = obtenerTicket(id_ticket)
    if not ticket:
        abort(404)
    usuarios = obtenerUsuarios()
    return render_template('resolverTicket.html', ticket=ticket, usuarios=usuarios)


@app.route('/ticket/<int:id_ticket>/resolver', methods=['POST'])
def guardar_resolucion(id_ticket):
    id_agente = request.form.get('id_agente')
    estado    = request.form.get('estado')
    notas     = request.form.get('notas_resolucion', '').strip()
    resolverTicket(id_ticket, id_agente, estado, notas)
    return redirect(url_for('listar_tickets'))


@app.route('/ticket/<int:id_ticket>/calificar', methods=['GET', 'POST'])
def calificar_ticket(id_ticket):
    ticket = obtenerTicket(id_ticket)
    if not ticket:
        abort(404)

    if ticket['estado'] not in ('resuelto', 'cerrado', 'base_proyecto'):
        abort(400)

    if request.method == 'GET' and ticket.get('calificacion_estrellas') is not None:
        return redirect(url_for('listar_tickets', calificacion='bloqueada'))

    mensaje = None
    tipo = None

    if request.method == 'POST':
        if ticket.get('calificacion_estrellas') is not None:
            return redirect(url_for('listar_tickets', calificacion='bloqueada'))

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
            if ticket.get('estado') == 'resuelto':
                resolverTicket(id_ticket, ticket.get('id_agente'), 'cerrado', ticket.get('notas_resolucion') or '')
            return redirect(url_for('listar_tickets', calificacion='ok'))

    return render_template('calificarTicket.html',
                           ticket=ticket,
                           mensaje=mensaje,
                           tipo=tipo)


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
            estado           = 'planificado',
            fecha_inicio     = date.today().strftime('%Y-%m-%d'),
            fecha_fin_plan   = request.form['fecha_fin_plan'],
            descripcion      = request.form['descripcion'],
        )
        insertarProyecto(obj)
    except KeyError:
        abort(400)
    except Exception as e:
        print(f'Error al guardar proyecto: {e}')
        abort(500)
    return redirect(url_for('form_proyecto'))


@app.route('/proyectos')
def listar_proyectos():
    proyectos = listarProyectos()
    return render_template('listaProyectos.html', proyectos=proyectos)


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
    estado_proy    = limpiar(request.args.get('estado_proy', ''))
    id_responsable = limpiar(request.args.get('id_responsable', ''))
 
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
    proyectos_filtrados = kpiProyectosFiltrados(estado_proy, id_responsable)
    responsables      = obtenerResponsablesProyecto()
 
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
                           proyectos_filtrados=proyectos_filtrados,
                           responsables=responsables,
                           estado_proy=estado_proy       or '',
                           id_responsable=id_responsable or '')


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
    fecha_inicio   = limpiar(request.args.get('fecha_inicio', ''))
    fecha_fin      = limpiar(request.args.get('fecha_fin', ''))
    aplicacion     = limpiar(request.args.get('aplicacion', ''))
    estado         = limpiar(request.args.get('estado', ''))
    prioridad      = limpiar(request.args.get('prioridad', ''))
    estado_proy    = limpiar(request.args.get('estado_proy', ''))
    id_responsable = limpiar(request.args.get('id_responsable', ''))
 
    resumen            = reporteResumen()
    tickets_app        = reporteTicketsPorApp()
    tickets_tipo       = reporteTicketsPorTipo()
    story_points       = reporteStoryPointsPorProgramador()
    carryover          = reporteCarryoverPorProgramador()
    aplicaciones       = obtenerAplicaciones()
    tickets_filtrados  = reporteTicketsFiltrados(fecha_inicio, fecha_fin,
                                                  aplicacion, estado, prioridad)
    proyectos_estado   = reporteProyectosPorEstado()
    proyectos_riesgo   = reporteProyectosEnRiesgo()
    rendimiento_sprint = reporteRendimientoPorSprint()
    proyectos_filtrados = reporteProyectosFiltrados(estado_proy, id_responsable)
    responsables       = obtenerResponsables()
 
    return render_template('reportes.html',
                           resumen=resumen,
                           tickets_app=tickets_app,
                           tickets_tipo=tickets_tipo,
                           story_points=story_points,
                           carryover=carryover,
                           aplicaciones=aplicaciones,
                           tickets_filtrados=tickets_filtrados,
                           fecha_inicio=fecha_inicio   or '',
                           fecha_fin=fecha_fin         or '',
                           aplicacion=aplicacion       or '',
                           estado=estado               or '',
                           prioridad=prioridad         or '',
                           proyectos_estado=proyectos_estado,
                           proyectos_riesgo=proyectos_riesgo,
                           rendimiento_sprint=rendimiento_sprint,
                           proyectos_filtrados=proyectos_filtrados,
                           responsables=responsables,
                           estado_proy=estado_proy     or '',
                           id_responsable=id_responsable or '')


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
            estado       = 'backlog',
            story_points = request.form.get('story_points') or 0,
        )
        insertarActividad(obj)
    except KeyError:
        abort(400)
    except Exception as e:
        print(f'Error al guardar actividad: {e}')
        abort(500)
    return redirect(url_for('gestion_proyecto', id_proyecto=id_proyecto))


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
    usuarios = listarUsuariosCompleto()
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
                                  or texto in (t['aplicacion'] or '').lower()
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

@app.route('/api/actividad/<int:id_actividad>/eliminar', methods=['POST'])
def api_eliminar_actividad(id_actividad):
    eliminarActividad(id_actividad)
    return jsonify({'ok': True})

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
    avances = listarAvances(id_proyecto)
    avances_cronologicos = list(reversed(avances))
    fechas      = [av['fecha_reporte'].strftime('%d/%m') for av in avances_cronologicos]
    porcentajes = [float(av['porcentaje_avance']) for av in avances_cronologicos]
    return jsonify({'fechas': fechas, 'porcentajes': porcentajes})

# ──────────────────────────────────────────────────────────────
#  ARRANQUE
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)