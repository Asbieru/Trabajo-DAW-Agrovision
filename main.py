"""
main.py  -  Servidor Flask  (AgroVision · bd_proyectofinal)
"""

from flask import Flask, render_template, request, redirect, url_for, session
from ticketDB import (Ticket,listarTickets,insertarTicket,obtenerTicket, resolverTicket,resumenTickets,ticketsPorAplicacion,ticketsPorPrioridad)
from proyectoDB import (Proyecto, listarProyectos, insertarProyecto)
from ad import (
    # DTOs
    EvaluacionCampo,
    # Consultas
    obtenerLotes, obtenerPlagas, obtenerUsuarios,
    listarEvaluaciones,
    # Inserciones
    insertarEvaluacion,
    # KPIs Indicadores
    kpiTicketsPorAgente, kpiTicketsPorMes,kpiAvanceSprintActual,
    # Auth
    registrarUsuario, autenticarUsuario,    
)

app = Flask(__name__)
app.secret_key = 'agrovision_secret_2024'
app.config['SESSION_PERMANENT'] = False

# ──────────────────────────────────────────────────────────────
#  RUTA RAIZ: redirige siempre al login o al dashboard
#  Esta es la que se abre cuando entras a http://127.0.0.1:5000/
# ──────────────────────────────────────────────────────────────

@app.route('/')
def raiz():
    if 'usuario' not in session:
        return redirect(url_for('login'))       # sin sesion -> login
    return redirect(url_for('index'))           # con sesion -> dashboard


# ──────────────────────────────────────────────────────────────
#  LOGIN
# ──────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya tiene sesion activa, va directo al dashboard
    if 'usuario' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        correo   = request.form.get('correo', '').strip()
        password = request.form.get('password', '')

        ok, mensaje, datos = autenticarUsuario(correo, password)
        if ok:
            session['usuario'] = datos
            return redirect(url_for('index'))

    return render_template('login.html')


# ──────────────────────────────────────────────────────────────
#  REGISTRO
# ──────────────────────────────────────────────────────────────

@app.route('/registro', methods=['POST'])
def registro():
    nombre    = request.form.get('nombre_completo', '').strip()
    correo    = request.form.get('correo', '').strip()
    password  = request.form.get('password', '')
    password2 = request.form.get('password2', '')

    if not nombre:
        return redirect(url_for('login') + '?tab=registro')

    if password != password2:
        return redirect(url_for('login') + '?tab=registro')

    if len(password) < 6:
        return redirect(url_for('login') + '?tab=registro')

    ok, mensaje = registrarUsuario(nombre, correo, password)
    if ok:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login') + '?tab=registro')


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
#  EVALUACIONES DE CAMPO
# ──────────────────────────────────────────────────────────────

@app.route('/evaluacion/nueva')
def form_evaluacion():
    lotes       = obtenerLotes()
    plagas      = obtenerPlagas()
    inspectores = obtenerUsuarios()
    return render_template('nuevaEvaluacionCampo.html',
                           lotes=lotes,
                           plagas=plagas,
                           inspectores=inspectores)


@app.route('/evaluacion/guardar', methods=['POST'])
def guardar_evaluacion():
    try:
        obj = EvaluacionCampo(
            id_lote           = request.form['id_lote'],
            id_plaga          = request.form['id_plaga'],
            id_inspector      = request.form['id_inspector'],
            fecha_evaluacion  = request.form['fecha_evaluacion'],
            hora_evaluacion   = request.form.get('hora_evaluacion', ''),
            plantas_evaluadas = request.form['plantas_evaluadas'],
            plantas_afectadas = request.form['plantas_afectadas'],
            nivel_incidencia  = request.form['nivel_incidencia'],
            foto_url          = request.form.get('foto_url', ''),
            observaciones     = request.form.get('observaciones', ''),
        )
        insertarEvaluacion(obj)
    except Exception as e:
        print(f'Error al procesar el formulario: {e}')

    return redirect(url_for('form_evaluacion'))


@app.route('/evaluaciones')
def listar_evaluaciones():
    registros = listarEvaluaciones()
    return render_template('GestionIncidencia.html', evaluaciones=registros)


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



# ══════════════════════════════════════════════════════════════
#  INDICADORES DE SOPORTE
# ══════════════════════════════════════════════════════════════

@app.route('/indicadores')
def indicadores_soporte():
    resumen       = resumenTickets()
    por_app       = ticketsPorAplicacion()
    por_prioridad = ticketsPorPrioridad()
    por_agente    = kpiTicketsPorAgente()
    por_mes       = kpiTicketsPorMes()
    sprint_activo = kpiAvanceSprintActual()
    return render_template('indicadores.html',
                           resumen=resumen,
                           por_app=por_app,
                           por_prioridad=por_prioridad,
                           por_agente=por_agente,
                           por_mes=por_mes,
                           sprint_activo=sprint_activo)


# ──────────────────────────────────────────────────────────────
#  ARRANQUE
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)