"""
main.py  -  Servidor Flask  (AgroVision · bd_proyectofinal)
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from ad import (
    # DTOs
    EvaluacionCampo, Ticket, Proyecto,
    # Consultas
    obtenerLotes, obtenerPlagas, obtenerUsuarios,
    listarEvaluaciones, listarTickets, listarProyectos,
    # Inserciones
    insertarEvaluacion, insertarTicket, insertarProyecto,
    # Auth
    registrarUsuario, autenticarUsuario,
    # Resolución de tickets
    obtenerTicket, resolverTicket,
)

app = Flask(__name__)
app.secret_key = 'agrovision_secret_2024'
app.config['SESSION_PERMANENT'] = False


# ──────────────────────────────────────────────────────────────
#  DECORADOR: protege rutas, redirige al login si no hay sesion
# ──────────────────────────────────────────────────────────────

def login_requerido(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if 'usuario' not in session:
            flash('Debes iniciar sesion para acceder.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorado


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
            flash(f"Bienvenido, {datos['nombre_completo']}!", 'exito')
            return redirect(url_for('index'))
        else:
            flash(f'{mensaje}', 'error')

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
        flash('El nombre no puede estar vacio.', 'error')
        return redirect(url_for('login') + '?tab=registro')

    if password != password2:
        flash('Las contrasenas no coinciden.', 'error')
        return redirect(url_for('login') + '?tab=registro')

    if len(password) < 6:
        flash('La contrasena debe tener al menos 6 caracteres.', 'error')
        return redirect(url_for('login') + '?tab=registro')

    ok, mensaje = registrarUsuario(nombre, correo, password)
    if ok:
        flash(f'{mensaje}', 'exito')
        return redirect(url_for('login'))
    else:
        flash(f'{mensaje}', 'error')
        return redirect(url_for('login') + '?tab=registro')


# ──────────────────────────────────────────────────────────────
#  LOGOUT
# ──────────────────────────────────────────────────────────────

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Sesion cerrada correctamente.', 'exito')
    return redirect(url_for('login'))


# ──────────────────────────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_requerido
def index():
    return render_template('panelDeControl.html')


# ──────────────────────────────────────────────────────────────
#  EVALUACIONES DE CAMPO
# ──────────────────────────────────────────────────────────────

@app.route('/evaluacion/nueva')
@login_requerido
def form_evaluacion():
    lotes       = obtenerLotes()
    plagas      = obtenerPlagas()
    inspectores = obtenerUsuarios()
    return render_template('nuevaEvaluacionCampo.html',
                           lotes=lotes,
                           plagas=plagas,
                           inspectores=inspectores)


@app.route('/evaluacion/guardar', methods=['POST'])
@login_requerido
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
        if insertarEvaluacion(obj):
            flash('Evaluacion registrada correctamente.', 'exito')
        else:
            flash('No se pudo guardar la evaluacion. Revisa los datos.', 'error')
    except Exception as e:
        flash(f'Error al procesar el formulario: {e}', 'error')

    return redirect(url_for('form_evaluacion'))


@app.route('/evaluaciones')
@login_requerido
def listar_evaluaciones():
    registros = listarEvaluaciones()
    return render_template('GestionIncidencia.html', evaluaciones=registros)


# ──────────────────────────────────────────────────────────────
#  TICKETS DE SOPORTE
# ──────────────────────────────────────────────────────────────

@app.route('/ticket/nuevo')
@login_requerido
def form_ticket():
    usuarios = obtenerUsuarios()
    return render_template('NuevoTicket.html', usuarios=usuarios)


@app.route('/ticket/guardar', methods=['POST'])
@login_requerido
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
        if insertarTicket(obj):
            flash('Ticket enviado correctamente.', 'exito')
        else:
            flash('No se pudo registrar el ticket. Intenta de nuevo.', 'error')
    except Exception as e:
        flash(f'Error al procesar el formulario: {e}', 'error')

    return redirect(url_for('form_ticket'))


@app.route('/tickets')
@login_requerido
def listar_tickets():
    tickets = listarTickets()
    return render_template('GestionIncidencia.html', tickets=tickets)


@app.route('/ticket/<int:id_ticket>/resolver')
@login_requerido
def form_resolver_ticket(id_ticket):
    ticket   = obtenerTicket(id_ticket)
    if not ticket:
        flash('Ticket no encontrado.', 'error')
        return redirect(url_for('listar_tickets'))
    usuarios = obtenerUsuarios()
    return render_template('resolverTicket.html', ticket=ticket, usuarios=usuarios)


@app.route('/ticket/<int:id_ticket>/resolver', methods=['POST'])
@login_requerido
def guardar_resolucion(id_ticket):
    id_agente = request.form.get('id_agente')
    estado    = request.form.get('estado')
    notas     = request.form.get('notas_resolucion', '').strip()

    ok, mensaje = resolverTicket(id_ticket, id_agente, estado, notas)
    flash(mensaje, 'exito' if ok else 'error')
    return redirect(url_for('listar_tickets'))


# ──────────────────────────────────────────────────────────────
#  PROYECTOS DE SOFTWARE
# ──────────────────────────────────────────────────────────────

@app.route('/proyecto/nuevo')
@login_requerido
def form_proyecto():
    responsables = obtenerUsuarios()
    return render_template('nuevoProyecto.html', responsables=responsables)


@app.route('/proyecto/guardar', methods=['POST'])
@login_requerido
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
        if insertarProyecto(obj):
            flash('Proyecto creado exitosamente.', 'exito')
        else:
            flash('No se pudo crear el proyecto. Verifica los datos.', 'error')
    except Exception as e:
        flash(f'Error al procesar el formulario: {e}', 'error')

    return redirect(url_for('form_proyecto'))


@app.route('/proyectos')
@login_requerido
def listar_proyectos():
    proyectos = listarProyectos()
    return render_template('GestionIncidencia.html', proyectos=proyectos)


# ──────────────────────────────────────────────────────────────
#  ARRANQUE
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)