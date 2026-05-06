"""
main.py  –  Servidor Flask  (AgroVisión · bd_proyectofinal)
Rutas para: dashboard, evaluaciones de campo, tickets y proyectos.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from ad import (
    # DTOs
    EvaluacionCampo, Ticket, Proyecto,
    # Consultas
    obtenerLotes, obtenerPlagas, obtenerUsuarios,
    listarEvaluaciones, listarTickets, listarProyectos,
    # Inserciones
    insertarEvaluacion, insertarTicket, insertarProyecto,
)

app = Flask(__name__)
app.secret_key = 'agrovision_secret_2024'   # Necesario para flash messages


# ──────────────────────────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('panelDeControl.html')


# ──────────────────────────────────────────────────────────────
#  EVALUACIONES DE CAMPO
# ──────────────────────────────────────────────────────────────

@app.route('/evaluacion/nueva')
def form_evaluacion():
    lotes       = obtenerLotes()
    plagas      = obtenerPlagas()
    inspectores = obtenerUsuarios()          # Todos los usuarios activos
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
        if insertarEvaluacion(obj):
            flash('✅ Evaluación registrada correctamente.', 'exito')
        else:
            flash('❌ No se pudo guardar la evaluación. Revisa los datos.', 'error')
    except Exception as e:
        flash(f'❌ Error al procesar el formulario: {e}', 'error')

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
        if insertarTicket(obj):
            flash('✅ Ticket enviado correctamente.', 'exito')
        else:
            flash('❌ No se pudo registrar el ticket. Intenta de nuevo.', 'error')
    except Exception as e:
        flash(f'❌ Error al procesar el formulario: {e}', 'error')

    return redirect(url_for('form_ticket'))


@app.route('/tickets')
def listar_tickets():
    tickets = listarTickets()
    return render_template('GestionIncidencia.html', tickets=tickets)


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
        if insertarProyecto(obj):
            flash('✅ Proyecto creado exitosamente.', 'exito')
        else:
            flash('❌ No se pudo crear el proyecto. Verifica los datos.', 'error')
    except Exception as e:
        flash(f'❌ Error al procesar el formulario: {e}', 'error')

    return redirect(url_for('form_proyecto'))


@app.route('/proyectos')
def listar_proyectos():
    proyectos = listarProyectos()
    return render_template('GestionIncidencia.html', proyectos=proyectos)


# ──────────────────────────────────────────────────────────────
#  ARRANQUE
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
