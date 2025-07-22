from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date, datetime, timedelta
from utils.auth import login_required
abbonamenti_bp = Blueprint('abbonamenti', __name__)

# --- GESTIONE ABBONAMENTI ---
@abbonamenti_bp.route('/clienti/<int:cliente_id>/abbonamenti/nuovo', methods=['GET', 'POST'])
def nuovo_abbonamento(cliente_id):
    cliente = db.get_cliente(cliente_id)
    if not cliente:
        flash('Cliente non trovato', 'error')
        return redirect(url_for('clienti.lista_clienti'))
    
    if request.method == 'POST':
        pacchetto_id = request.form.get('pacchetto_id', type=int)
        data_inizio = request.form.get('data_inizio')
        prezzo_totale = request.form.get('prezzo_totale', type=float)
        numero_rate = request.form.get('numero_rate', type=int, default=1)
        numero_lezioni = request.form.get('numero_lezioni', type=int)  # <-- aggiungi questa riga

        if db.create_abbonamento(cliente_id, pacchetto_id, data_inizio, prezzo_totale, numero_rate, numero_lezioni):
            flash('Abbonamento creato con successo', 'success')
            return redirect(url_for('clienti.dettaglio_cliente', cliente_id=cliente_id))
        else:
            flash('Errore durante la creazione dell\'abbonamento', 'error')
    
    pacchetti = db.get_all_pacchetti_validi()
    return render_template('abbonamenti/nuovo.html', 
                         cliente=cliente, 
                         pacchetti=pacchetti,
                         oggi=datetime.now().strftime('%Y-%m-%d'))

@abbonamenti_bp.route('/abbonamenti/<int:abbonamento_id>')
def dettaglio_abbonamento(abbonamento_id):
    abbonamento = db.get_abbonamento(abbonamento_id)
    if not abbonamento:
        flash('Abbonamento non trovato', 'error')
        return redirect(url_for('index'))
    
    cliente = db.get_cliente(abbonamento['cliente_id'])
    rate = db.get_rate_by_abbonamento(abbonamento_id)
    lezioni = db.get_lezioni_by_abbonamento(abbonamento_id)

        # Convert rows to dictionaries and fetch the email of the user who registered each lesson
    lezioni = [dict(lezione) for lezione in lezioni]
    for lezione in lezioni:
        print(lezione['registrata_da'])
        lezione['registrata_da'] = db.get_user_email_by_id(lezione['registrata_da'])
    oggi = date.today()
    
    return render_template('abbonamenti/dettaglio.html',
                         abbonamento=abbonamento,
                         cliente=cliente,
                         rate=rate,
                         lezioni=lezioni,
                         oggi=oggi)

@abbonamenti_bp.route('/abbonamenti/<int:abbonamento_id>/elimina', methods=['POST'])
def elimina_abbonamento(abbonamento_id):
    abbonamento = db.get_abbonamento(abbonamento_id)
    if not abbonamento:
        flash('Abbonamento non trovato', 'error')
        return redirect(url_for('index'))
    
    cliente_id = abbonamento['cliente_id']
    
    if db.delete_abbonamento(abbonamento_id):
        db.log_event(session.get('user_id'), session.get('user_email'), 'Eliminato abbonamento', f'Abbonamento ID: {abbonamento_id}')
        flash('Abbonamento eliminato con successo', 'success')
    else:
        flash('Errore durante l\'eliminazione dell\'abbonamento', 'error')
    
    return redirect(url_for('clienti.dettaglio_cliente', cliente_id=cliente_id))

@abbonamenti_bp.route('/abbonamenti_conferiti')
def abbonamenti_conferiti():
    user_role = session.get('user_role')
    user_email = session.get('user_email')
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
        for company in societa:
            sedi.extend(db.get_sedi_by_societa(company['id']))
    elif user_role == 'societa':
        societa = db.get_societa_by_email(user_email)
        if societa:
            sedi = db.get_sedi_by_societa(societa['id'])
    elif user_role == 'franchisor':
        area_managers = db.get_area_managers_by_franchisor_email(user_email)
        societa = []
        for manager in area_managers:
            societa.extend(db.get_societa_by_area_manager(manager['id']))
        for company in societa:
            sedi.extend(db.get_sedi_by_societa(company['id']))

    sede_ids = [s['id'] for s in sedi if s and 'id' in s]

    # Gestione filtri da/a
    oggi = date.today()
    mese_inizio = oggi.replace(day=1)
    mese_fine = (mese_inizio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    da = request.args.get('da', mese_inizio.strftime('%Y-%m-%d'))
    a = request.args.get('a', mese_fine.strftime('%Y-%m-%d'))

    abbonamenti = db.get_abbonamenti_conferiti(sede_ids, da, a)

    return render_template('abbonamenti_conferiti.html', abbonamenti=abbonamenti, da=da, a=a)