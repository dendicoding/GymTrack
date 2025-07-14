from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date, datetime, timedelta
from utils.auth import login_required
from calendar import monthcalendar

# ... altri import ...
rate_bp = Blueprint('rate', __name__)

@rate_bp.route('/rate/<int:rata_id>/modifica', methods=['GET', 'POST'])
def modifica_rata(rata_id):
    rata = db.get_rata(rata_id)
    if not rata:
        flash('Rata non trovata', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if rata['pagato']:
            # Se la rata è pagata, aggiorna data_pagamento e metodo_pagamento
            data_pagamento = request.form.get('data_pagamento')
            metodo_pagamento = request.form.get('metodo_pagamento')
            if db.modifica_rata_pagata(rata_id, data_pagamento, metodo_pagamento):
                flash('Rata modificata con successo!', 'success')
            else:
                flash('Errore durante la modifica della rata', 'error')
        else:
            # Se la rata non è pagata, aggiorna importo e data_scadenza
            importo = request.form.get('importo', type=float)
            data_scadenza = request.form.get('data_scadenza')
            if db.modifica_rata_non_pagata(rata_id, importo, data_scadenza):
                flash('Rata modificata con successo!', 'success')
            else:
                flash('Errore durante la modifica della rata', 'error')

        return redirect(url_for('abbonamenti.dettaglio_abbonamento', abbonamento_id=rata['abbonamento_id']))

    return render_template('rate/modifica_rata.html', rata=rata)

@rate_bp.route('/rate/<int:rata_id>/paga', methods=['GET', 'POST'])
def paga_rata(rata_id):
    oggi = date.today().strftime('%Y-%m-%d')
    rata = db.get_rata(rata_id)
    if not rata:
        flash('Rata non trovata', 'error')
        return redirect(url_for('clienti.lista_clienti'))
    
    if rata['pagato']:
        flash('Questa rata è già stata pagata', 'warning')
        return redirect(url_for('abbonamenti.dettaglio_abbonamento', abbonamento_id=rata['abbonamento_id']))
    
    if request.method == 'POST':
        from decimal import Decimal
        data_pagamento = request.form.get('data_pagamento', datetime.now().strftime('%Y-%m-%d'))
        metodo_pagamento = request.form.get('metodo_pagamento')
        importo_pagato = Decimal(request.form.get('importo_pagato'))
        pagamento_parziale = 'pagamento_parziale' in request.form
        
        if importo_pagato < rata['importo'] and pagamento_parziale:
            importo_rimanente = rata['importo'] - importo_pagato
            if isinstance(rata['data_scadenza'], str):
                data_scadenza = datetime.strptime(rata['data_scadenza'], '%Y-%m-%d').date()
            else:
                data_scadenza = rata['data_scadenza']
            nuova_data_scadenza = (data_scadenza + timedelta(days=7)).strftime('%Y-%m-%d')            
            if db.paga_rata(rata_id, metodo_pagamento, importo_pagato):
                db.crea_nuova_rata(rata['abbonamento_id'], importo_rimanente, nuova_data_scadenza)
                db.log_event(session.get('user_id'), session.get('user_email'), 'Pagamento parziale rata', f'Rata ID: {rata_id}')
                flash('Pagamento parziale registrato con successo e nuova rata generata', 'success')
            else:
                flash('Errore durante la registrazione del pagamento parziale', 'error')
        else:
            if db.paga_rata(rata_id, metodo_pagamento, importo_pagato):
                db.log_event(session.get('user_id'), session.get('user_email'), 'Pagamento rata', f'Rata ID: {rata_id}')
                flash('Pagamento registrato con successo', 'success')
            else:
                flash('Errore durante la registrazione del pagamento', 'error')
        
        return redirect(url_for('abbonamenti.dettaglio_abbonamento', abbonamento_id=rata['abbonamento_id']))
    
    return render_template('rate/paga.html', rata=rata, oggi=oggi)

# --- CALENDARIO E SCADENZIARIO ---
@rate_bp.route('/calendario')
@login_required
def calendario():
    mese = request.args.get('mese', date.today().month, type=int)
    anno = request.args.get('anno', date.today().year, type=int)
    
    # Calcola il mese precedente e successivo
    if mese == 1:
        mese_precedente = date(anno - 1, 12, 1)
    else:
        mese_precedente = date(anno, mese - 1, 1)
        
    if mese == 12:
        mese_successivo = date(anno + 1, 1, 1)
    else:
        mese_successivo = date(anno, mese + 1, 1)
    
    # Ottieni il calendario del mese
    cal = monthcalendar(anno, mese)
    
    # Fetch sede_ids based on user role
    user_role = session.get('user_role')
    user_email = session.get('user_email')
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

    # Ottieni le scadenze dal database
    scadenze = db.get_rate_calendario(mese, anno, sede_ids)
    scadenze_dict = {}
    
    # Creiamo un dizionario con la data come chiave
    for scadenza in scadenze:
    # Se data_scadenza è già una data, non serve convertirla
        if isinstance(scadenza['data_scadenza'], str):
            data = datetime.strptime(scadenza['data_scadenza'], '%Y-%m-%d').date()
        else:
            data = scadenza['data_scadenza']
        scadenze_dict[data.day] = {
            'rate_da_pagare': scadenza['rate_da_pagare'],
            'clienti': scadenza['clienti'].split(',') if scadenza['clienti'] else [],
            'clienti_ids': scadenza['clienti_ids'].split(',') if scadenza['clienti_ids'] else []
        }
    
    # Formatta il calendario per il template
    calendario = []
    for settimana in cal:
        settimana_formattata = []
        for giorno in settimana:
            if giorno == 0:
                settimana_formattata.append({
                    'data': None,
                    'altro_mese': True,
                    'scadenze': None
                })
            else:
                settimana_formattata.append({
                    'data': date(anno, mese, giorno),
                    'altro_mese': False,
                    'scadenze': scadenze_dict.get(giorno)
                })
        calendario.append(settimana_formattata)
    
    return render_template('calendario.html',
                         calendario=calendario,
                         mese_corrente=mese,
                         anno_corrente=anno,
                         mese_precedente=mese_precedente,
                         mese_successivo=mese_successivo)

@rate_bp.route('/scadenziario')
@login_required
def scadenziario():
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
    rate = db.get_rate_scadenza(sede_ids)
    oggi = date.today()
    return render_template('scadenziario.html', rate=rate, oggi=oggi)

