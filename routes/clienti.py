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

    # Filtri società/sede
    societa_id = request.args.get('societa_id')
    sede_id = request.args.get('sede_id')

    # Se non ci sono parametri, usa la sessione come default
    if societa_id is None and sede_id is None:
        societa_id = session.get('societa_id')
        sede_id = session.get('sede_id')

    # Aggiorna la sessione se l'utente cambia filtro
    if request.args.get('societa_id') is not None:
        session['societa_id'] = societa_id
    if request.args.get('sede_id') is not None:
        session['sede_id'] = sede_id

    # Costruisci la gerarchia per i menu a tendina
    hierarchy = db.build_hierarchy(user_role=user_role, user_email=user_email)
    societa = []
    sedi = []

    if user_role == 'franchisor':
        for area_manager in hierarchy[0].get('area_managers', []):
            for soc in area_manager.get('societa', []):
                societa.append({'id': soc['id'], 'nome': soc['nome']})
        if societa_id:
            sedi = [{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(societa_id)]
        else:
            for area_manager in hierarchy[0].get('area_managers', []):
                for soc in area_manager.get('societa', []):
                    sedi.extend([{'id': sede['id'], 'nome': sede['nome']} for sede in soc.get('sedi', [])])
    elif user_role == 'area manager':
        for area_manager in hierarchy[0].get('area_managers', []):
            if area_manager.get('email') == user_email:
                for soc in area_manager.get('societa', []):
                    societa.append({'id': soc['id'], 'nome': soc['nome']})
        if societa_id:
            sedi = [{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(societa_id)]
        else:
            for area_manager in hierarchy[0].get('area_managers', []):
                if area_manager.get('email') == user_email:
                    for soc in area_manager.get('societa', []):
                        sedi.extend([{'id': sede['id'], 'nome': sede['nome']} for sede in soc.get('sedi', [])])
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

    # Determina i sede_ids da usare per il filtro clienti
    sede_ids = []
    if sede_id:
        sede_ids = [int(sede_id)]
    elif societa_id:
        sedi_societa = db.get_sedi_by_societa(societa_id)
        sede_ids = [sede['id'] for sede in sedi_societa]
    else:
        sede_ids = [sede['id'] for sede in sedi]

    # Se non ci sono sedi, nessun cliente
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
        
    for cliente in clienti:
        # Conta le sedi associate (usando la tabella clienti_sedi)
        sedi_assoc = db.get_sedi_aggiuntive_cliente(cliente['id'], cliente['sede_id'])
        cliente['is_multi_sede'] = len(sedi_assoc) > 0

    oggi = date.today().strftime('%Y-%m-%d')
    clienti_ids = [c['id'] for c in clienti]
    clienti_senza_appuntamenti = set(clienti_ids)
    clienti_prova_annullata = set()
    if clienti_ids:
        appuntamenti = db.get_appointments_by_clienti(clienti_ids, oggi)
        clienti_con_appuntamenti = set([a['client_id'] for a in appuntamenti if a['date_time'].date() >= date.today()])
        clienti_senza_appuntamenti = set(clienti_ids) - clienti_con_appuntamenti

        # Evidenzia anche chi ha almeno una "prova annullata"
        for a in appuntamenti:
            if (a.get('status', '').lower().replace(' ', '_') == 'prova_annullata'):
                clienti_prova_annullata.add(a['client_id'])
    else:
        clienti_senza_appuntamenti = set()
        clienti_prova_annullata = set()
    
    clienti_evidenziati = clienti_senza_appuntamenti | clienti_prova_annullata

    # Passa anche societa, sedi, e i valori selezionati al template
    return render_template(
        'clienti/lista.html',
        clienti=clienti,
        titolo=titolo,
        tipo_attivo=tipo,
        clienti_senza_appuntamenti=clienti_evidenziati,
        societa=societa,
        sedi=sedi,
        selected_societa_id=str(societa_id) if societa_id else '',
        selected_sede_id=str(sede_id) if sede_id else ''
    )

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
        multi_sede = request.form.get('multi_sede')
        sedi_ids = [sede_id]
        if multi_sede:
            sedi_aggiuntive = request.form.getlist('sedi_aggiuntive')
            # Evita duplicati e la sede principale
            sedi_ids += [sid for sid in sedi_aggiuntive if sid != sede_id]
        
        cliente_id = db.add_cliente(nome, cognome, email, telefono, data_nascita, 
                                     indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, provenienza, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, sede_id)
        
        if multi_sede and sedi_ids:
            db.set_clienti_sedi(cliente_id, sedi_ids)
        else:
            db.set_clienti_sedi(cliente_id, [sede_id])
        db.log_event(session.get('user_id'), session.get('user_email'), 'Aggiunto nuovo cliente', f'Cliente: {nome} {cognome}')
        flash(f'Cliente {nome} {cognome} aggiunto con successo!', 'success')
        # Redireziona in base al tipo
        if tipo.lower() == 'lead':
            return redirect(url_for('clienti.lista_clienti'))
        else:
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
        for area_manager in hierarchy[0].get('area_managers', []):
            # Filtra solo l'area manager loggato
            if area_manager.get('email') == user_email:
                for societa in area_manager.get('societa', []):
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
    for lezione in lezioni:
        lezione['registrata_da'] = db.get_user_email_by_id(lezione['registrata_da'])

    oggi = datetime.now().strftime('%Y-%m-%d')

    # Usa la funzione del database per recuperare le sedi aggiuntive
    sedi_aggiuntive = db.get_sedi_aggiuntive_cliente(cliente_id, cliente['sede_id'])

    return render_template('clienti/dettaglio.html',
                         cliente=cliente,
                         abbonamenti=abbonamenti,
                         lezioni=lezioni,
                         oggi=oggi,
                         sedi_aggiuntive=sedi_aggiuntive)

@clienti_bp.route('/clienti/<int:cliente_id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_cliente(cliente_id):
    cliente = db.get_cliente(cliente_id)
    if not cliente:
        abort(404)

    # Recupera tutte le sedi disponibili per l'utente loggato
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    hierarchy = db.build_hierarchy(user_role=user_role, user_email=user_email)
    sedi = []
    if user_role == 'franchisor':
        for area_manager in hierarchy[0].get('area_managers', []):
            for societa in area_manager.get('societa', []):
                sedi.extend(societa.get('sedi', []))
    elif user_role == 'area manager':
        for area_manager in hierarchy[0].get('area_managers', []):
            if area_manager.get('email') == user_email:
                for societa in area_manager.get('societa', []):
                    sedi.extend(societa.get('sedi', []))
    elif user_role == 'societa':
        societa = db.get_societa_by_email(user_email)
        if societa:
            sedi = db.get_sedi_by_societa(societa['id'])
    elif user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sedi = [sede]
    elif user_role == 'trainer':
        sede = db.get_sede_by_trainer_email(user_email)
        if sede:
            sedi = [sede]
    if not isinstance(sedi, list):
        sedi = []

    # Recupera le sedi associate al cliente (oltre la principale)
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT sede_id FROM clienti_sedi WHERE cliente_id = %s', (cliente_id,))
    sedi_associati = [str(row[0]) for row in cursor.fetchall() if str(row[0]) != str(cliente['sede_id'])]
    conn.close()
    multi_sede = len(sedi_associati) > 0

    if request.method == 'POST':
        nome = request.form['nome']
        cognome = request.form['cognome']
        email = request.form['email']
        telefono = request.form['telefono']
        data_nascita = request.form['data_nascita']
        if not data_nascita:
            data_nascita = None
        indirizzo = request.form['indirizzo']
        citta = request.form['citta']
        cap = request.form['cap']
        note = request.form['note']
        tipo = request.form['tipo']
        tipologia = request.form['tipologia']
        codice_fiscale = request.form['codice_fiscale']
        taglia_giubotto = request.form['taglia_giubotto']
        taglia_cintura = request.form['taglia_cintura']
        taglia_braccia = request.form['taglia_braccia']
        taglia_gambe = request.form['taglia_gambe']
        obiettivo_cliente = request.form['obiettivo_cliente']
        sede_id = request.form['sede_id']
        multi_sede = request.form.get('multi_sede')
        sedi_ids = [sede_id]
        if multi_sede:
            sedi_aggiuntive = request.form.getlist('sedi_aggiuntive')
            sedi_ids += [sid for sid in sedi_aggiuntive if sid != sede_id]
        try:
            db.update_cliente(cliente_id, nome, cognome, email, telefono, data_nascita,
                              indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia,
                              taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe,
                              obiettivo_cliente, sede_id)
            db.set_clienti_sedi(cliente_id, sedi_ids)
            db.log_event(session.get('user_id'), session.get('user_email'), 'Modificato cliente', f'Cliente ID: {cliente_id}')
            flash(f'Cliente {nome} {cognome} aggiornato con successo!', 'success')
        except Exception as e:
            flash(f'Errore durante l\'aggiornamento del cliente: {str(e)}', 'error')
            return redirect(url_for('clienti.modifica_cliente', cliente_id=cliente_id))
        return redirect(url_for('clienti.dettaglio_cliente', cliente_id=cliente_id))

    return render_template('clienti/modifica.html',
                           cliente=cliente,
                           sedi=sedi,
                           sedi_associati=sedi_associati,
                           multi_sede=multi_sede)


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
    

