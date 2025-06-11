from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date, datetime
from utils.auth import login_required

lezioni_bp = Blueprint('lezioni', __name__)

@lezioni_bp.route('/abbonamenti/<int:abbonamento_id>/registra-lezione', methods=['GET', 'POST'])
@login_required
def registra_lezione(abbonamento_id):
    # Ottieni l'abbonamento
    abbonamento = db.get_abbonamento(abbonamento_id)
    if not abbonamento:
        flash('Abbonamento non trovato', 'error')
        return redirect(url_for('clienti.lista_clienti'))
    
    # Ottieni il cliente
    cliente = db.get_cliente(abbonamento['cliente_id'])
    if not cliente:
        flash('Cliente non trovato', 'error')
        return redirect(url_for('clienti.lista_clienti'))
    
    # Verifica se l'abbonamento è ancora valido
    oggi = datetime.now().date()
    data_scadenza = datetime.strptime(abbonamento['data_fine'], '%Y-%m-%d').date()
    
    if data_scadenza < oggi:
        flash('Abbonamento scaduto', 'error')
        return redirect(url_for('clienti.dettaglio_cliente', cliente_id=cliente['id']))
    
    # Verifica se ci sono ancora lezioni disponibili
    lezioni_rimanenti = abbonamento['numero_lezioni'] - abbonamento['lezioni_utilizzate']
    if lezioni_rimanenti <= 0:
        flash('Nessuna lezione rimanente', 'error')
        return redirect(url_for('clienti.dettaglio_cliente', cliente_id=cliente['id']))
    
    if request.method == 'POST':
        data = request.form.get('data')
        note = request.form.get('note', '')
        user_id = session.get('user_id')
        
        # Registra la lezione
        if db.add_lezione(abbonamento_id, data, note, user_id):
            db.log_event(session.get('user_id'), session.get('user_email'), 'Registrata lezione', f'Abbonamento ID: {abbonamento_id}')
            flash('Lezione registrata con successo', 'success')
            return redirect(url_for('clienti.dettaglio_cliente', cliente_id=cliente['id']))
        else:
            flash('Errore durante la registrazione della lezione', 'error')
    
    return render_template('lezioni/registra.html',
                         cliente=cliente,
                         abbonamento=abbonamento,
                         oggi=oggi.strftime('%Y-%m-%d'))


#---------------DA MANTENERE?
@lezioni_bp.route('/abbonamenti/<int:abbonamento_id>/nuova-lezione', methods=['GET', 'POST'])
def nuova_lezione(abbonamento_id):
    abbonamento = db.get_abbonamento(abbonamento_id)
    if not abbonamento:
        abort(404)
    
    if request.method == 'POST':
        data = request.form['data']
        note = request.form['note']
        user_email = session.get('user_email')  # Get the current user's email
        
        lezione_id = db.add_lezione(abbonamento_id, data, note, user_email)
        
        flash('Lezione aggiunta con successo!', 'success')
        return redirect(url_for('dettaglio_abbonamento', abbonamento_id=abbonamento_id))
    
    cliente = db.get_cliente(abbonamento['cliente_id'])
    return render_template('abbonamenti/nuova_lezione.html', abbonamento=abbonamento, cliente=cliente)

@lezioni_bp.route('/lezioni/<int:lezione_id>/completa', methods=['POST'])
def completa_lezione(lezione_id):
    db.completa_lezione(lezione_id)
    flash('Lezione completata con successo!', 'success')
    return redirect(request.referrer or url_for('index'))
#---------------------------------------------------------------