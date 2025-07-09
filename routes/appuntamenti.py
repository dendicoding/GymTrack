from collections import defaultdict
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date, datetime, timedelta
from utils.auth import login_required
# ... altri import ...

appuntamenti_bp = Blueprint('appuntamenti', __name__)

@appuntamenti_bp.route('/trainer/appointment/new', methods=['GET', 'POST'])
@login_required
def add_appointment():
    

    # Step 1: Ottieni il ruolo e l'email dell'utente loggato
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    user_id = session.get('user_id')
    
    print(f"Ruolo ed email {user_role}: {user_email}")

    # Step 2: Determina le sedi sotto la gerarchia dell'utente
    societa = []
    sedi = []
    if user_role == 'trainer':
        sede = db.get_sede_by_trainer_email(user_email)
        if sede:
            sedi.append(sede)
    elif user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sedi.append(sede)
    elif user_role == 'area manager':
        societa = db.get_societa_by_area_manager_email(user_email)
        print(f"Società sotto l'area manager {user_email}: {societa}")

        for company in societa:
            sedi.extend(db.get_sedi_by_societa(company['id']))
    elif user_role == 'societa':
        societa = db.get_societa_by_email(user_email)
        if societa:
            sedi = db.get_sedi_by_societa(societa['id'])
            #sedi.extend([sede['id'] for sede in sedi])
    elif user_role == 'franchisor':
        area_managers = db.get_area_managers_by_franchisor_email(user_email)
        for manager in area_managers:
            societa = db.get_societa_by_area_manager(manager['id'])
            
            for company in societa:
                sedi.extend(db.get_sedi_by_societa(company['id']))

    clienti = db.get_all_clienti([s['id'] for s in sedi if 'id' in s])

    # Precompila la data e ora se fornita nella query string
    prefilled_date_time = request.args.get('date_time', '')
    prefilled_end_date_time = request.args.get('end_date_time', '')

    # Rimuovi il suffisso `.000Z` e formatta correttamente i valori
    if prefilled_date_time:
        prefilled_date_time = prefilled_date_time.split('.')[0]  # Rimuove `.000Z`
        prefilled_date_time = prefilled_date_time.replace('Z', '')  # Rimuove `Z`
    if prefilled_end_date_time:
        prefilled_end_date_time = prefilled_end_date_time.split('.')[0]  # Rimuove `.000Z`
        prefilled_end_date_time = prefilled_end_date_time.replace('Z', '')  # Rimuove `Z`

    if request.method == 'POST':
        title = request.form['title']
        notes = request.form['notes']
        date_time = datetime.strptime(request.form['date_time'], '%Y-%m-%dT%H:%M')
        end_date_time = datetime.strptime(request.form['end_date_time'], '%Y-%m-%dT%H:%M')
        appointment_type = request.form['appointment_type']
        status = request.form['status']
        client_id = request.form['client_id']
        is_trial = 'is_trial' in request.form
        is_recovery = 'is_recovery' in request.form
        is_lesson_zero = 'is_lesson_zero' in request.form
        package_id = request.form.get('package_id')  # Pacchetto selezionato

        # Logica per appuntamenti ricorrenti
        is_recurring = 'is_recurring' in request.form
        duration = int(request.form['duration']) if 'duration' in request.form and request.form['duration'] else None

        if is_recurring and duration:
            # Calcola il giorno della settimana
            day_of_week = date_time.weekday()  # 0 = Lunedì, 6 = Domenica
            current_date = date_time
            while current_date <= end_date_time:
                if current_date.weekday() == day_of_week:
                    recurring_end_time = current_date + timedelta(minutes=duration)
                    db.add_appointment(
                        user_id, client_id, title, notes, current_date, recurring_end_time,
                        appointment_type, status, is_trial, is_recovery, is_lesson_zero, package_id
                    )
                current_date += timedelta(days=1)
            flash('Appuntamenti ripetuti creati con successo!', 'success')
        else:
            # Salva l'appuntamento singolo nel database
            appointment_id = db.add_appointment(
                user_id, client_id, title, notes, date_time, end_date_time,
                appointment_type, status, is_trial, is_recovery, is_lesson_zero, package_id
            )

            if appointment_id:
                flash('Appuntamento aggiunto con successo!', 'success')
                return redirect(url_for('appuntamenti.trainer_calendar'))
            else:
                flash('Errore durante l\'aggiunta dell\'appuntamento.', 'error')

    return render_template(
        'trainer/add_appointment.html',
        clienti=clienti,
        prefilled_date_time=prefilled_date_time,
        prefilled_end_date_time=prefilled_end_date_time
    )

