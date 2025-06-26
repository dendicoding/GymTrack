from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date
from utils.auth import login_required
# ... altri import ...

pacchetti_bp = Blueprint('pacchetti', __name__)

@pacchetti_bp.route('/pacchetti')
def lista_pacchetti():
    pacchetti = db.get_all_pacchetti()
    
    return render_template('pacchetti/lista.html', pacchetti=pacchetti)

@pacchetti_bp.route('/pacchetti/<int:pacchetto_id>')
def dettaglio_pacchetto(pacchetto_id):
    pacchetto = db.get_pacchetto(pacchetto_id)
    if not pacchetto:
        flash('Pacchetto non trovato', 'error')
        return redirect(url_for('pacchetti.lista_pacchetti'))
    
    statistiche = db.get_statistiche_pacchetto(pacchetto_id)
    abbonamenti = db.get_abbonamenti_by_pacchetto(pacchetto_id)
    mesi, vendite_mensili = db.get_vendite_mensili_pacchetto(pacchetto_id)
    oggi = date.today()
    
    return render_template('pacchetti/dettaglio.html',
                         pacchetto=pacchetto,
                         statistiche=statistiche,
                         abbonamenti=abbonamenti,
                         mesi=mesi,
                         vendite_mensili=vendite_mensili,
                         oggi=oggi)

@pacchetti_bp.route('/pacchetti/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_pacchetto():
    # Consenti solo ai franchisor
    if session.get('user_role') != 'franchisor':
        flash('Non hai i permessi per creare nuovi pacchetti.', 'danger')
        return redirect(url_for('pacchetti.lista_pacchetti'))

    if request.method == 'POST':
        # Recupera i dati dal form
        nome = request.form.get('nome')
        descrizione = request.form.get('descrizione')
        prezzo = request.form.get('prezzo', type=float)
        numero_lezioni = request.form.get('numero_lezioni', type=int)
        attivo = 'attivo' in request.form
        pagamento_unico = 'pagamento_unico' in request.form
        data_scadenza = request.form.get('data_scadenza')

        # Aggiungi il pacchetto al database
        try:
            db.add_pacchetto(nome, descrizione, prezzo, numero_lezioni, attivo, pagamento_unico, data_scadenza)
            flash('Pacchetto aggiunto con successo!', 'success')
            return redirect(url_for('pacchetti.lista_pacchetti'))
        except Exception as e:
            flash(f'Errore durante l\'aggiunta del pacchetto: {e}', 'danger')

    # In caso di richiesta GET o errore, mostra il form
    return render_template('pacchetti/nuovo.html')


@pacchetti_bp.route('/pacchetti/<int:pacchetto_id>/elimina', methods=['POST'])
def elimina_pacchetto(pacchetto_id):
    pacchetto = db.get_pacchetto(pacchetto_id)
    if not pacchetto:
        flash('Pacchetto non trovato', 'error')
        return redirect(url_for('pacchetti.lista_pacchetti'))
    
    try:
        db.delete_pacchetto(pacchetto_id)
        flash('Pacchetto eliminato con successo!', 'success')
    except Exception as e:
        flash(f'Errore durante l\'eliminazione del pacchetto: {e}', 'danger')
    
    return redirect(url_for('pacchetti.lista_pacchetti'))


@pacchetti_bp.route('/pacchetti/<int:pacchetto_id>/modifica', methods=['GET', 'POST'])
def modifica_pacchetto(pacchetto_id):
    pacchetto = db.get_pacchetto(pacchetto_id)
    if not pacchetto:
        flash('Pacchetto non trovato', 'error')
        return redirect(url_for('pacchetti.lista_pacchetti'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        descrizione = request.form.get('descrizione')
        prezzo = float(request.form.get('prezzo'))
        numero_lezioni = int(request.form.get('numero_lezioni'))
        durata_giorni = int(request.form.get('durata_giorni'))
        attivo = 'attivo' in request.form
        pagamento_unico = 'pagamento_unico' in request.form
        usa_data_scadenza = 'usa_data_scadenza' in request.form
        data_scadenza = request.form.get('data_scadenza') if usa_data_scadenza else None
        
        if db.update_pacchetto(pacchetto_id, nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo, pagamento_unico, data_scadenza):
            flash('Pacchetto aggiornato con successo!', 'success')
        else:
            flash('Errore durante l\'aggiornamento del pacchetto.', 'error')
        
        return redirect(url_for('pacchetti.dettaglio_pacchetto', pacchetto_id=pacchetto_id))
    
    return render_template('pacchetti/modifica.html', pacchetto=pacchetto)


@pacchetti_bp.route('/get_pacchetti/<int:client_id>', methods=['GET'])
@login_required
def get_pacchetti(client_id):
    pacchetti = db.get_abbonamenti_by_cliente(client_id)
    print(f"Pacchetti per il cliente {client_id}: {pacchetti}")
    return jsonify([{
        'id': pacchetto['id'],
        'nome': pacchetto['nome_pacchetto'],
        'lezioni_rimanenti': pacchetto['numero_lezioni'] - pacchetto['lezioni_utilizzate']
    } for pacchetto in pacchetti])