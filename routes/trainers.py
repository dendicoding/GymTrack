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

    # --- FILTRI SOCIETA/SEDE ---
    societa_id = request.args.get('societa_id')
    sede_id = request.args.get('sede_id')

    if societa_id is None and sede_id is None:
        societa_id = session.get('societa_id')
        sede_id = session.get('sede_id')

    if request.args.get('societa_id') is not None:
        session['societa_id'] = societa_id
    if request.args.get('sede_id') is not None:
        session['sede_id'] = sede_id

    societa = []
    sedi = []
    if user_role == 'franchisor':
        area_managers = db.get_area_managers_by_franchisor_email(user_email)
        for manager in area_managers:
            for soc in db.get_societa_by_area_manager(manager['id']):
                societa.append({'id': soc['id'], 'nome': soc['nome']})
        if societa_id:
            sedi = [{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(societa_id)]
        else:
            for manager in area_managers:
                for soc in db.get_societa_by_area_manager(manager['id']):
                    sedi.extend([{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(soc['id'])])
    elif user_role == 'area manager':
        societa_list = db.get_societa_by_area_manager_email(user_email)
        for soc in societa_list:
            societa.append({'id': soc['id'], 'nome': soc['nome']})
        if societa_id:
            sedi = [{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(societa_id)]
        else:
            for soc in societa_list:
                sedi.extend([{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(soc['id'])])
    elif user_role == 'societa':
        societa_obj = db.get_societa_by_email(user_email)
        if societa_obj:
            societa.append({'id': societa_obj['id'], 'nome': societa_obj['nome']})
            sedi = [{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(societa_obj['id'])]
    elif user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sedi = [{'id': sede['id'], 'nome': sede['nome']}]
    elif user_role == 'trainer':
        sede = db.get_sede_by_trainer_email(user_email)
        if sede:
            sedi = [{'id': sede['id'], 'nome': sede['nome']}]

    # Determina i sede_ids da usare per il filtro
    if sede_id:
        sede_ids = [int(sede_id)]
    elif societa_id:
        sedi_societa = db.get_sedi_by_societa(societa_id)
        sede_ids = [sede['id'] for sede in sedi_societa]
    else:
        sede_ids = [sede['id'] for sede in sedi]

    trainers = db.get_trainers_with_status(sede_ids)
    return render_template(
        'trainer/view_trainers.html',
        trainers=trainers,
        societa=societa,
        sedi=sedi,
        selected_societa_id=str(societa_id) if societa_id else '',
        selected_sede_id=str(sede_id) if sede_id else ''
    )

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
    for r in resoconti:
    # Assumendo che r['data'] sia una stringa tipo '2025-07-23'
        r['mese'] = r['data'].strftime('%Y-%m')  # 'YYYY-MM'
    return render_template('trainer/resoconti.html', resoconti=resoconti)


@trainers_bp.route('/trainer/attendance', methods=['GET'])
@login_required
def trainer_attendance():
    if session.get('user_role') != 'trainer':
        abort(403)
    trainer_id = session.get('user_id')
    is_present = db.is_trainer_present(trainer_id)
    session['is_present'] = is_present  # <-- aggiorna la sessione
    return render_template('trainer_attendance.html', is_present=is_present)

@trainers_bp.route('/trainer/entrata', methods=['POST'])
@login_required
def trainer_entrata():
    if session.get('user_role') != 'trainer':
        abort(403)
    trainer_id = session.get('user_id')
    db.log_event(trainer_id, session.get('user_email'), 'entra', 'Trainer entrato')
    flash('Entrata registrata con successo!', 'success')
    return redirect(url_for('index'))

@trainers_bp.route('/trainer/uscita', methods=['POST'])
@login_required
def trainer_uscita():
    if session.get('user_role') != 'trainer':
        abort(403)
    trainer_id = session.get('user_id')
    db.log_event(trainer_id, session.get('user_email'), 'esci', 'Trainer uscito')
    flash('Uscita registrata con successo!', 'success')
    return redirect(url_for('index'))

@trainers_bp.route('/trainer-status')
@login_required
def trainer_status():
    user_role = session.get('user_role')
    user_email = session.get('user_email')

    # --- FILTRI SOCIETA/SEDE ---
    societa_id = request.args.get('societa_id')
    sede_id = request.args.get('sede_id')

    if societa_id is None and sede_id is None:
        societa_id = session.get('societa_id')
        sede_id = session.get('sede_id')

    if request.args.get('societa_id') is not None:
        session['societa_id'] = societa_id
    if request.args.get('sede_id') is not None:
        session['sede_id'] = sede_id

    societa = []
    sedi = []
    if user_role == 'franchisor':
        area_managers = db.get_area_managers_by_franchisor_email(user_email)
        for manager in area_managers:
            for soc in db.get_societa_by_area_manager(manager['id']):
                societa.append({'id': soc['id'], 'nome': soc['nome']})
        if societa_id:
            sedi = [{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(societa_id)]
        else:
            for manager in area_managers:
                for soc in db.get_societa_by_area_manager(manager['id']):
                    sedi.extend([{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(soc['id'])])
    elif user_role == 'area manager':
        societa_list = db.get_societa_by_area_manager_email(user_email)
        for soc in societa_list:
            societa.append({'id': soc['id'], 'nome': soc['nome']})
        if societa_id:
            sedi = [{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(societa_id)]
        else:
            for soc in societa_list:
                sedi.extend([{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(soc['id'])])
    elif user_role == 'societa':
        societa_obj = db.get_societa_by_email(user_email)
        if societa_obj:
            societa.append({'id': societa_obj['id'], 'nome': societa_obj['nome']})
            sedi = [{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(societa_obj['id'])]
    elif user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sedi = [{'id': sede['id'], 'nome': sede['nome']}]
    elif user_role == 'trainer':
        sede = db.get_sede_by_trainer_email(user_email)
        if sede:
            sedi = [{'id': sede['id'], 'nome': sede['nome']}]

    # Determina i sede_ids da usare per il filtro
    if sede_id:
        sede_ids = [int(sede_id)]
    elif societa_id:
        sedi_societa = db.get_sedi_by_societa(societa_id)
        sede_ids = [sede['id'] for sede in sedi_societa]
    else:
        sede_ids = [sede['id'] for sede in sedi]

    # Fetch trainers and their status
    trainers = db.get_trainers_with_status(sede_ids)
    return render_template(
        'trainer_status.html',
        trainers=trainers,
        societa=societa,
        sedi=sedi,
        selected_societa_id=str(societa_id) if societa_id else '',
        selected_sede_id=str(sede_id) if sede_id else ''
    )

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
    
    # Passa la variabile date al template
    return render_template('trainer/resoconto.html', date=date)