@appuntamenti_bp.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    if session.get('user_role') != 'trainer':
        abort(403)
    
    appointment = db.get_appointment_by_id(appointment_id)
    
    if not appointment:
        flash('Appuntamento non trovato', 'danger')
        return redirect(url_for('trainer_calendar'))
    
    if appointment['created_by'] != session.get('user_id'):
        abort(403)
    
    if request.method == 'POST':
        # Raccolta dei dati dal form
        client_id = request.form.get('client_id')
        date_time = request.form.get('date_time')
        end_date_time = request.form.get('end_date_time')
        appointment_type = request.form.get('type')
        status = request.form.get('status')
        notes = request.form.get('notes')
        
        
        # Aggiornamento dell'appuntamento
        db.update_appointment(
            appointment_id=appointment_id,
            title=request.form.get('title'),
            client_id=request.form.get('client_id'),
            notes=request.form.get('notes'),
            date_time=request.form.get('date_time'),
            end_date_time=request.form.get('end_date_time'),
            appointment_type=request.form.get('type'),
            status=request.form.get('status'),
            is_trial=bool(request.form.get('is_trial')),
            is_recovery=bool(request.form.get('is_recovery')),
            is_lesson_zero=bool(request.form.get('is_lesson_zero'))
        )
        
        flash('Appuntamento aggiornato con successo', 'success')
        return redirect(url_for('appuntamenti.trainer_calendar'))
    
    # Per il metodo GET, mostra il form di modifica
    clients = db.get_all_clienti()
    return render_template(
        'trainer/edit_appointment.html',
        appointment=appointment,
        clients=clients
    )

