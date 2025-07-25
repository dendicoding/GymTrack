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

    societa_id = request.args.get('societa_id')
    sede_id = request.args.get('sede_id')

    # Se non ci sono parametri, usa la sessione come default
    if societa_id is None and sede_id is None:
        societa_id = session.get('societa_id')
        sede_id = session.get('sede_id')

    if request.args.get('societa_id') is not None:
        session['societa_id'] = societa_id
    if request.args.get('sede_id') is not None:
        session['sede_id'] = sede_id

    # Costruisci la gerarchia per i menu a tendina
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

    # Se la lista sedi è vuota, ricostruiscila dalla gerarchia
    if not sedi:
        if user_role == 'franchisor':
            area_managers = db.get_area_managers_by_franchisor_email(user_email)
            for manager in area_managers:
                for soc in db.get_societa_by_area_manager(manager['id']):
                    sedi.extend([{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(soc['id'])])
        elif user_role == 'area manager':
            societa_list = db.get_societa_by_area_manager_email(user_email)
            for soc in societa_list:
                sedi.extend([{'id': sede['id'], 'nome': sede['nome']} for sede in db.get_sedi_by_societa(soc['id'])])

    # Determina i sede_ids da usare per il filtro abbonamenti
    if sede_id:
        sede_ids = [int(sede_id)]
    elif societa_id:
        sedi_societa = db.get_sedi_by_societa(societa_id)
        sede_ids = [sede['id'] for sede in sedi_societa]
    else:
        sede_ids = [sede['id'] for sede in sedi]

    # Gestione filtri da/a
    oggi = date.today()
    mese_inizio = oggi.replace(day=1)
    mese_fine = (mese_inizio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    da = request.args.get('da', mese_inizio.strftime('%Y-%m-%d'))
    a = request.args.get('a', mese_fine.strftime('%Y-%m-%d'))

    abbonamenti = db.get_abbonamenti_conferiti(sede_ids, da, a)

    return render_template(
        'abbonamenti_conferiti.html',
        abbonamenti=abbonamenti,
        da=da,
        a=a,
        societa=societa,
        sedi=sedi,
        selected_societa_id=str(societa_id) if societa_id else '',
        selected_sede_id=str(sede_id) if sede_id else ''
    )