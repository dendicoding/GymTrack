from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date, datetime
from utils.auth import login_required
# ... altri import ...

clienti_bp = Blueprint('clienti', __name__)

@clienti_bp.route('/clienti')
def lista_clienti():
    tipo = request.args.get('tipo', 'tutti')
    user_role = session.get('user_role')
    user_email = session.get('user_email')


    # Directly fetch the sede_id for the logged-in user if the role is 'sede'
    sede_ids = []
    if user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sede_ids.append(sede['id'])
    elif user_role == 'trainer':
        # Fetch the sede associated with the trainer
        sede = db.get_sede_by_trainer_email(user_email)
        if sede:
            sede_ids.append(sede['id'])
    elif user_role == 'societa':
        # Fetch all sedi under the company
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
    print(f"Filtered sede_ids: {sede_ids}")

    # If no sedi are found, return an empty list of clients
    if not sede_ids:
        clienti = []
        titolo = "Nessun Cliente Disponibile"
    else:
        # Fetch clients based on the filtered sede IDs
        if tipo == 'lead':
            clienti = db.get_leads(sede_ids)
            titolo = "Clienti Lead"
        elif tipo == 'effettivo':
            clienti = db.get_clienti_effettivi(sede_ids)
            titolo = "Clienti Effettivi"
        else:
            clienti = db.get_all_clienti(sede_ids)
            titolo = "Tutti i Clienti"
        
    oggi = date.today().strftime('%Y-%m-%d')
    clienti_ids = [c['id'] for c in clienti]
    clienti_senza_appuntamenti = set(clienti_ids)
    if clienti_ids:
        appuntamenti = db.get_appointments_by_clienti(clienti_ids, oggi)
        clienti_con_appuntamenti = set([a['client_id'] for a in appuntamenti if a['date_time'].date() >= date.today()])
        clienti_senza_appuntamenti = set(clienti_ids) - clienti_con_appuntamenti
    else:
        clienti_senza_appuntamenti = set()

    return render_template('clienti/lista.html', clienti=clienti, titolo=titolo, tipo_attivo=tipo, clienti_senza_appuntamenti=clienti_senza_appuntamenti )


