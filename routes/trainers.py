from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date
from utils.auth import login_required
# ... altri import ...

trainers_bp = Blueprint('trainers', __name__)

@trainers_bp.route('/trainers', methods=['GET'])
@login_required
def view_trainers():
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    
    # Fetch sede_ids based on user role
    sede_ids = []
    if user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sede_ids.append(sede['id'])
    elif user_role == 'societa':
        societa = db.get_societa_by_email(user_email)
        if societa:
            sedi = db.get_sedi_by_societa(societa['id'])
            sede_ids.extend([sede['id'] for sede in sedi])
    elif user_role == 'area manager':
        societa = db.get_societa_by_area_manager_email(user_email)
        for company in societa:
            sedi = db.get_sedi_by_societa(company['id'])
            sede_ids.extend([sede['id'] for sede in sedi])
    elif user_role == 'franchisor':
        area_managers = db.get_area_managers_by_franchisor_email(user_email)
        for manager in area_managers:
            societa = db.get_societa_by_area_manager(manager['id'])
            for company in societa:
                sedi = db.get_sedi_by_societa(company['id'])
                sede_ids.extend([sede['id'] for sede in sedi])

    sede_ids = [sede_id for sede_id in sede_ids if sede_id is not None]
    trainers = db.get_trainers_with_status(sede_ids)
    return render_template('trainer/view_trainers.html', trainers=trainers)

@trainers_bp.route('/trainer/resoconto/<int:resoconto_id>', methods=['GET'])
@login_required
def view_resoconto(resoconto_id):
    resoconto = db.get_resoconto(resoconto_id)
    if not resoconto:
        flash('Resoconto non trovato', 'error')
        return redirect(url_for('view_trainers'))
    return render_template('trainer/view_resoconto.html', resoconto=resoconto)

@trainers_bp.route('/trainer/<int:trainer_id>/resoconto')
@login_required
def trainer_resoconti(trainer_id):
    resoconti = db.get_resoconti_by_trainer(trainer_id)
    return render_template('trainer/resoconti.html', resoconti=resoconti)


@trainers_bp.route('/trainer/attendance', methods=['GET'])
@login_required
def trainer_attendance():
    if session.get('user_role') != 'trainer':
        abort(403)
    trainer_id = session.get('user_id')
    
    is_present = db.is_trainer_present(trainer_id)
    print(is_present)
    return render_template('trainer_attendance.html', is_present=is_present)

@trainers_bp.route('/trainer/entrata', methods=['POST'])
@login_required
def trainer_entrata():
    if session.get('user_role') != 'trainer':
        abort(403)
    trainer_id = session.get('user_id')
    db.log_event(trainer_id, session.get('user_email'), 'entra', 'Trainer entrato')
    flash('Entrata registrata con successo!', 'success')
    return redirect(url_for('trainers.trainer_attendance'))

@trainers_bp.route('/trainer/uscita', methods=['POST'])
@login_required
def trainer_uscita():
    if session.get('user_role') != 'trainer':
        abort(403)
    trainer_id = session.get('user_id')
    db.log_event(trainer_id, session.get('user_email'), 'esci', 'Trainer uscito')
    flash('Uscita registrata con successo!', 'success')
    return redirect(url_for('trainers.trainer_attendance'))

@trainers_bp.route('/trainer-status')
@login_required
def trainer_status():
    user_role = session.get('user_role')
    user_email = session.get('user_email')

    # Fetch sede_ids based on user role
    sede_ids = []
    if user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sede_ids.append(sede['id'])
    elif user_role == 'trainer':
        sede = db.get_sede_by_trainer_email(user_email)
        if sede:
            sede_ids.append(sede['id'])
    elif user_role == 'societa':
        societa = db.get_societa_by_email(user_email)
        if societa:
            sedi = db.get_sedi_by_societa(societa['id'])
            sede_ids.extend([sede['id'] for sede in sedi])
    elif user_role == 'area manager':
        societa = db.get_societa_by_area_manager_email(user_email)
        for company in societa:
            sedi = db.get_sedi_by_societa(company['id'])
            sede_ids.extend([sede['id'] for sede in sedi])
    elif user_role == 'franchisor':
        area_managers = db.get_area_managers_by_franchisor_email(user_email)
        for manager in area_managers:
            societa = db.get_societa_by_area_manager(manager['id'])
            for company in societa:
                sedi = db.get_sedi_by_societa(company['id'])
                sede_ids.extend([sede['id'] for sede in sedi])

    # Ensure only valid sede_ids are used
    sede_ids = [sede_id for sede_id in sede_ids if sede_id is not None]

    # Fetch trainers and their status
    trainers = db.get_trainers_with_status(sede_ids)
    print(trainers)
    return render_template('trainer_status.html', trainers=trainers)

@trainers_bp.route('/trainer/resoconto', methods=['GET', 'POST'])
@login_required
def trainer_resoconto():
    if session.get('user_role') != 'trainer':
        flash('Accesso negato. Solo i trainer possono accedere a questa pagina.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.form['data']
        ore_lavoro = request.form['ore_lavoro']
        ore_buca = request.form['ore_buca']
        attivita_buca = request.form['attivita_buca']
        user_email = session.get('user_email')
        trainer = db.get_trainer_by_email(user_email)
        if not trainer:
            flash('Trainer non trovato.', 'error')
            return redirect(url_for('index'))
        trainer_id = trainer['id']
        
        db.add_resoconto(trainer_id, data, ore_lavoro, ore_buca, attivita_buca)
        flash('Resoconto dichiarato con successo!', 'success')
        return redirect(url_for('trainers.trainer_resoconto'))
    
    return render_template('trainer/resoconto.html')