@appuntamenti_bp.route('/delete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    print("CSRF Token ricevuto:", request.headers.get('X-CSRFToken'))

    if session.get('user_role') != 'trainer':
        flash('Non hai i permessi per eliminare questo appuntamento.', 'error')
        return redirect(url_for('appuntamenti.trainer_calendar'))

    appointment = db.get_appointment_by_id(appointment_id)
    print(appointment)
    if not appointment:
        flash('Appuntamento non trovato.', 'error')
        return redirect(url_for('appuntamenti.trainer_calendar'))



    if db.delete_appointment(appointment_id):
        flash('Appuntamento eliminato con successo.', 'success')
    else:
        flash('Errore durante l\'eliminazione dell\'appuntamento.', 'error')

    return redirect(url_for('appuntamenti.trainer_calendar'))


@appuntamenti_bp.route('/trainer/calendar', methods=['GET'])
@login_required
def trainer_calendar():
    # Step 1: Ottieni il ruolo e l'email dell'utente loggato
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    print(f"Ruolo ed email {user_role}: {user_email}")

    # Step 2: Determina le sedi sotto la gerarchia dell'utente
    societa = []
    sedi = []
    if user_role == 'trainer':
        sede = db.get_sede_by_trainer_email(user_email)
        if sede:
            sedi.append(sede)
    elif user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sedi.append(sede)
    elif user_role == 'area manager':
        societa = db.get_societa_by_area_manager_email(user_email)
        print(f"Società sotto l'area manager {user_email}: {societa}")

        for company in societa:
            sedi.extend(db.get_sedi_by_societa(company['id']))
    elif user_role == 'societa':
        societa = db.get_societa_by_email(user_email)
        if societa:
            sedi = db.get_sedi_by_societa(societa['id'])
            #sedi.extend([sede['id'] for sede in sedi])
    elif user_role == 'franchisor':
        area_managers = db.get_area_managers_by_franchisor_email(user_email)
        for manager in area_managers:
            societa = db.get_societa_by_area_manager(manager['id'])
            
            for company in societa:
                sedi.extend(db.get_sedi_by_societa(company['id']))

    # Step 3: Filtra gli eventi in base alla sede selezionata
    selected_societa_id = request.args.get('societa_id', type=int)

    selected_sede_id = request.args.get('sede_id', type=int)
    user_ids = []
    
    if selected_societa_id:
        sedi = db.get_sedi_by_societa(selected_societa_id)

    if selected_sede_id:
        trainers_in_sede = db.get_trainers_by_sede(selected_sede_id)
        user_ids = []
        for trainer in trainers_in_sede:
            user = db.get_user_by_email(trainer['email'])
            if user:
                user_ids.append(user['id'])
    else:
        for sede in sedi:
            trainers_in_sede = db.get_trainers_by_sede(sede['id'])
            for trainer in trainers_in_sede:
                user = db.get_user_by_email(trainer['email'])
                if user:
                    user_ids.append(user['id'])

    # Step 4: Ottieni gli appuntamenti per gli utenti trovati
    print(f"User IDs per gli appuntamenti: {user_ids}")
    start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    print(f"Data di inizio per gli appuntamenti: {start_date}")
    appointments = db.get_appointments_by_users(user_ids, start_date)
    if appointments: print(f"Appuntamenti trovati: {appointments}") 
    else: print("Nessun appuntamento trovato.")

    # Raggruppa gli appuntamenti per data
    grouped_appointments = defaultdict(list)
    for appointment in appointments:
        appointment_date = appointment['date_time'].date()
        grouped_appointments[appointment_date].append(appointment)

    if selected_sede_id:
        clienti = db.get_all_clienti([selected_sede_id])
    else:
        clienti = db.get_all_clienti([s['id'] for s in sedi if 'id' in s])
    selected_client_id = request.args.get('client_id', type=int)


    # FILTRO per client_id
    if selected_client_id:
        for day in list(grouped_appointments.keys()):
            grouped_appointments[day] = [
                app for app in grouped_appointments[day]
                if str(app.get('client_id')) == str(selected_client_id)
            ]
        # Rimuovi giorni senza appuntamenti
        grouped_appointments = {k: v for k, v in grouped_appointments.items() if v}

    
    # Step 5: Renderizza il template del calendario
    return render_template(
        'trainer/calendar.html',
        current_date=datetime.strptime(start_date, '%Y-%m-%d'),
        timedelta=timedelta,
        date=date,
        clienti=clienti,
        selected_client_id=selected_client_id,
        grouped_appointments=grouped_appointments,
        sedi=sedi,
        societa=societa,
        selected_societa_id=selected_societa_id,
        selected_sede_id=selected_sede_id
    )

@appuntamenti_bp.route('/mark_appointment_completed/<int:appointment_id>', methods=['POST'])
@login_required
def mark_appointment_completed(appointment_id):
    # Ottieni i dettagli dell'appuntamento
    appointment = db.get_appointment_by_id(appointment_id)
    if not appointment:
        return jsonify({'success': False, 'message': 'Appuntamento non trovato'}), 404

    # Verifica che il tipo di appuntamento sia un allenamento
    if appointment['appointment_type'] not in ['Allenamento Funzionale', 'Allenamento EMS']:
        return jsonify({'success': False, 'message': 'Solo gli allenamenti possono essere completati'}), 400

    # Verifica che il pacchetto sia associato all'appuntamento
    if 'package_id' not in appointment or not appointment['package_id']:
        return jsonify({'success': False, 'message': 'Nessun pacchetto associato a questo appuntamento'}), 400

    # Registra la lezione
    # Verifica se l'abbonamento è ancora valido
    oggi = datetime.now().date()
    
    
    if request.method == 'POST':
        note = ''
        if request.is_json:
            note = request.json.get('note', '')
        else:
            note = request.form.get('note', '')
        user_id = session.get('user_id')
        
        # Registra la lezione
        if db.add_lezione(appointment['package_id'], oggi, note, user_id):
            db.log_event(session.get('user_id'), session.get('user_email'), 'Registrata lezione', f'Abbonamento ID: {appointment["package_id"]}')
            flash('Lezione registrata con successo', 'success')
            return jsonify({'success': True, 'message': 'Lezione registrata con successo'})
        else:
            flash('Errore durante la registrazione della lezione', 'error')

    return jsonify({'success': True, 'message': 'Lezione registrata con successo'}), 200