@clienti_bp.route('/clienti/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        cognome = request.form['cognome']
        email = request.form['email']
        telefono = request.form['telefono']
        data_nascita = request.form['data_nascita']
        indirizzo = request.form['indirizzo']
        citta = request.form['citta']
        cap = request.form['cap']
        note = request.form['note']
        tipo = request.form['tipo']
        codice_fiscale = request.form['codice_fiscale']
        tipologia = request.form.get('tipologia')  # New field
        provenienza = request.form.get('provenienza')
        taglia_giubotto = request.form['taglia_giubotto']
        taglia_cintura = request.form['taglia_cintura']
        taglia_braccia = request.form['taglia_braccia']
        taglia_gambe = request.form['taglia_gambe']
        obiettivo_cliente = request.form['obiettivo_cliente']
        sede_id = request.form['sede_id']
        
        cliente_id = db.add_cliente(nome, cognome, email, telefono, data_nascita, 
                                     indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, provenienza, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, sede_id)
        
        db.log_event(session.get('user_id'), session.get('user_email'), 'Aggiunto nuovo cliente', f'Cliente: {nome} {cognome}')
        flash(f'Cliente {nome} {cognome} aggiunto con successo!', 'success')
        return redirect(url_for('clienti.dettaglio_cliente', cliente_id=cliente_id))
    
    # Fetch sedi under the logged-in user's hierarchy
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    hierarchy = db.build_hierarchy(user_role=user_role, user_email=user_email)

    sedi = []
    if user_role == 'franchisor':
        for area_manager in hierarchy[0].get('area_managers', []):
            for societa in area_manager.get('societa', []):
                sedi.extend(societa.get('sedi', []))
    elif user_role == 'area manager':
        for societa in hierarchy[0].get('area_managers', [])[0].get('societa', []):
            sedi.extend(societa.get('sedi', []))
    elif user_role == 'societa':
        # Fetch sedi directly under the company
        societa = db.get_societa_by_email(user_email)
        if societa:
            sedi = db.get_sedi_by_societa(societa['id'])
    elif user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sedi = [sede]
    elif user_role == 'trainer':
        # Fetch the sede associated with the trainer
        sede = db.get_sede_by_trainer_email(user_email)
        if sede:
            sedi = [sede]

    # Safeguard: Ensure `sedi` is a list
    if not isinstance(sedi, list):
        sedi = []

    return render_template('clienti/nuovo.html', sedi=sedi)


@clienti_bp.route('/clienti/<int:cliente_id>')
def dettaglio_cliente(cliente_id):
    cliente = db.get_cliente(cliente_id)
    if not cliente:
        flash('Cliente non trovato', 'error')
        return redirect(url_for('clienti.lista_clienti'))
    
    abbonamenti = db.get_abbonamenti_by_cliente(cliente_id)
    lezioni = db.get_lezioni_by_cliente(cliente_id)
    
    # Convert rows to dictionaries and fetch the email of the user who registered each lesson
    lezioni = db.get_lezioni_by_cliente(cliente_id)
    for lezione in lezioni:
        print(lezione['registrata_da'])
        lezione['registrata_da'] = db.get_user_email_by_id(lezione['registrata_da'])
    
    oggi = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('clienti/dettaglio.html',
                         cliente=cliente,
                         abbonamenti=abbonamenti,
                         lezioni=lezioni,
                         oggi=oggi)

@clienti_bp.route('/clienti/<int:cliente_id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_cliente(cliente_id):
    cliente = db.get_cliente(cliente_id)
    if not cliente:
        abort(404)
    
    if request.method == 'POST':
        nome = request.form['nome']
        cognome = request.form['cognome']
        email = request.form['email']
        telefono = request.form['telefono']
        data_nascita = request.form['data_nascita']
        indirizzo = request.form['indirizzo']
        citta = request.form['citta']
        cap = request.form['cap']
        note = request.form['note']
        tipo = request.form['tipo']
        tipologia = request.form['tipologia']  # Assicurati che venga letto correttamente
        codice_fiscale = request.form['codice_fiscale']
        taglia_giubotto = request.form['taglia_giubotto']
        taglia_cintura = request.form['taglia_cintura']
        taglia_braccia = request.form['taglia_braccia']
        taglia_gambe = request.form['taglia_gambe']
        obiettivo_cliente = request.form['obiettivo_cliente']
        #sede_id = request.form['sede_id']  # Fetch sede_id from the form
        
        try:
            db.update_cliente(cliente_id, nome, cognome, email, telefono, data_nascita, 
                              indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, 
                              taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, 
                              obiettivo_cliente)
            
            db.log_event(session.get('user_id'), session.get('user_email'), 'Modificato cliente', f'Cliente ID: {cliente_id}')
            flash(f'Cliente {nome} {cognome} aggiornato con successo!', 'success')
        except Exception as e:
            flash(f'Errore durante l\'aggiornamento del cliente: {str(e)}', 'error')
            return redirect(url_for('modifica_cliente', cliente_id=cliente_id))
        
        return redirect(url_for('clienti.dettaglio_cliente', cliente_id=cliente_id))
    
    return render_template('clienti/modifica.html', cliente=cliente)


@clienti_bp.route('/clienti/<int:cliente_id>/elimina', methods=['POST'])
def elimina_cliente(cliente_id):
    cliente = db.get_cliente(cliente_id)
    nome = cliente['nome']
    cognome = cliente['cognome']
    if not cliente:
        abort(404)
    
    db.delete_cliente(cliente_id)
    db.log_event(session.get('user_id'), session.get('user_email'), 'Eliminato cliente', f'Cliente: {nome} {cognome}')
    flash(f'Cliente {cliente["nome"]} {cliente["cognome"]} eliminato con successo!', 'success')
    return redirect(url_for('clienti.lista_clienti'))

@clienti_bp.route('/clienti/<int:cliente_id>/promuovi', methods=['POST', 'GET'])
def promuovi_cliente(cliente_id):
    success, message = db.promuovi_cliente(cliente_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('clienti.dettaglio_cliente', cliente_id=cliente_id))