from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from werkzeug.exceptions import NotFound
import database as db
from datetime import datetime, date
import locale
from datetime import datetime, timedelta
from models.abbonamento import Abbonamento
from calendar import monthcalendar
from collections import defaultdict

from flask import session, g
from functools import wraps
app = Flask(__name__)
app.secret_key = 'sviluppo_palestra_2025'  # Chiave necessaria per flash messages
# Aggiungi questa configurazione per la sessione
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Inizializzazione del database
db.init_db()


# Set locale for currency formatting (use 'it_IT' for Italian format)
locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')  # Adjust as needed

# Aggiungi questa funzione per il login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Devi effettuare il login per accedere a questa pagina', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Aggiungi alla funzione init_db
@app.before_request
def setup():
    db.init_db()
    db.create_user_tables()

# Aggiungi queste route per il login e la registrazione
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        user = db.authenticate_user(email, password, role)
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['nome']
            session['user_role'] = role
            
            flash(f'Benvenuto, {user["nome"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email o password non validi', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout effettuato con successo', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = request.form['password']
        
        franchisor_id = db.register_franchisor(nome, email, password)
        
        if franchisor_id:
            flash('Registrazione completata con successo!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Errore durante la registrazione', 'error')
    
    return render_template('auth/register.html')

@app.route('/gestione-gerarchia')
@login_required
def gestione_gerarchia():
    # Controlla il ruolo dell'utente
    role = session.get('user_role')
    user_id = session.get('user_id')
    
    if role == 'franchisor':
        area_managers = db.get_area_managers_by_franchisor(user_id)
        return render_template('auth/gerarchia.html', 
                             role=role, 
                             area_managers=area_managers)
    elif role == 'area_manager':
        societa = db.get_societa_by_area_manager(user_id)
        return render_template('auth/gerarchia.html', 
                             role=role, 
                             societa=societa)
    elif role == 'societa':
        sedi = db.get_sedi_by_societa(user_id)
        return render_template('auth/gerarchia.html', 
                             role=role, 
                             sedi=sedi)
    else:
        flash('Non hai i permessi per accedere a questa pagina', 'error')
        return redirect(url_for('index'))

@app.route('/add-area-manager', methods=['GET', 'POST'])
@login_required
def add_area_manager():
    #if session.get('user_role') != 'franchisor':
        #flash('Non hai i permessi per aggiungere area manager', 'error')
        #return redirect(url_for('index'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        cognome = request.form['cognome']
        email = request.form['email']
        password = request.form['password']
        franchisor_id = request.form['franchisor_id']
        
        # Register the area manager
        area_manager_id = db.register_area_manager(franchisor_id, nome, cognome, email, password)
        
        if area_manager_id:
            # Create the user in the utenti table
            user_created = db.create_user(nome, cognome, email, password, 'area_manager')
            if user_created:
                flash('Area Manager aggiunto con successo!', 'success')
                return redirect(url_for('gestione_gerarchia'))
            else:
                flash('Errore durante la creazione dell\'utente Area Manager', 'error')
        else:
            flash('Errore durante l\'aggiunta dell\'Area Manager', 'error')
    
    return render_template('auth/add_area_manager.html')

@app.route('/add-societa', methods=['GET', 'POST'])
@login_required
def add_societa():
    #if session.get('user_role') != 'area_manager':
        #flash('Non hai i permessi per aggiungere società', 'error')
        #return redirect(url_for('index'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = request.form['password']
        area_manager_id = request.form['area_manager_id']
        
        societa_id = db.register_societa(area_manager_id, nome, email, password)
        
        if societa_id:
            flash('Società aggiunta con successo!', 'success')
            return redirect(url_for('gestione_gerarchia'))
        else:
            flash('Errore durante l\'aggiunta della Società', 'error')
    
    return render_template('auth/add_societa.html')

@app.route('/add-sede', methods=['GET', 'POST'])
@login_required
def add_sede():
    #if session.get('user_role') != 'societa':
        #flash('Non hai i permessi per aggiungere sedi', 'error')
        #return redirect(url_for('index'))
    
    if request.method == 'POST':
        print(request.form)  # Debugging line
        nome = request.form['nome']
        indirizzo = request.form['indirizzo']
        citta = request.form['citta']
        cap = request.form['cap']  # This line raises the error if 'cap' is missing
        email = request.form['email']
        password = request.form['password']
        societa_id = request.form['societa_id']
        
        sede_id = db.register_sede(societa_id, nome, indirizzo, citta, cap, email, password)
        
        if sede_id:
            flash('Sede aggiunta con successo!', 'success')
            return redirect(url_for('gestione_gerarchia'))
        else:
            flash('Errore durante l\'aggiunta della Sede', 'error')
    
    return render_template('auth/add_sede.html')

# Custom Jinja2 filters
@app.template_filter('format_date')
def format_date_filter(date):
    if isinstance(date, str):
        try:
            # Converte la stringa in oggetto datetime
            date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return date  # Ritorna la stringa originale se non può essere convertita
    
    # A questo punto date dovrebbe essere un oggetto datetime
    try:
        return date.strftime('%d/%m/%Y')
    except AttributeError:
        return date  # Ritorna il valore originale se non può essere formattato

@app.template_filter('format_datetime')
def format_datetime_filter(date):
    if not date:
        return ""
    return date.strftime('%d/%m/%Y %H:%M')

@app.template_filter('format_currency')
def format_currency_filter(value):
    try:
        return f"€{float(value):,.2f}"
    except (ValueError, TypeError):
        return value

@app.template_filter('to_date')
def to_date_filter(date_str):
    if not date_str:
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()

@app.template_filter('month_name')
def month_name_filter(month_number):
    mesi = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
            'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    return mesi[month_number - 1]

# Route principale e dashboard
@app.route('/')
@login_required
def index():
    #rate_in_scadenza = db.get_rate_scadenza(7)
    stats = db.get_statistiche_dashboard()
    oggi = date.today()
    return render_template('dashboard.html', stats=stats, oggi=oggi)

# --- GESTIONE CLIENTI ---
@app.route('/clienti')
def lista_clienti():
    tipo = request.args.get('tipo', 'tutti')
    
    if tipo == 'lead':
        clienti = db.get_leads()
        titolo = "Clienti Lead"
    elif tipo == 'effettivo':
        clienti = db.get_clienti_effettivi()
        titolo = "Clienti Effettivi"
    else:
        clienti = db.get_all_clienti()
        titolo = "Tutti i Clienti"
    
    return render_template('clienti/lista.html', clienti=clienti, titolo=titolo, tipo_attivo=tipo)

@app.route('/clienti/nuovo', methods=['GET', 'POST'])
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
        
        cliente_id = db.add_cliente(nome, cognome, email, telefono, data_nascita, 
                                     indirizzo, citta, cap, note, tipo, codice_fiscale)
        
        flash(f'Cliente {nome} {cognome} aggiunto con successo!', 'success')
        return redirect(url_for('dettaglio_cliente', cliente_id=cliente_id))
    
    return render_template('clienti/nuovo.html')

@app.route('/clienti/<int:cliente_id>')
def dettaglio_cliente(cliente_id):
    cliente = db.get_cliente(cliente_id)
    if not cliente:
        flash('Cliente non trovato', 'error')
        return redirect(url_for('lista_clienti'))
    
    abbonamenti = db.get_abbonamenti_by_cliente(cliente_id)
    lezioni = db.get_lezioni_by_cliente(cliente_id)
    oggi = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('clienti/dettaglio.html',
                         cliente=cliente,
                         abbonamenti=abbonamenti,
                         lezioni=lezioni,
                         oggi=oggi)

@app.route('/clienti/<int:cliente_id>/modifica', methods=['GET', 'POST'])
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
        codice_fiscale = request.form['codice_fiscale']
        
        db.update_cliente(cliente_id, nome, cognome, email, telefono, data_nascita, 
                          indirizzo, citta, cap, note, tipo, codice_fiscale)
        
        flash(f'Cliente {nome} {cognome} aggiornato con successo!', 'success')
        return redirect(url_for('dettaglio_cliente', cliente_id=cliente_id))
    
    return render_template('clienti/modifica.html', cliente=cliente)

@app.route('/clienti/<int:cliente_id>/elimina', methods=['POST'])
def elimina_cliente(cliente_id):
    cliente = db.get_cliente(cliente_id)
    if not cliente:
        abort(404)
    
    db.delete_cliente(cliente_id)
    flash(f'Cliente {cliente["nome"]} {cliente["cognome"]} eliminato con successo!', 'success')
    return redirect(url_for('lista_clienti'))

@app.route('/clienti/<int:cliente_id>/promuovi', methods=['POST', 'GET'])
def promuovi_cliente(cliente_id):
    success, message = db.promuovi_cliente(cliente_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('dettaglio_cliente', cliente_id=cliente_id))

# --- GESTIONE PACCHETTI ---
@app.route('/pacchetti')
def lista_pacchetti():
    pacchetti = db.get_all_pacchetti()
    return render_template('pacchetti/lista.html', pacchetti=pacchetti)

@app.route('/pacchetti/<int:pacchetto_id>')
def dettaglio_pacchetto(pacchetto_id):
    pacchetto = db.get_pacchetto(pacchetto_id)
    if not pacchetto:
        flash('Pacchetto non trovato', 'error')
        return redirect(url_for('lista_pacchetti'))
    
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

@app.route('/pacchetti/nuovo', methods=['GET', 'POST'])
def nuovo_pacchetto():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descrizione = request.form.get('descrizione')
        prezzo = float(request.form.get('prezzo'))
        numero_lezioni = int(request.form.get('numero_lezioni'))
        durata_giorni = int(request.form.get('durata_giorni'))
        attivo = 'attivo' in request.form
        
        if db.add_pacchetto(nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo):
            flash('Pacchetto creato con successo', 'success')
            return redirect(url_for('lista_pacchetti'))
        else:
            flash('Errore durante la creazione del pacchetto', 'error')
    
    return render_template('pacchetti/nuovo.html')

@app.route('/pacchetti/<int:pacchetto_id>/modifica', methods=['GET', 'POST'])
def modifica_pacchetto(pacchetto_id):
    pacchetto = db.get_pacchetto(pacchetto_id)
    if not pacchetto:
        flash('Pacchetto non trovato', 'error')
        return redirect(url_for('lista_pacchetti'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        descrizione = request.form.get('descrizione')
        prezzo = float(request.form.get('prezzo'))
        numero_lezioni = int(request.form.get('numero_lezioni'))
        durata_giorni = int(request.form.get('durata_giorni'))
        attivo = 'attivo' in request.form
        
        if db.update_pacchetto(pacchetto_id, nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo):
            flash('Pacchetto aggiornato con successo', 'success')
            return redirect(url_for('dettaglio_pacchetto', pacchetto_id=pacchetto_id))
        else:
            flash('Errore durante l\'aggiornamento del pacchetto', 'error')
    
    return render_template('pacchetti/modifica.html', pacchetto=pacchetto)

# --- GESTIONE ABBONAMENTI ---
@app.route('/clienti/<int:cliente_id>/abbonamenti/nuovo', methods=['GET', 'POST'])
def nuovo_abbonamento(cliente_id):
    cliente = db.get_cliente(cliente_id)
    if not cliente:
        flash('Cliente non trovato', 'error')
        return redirect(url_for('lista_clienti'))
    
    if request.method == 'POST':
        pacchetto_id = request.form.get('pacchetto_id', type=int)
        data_inizio = request.form.get('data_inizio')
        prezzo_totale = request.form.get('prezzo_totale', type=float)
        numero_rate = request.form.get('numero_rate', type=int, default=1)
        
        if db.create_abbonamento(cliente_id, pacchetto_id, data_inizio, prezzo_totale, numero_rate):
            flash('Abbonamento creato con successo', 'success')
            return redirect(url_for('dettaglio_cliente', cliente_id=cliente_id))
        else:
            flash('Errore durante la creazione dell\'abbonamento', 'error')
    
    pacchetti = db.get_all_pacchetti()
    return render_template('abbonamenti/nuovo.html', 
                         cliente=cliente, 
                         pacchetti=pacchetti,
                         oggi=datetime.now().strftime('%Y-%m-%d'))

# Add this to your Flask app file where you define your template filters


@app.route('/abbonamenti/<int:abbonamento_id>')
def dettaglio_abbonamento(abbonamento_id):
    abbonamento = db.get_abbonamento(abbonamento_id)
    if not abbonamento:
        flash('Abbonamento non trovato', 'error')
        return redirect(url_for('index'))
    
    cliente = db.get_cliente(abbonamento['cliente_id'])
    rate = db.get_rate_by_abbonamento(abbonamento_id)
    lezioni = db.get_lezioni_by_abbonamento(abbonamento_id)
    oggi = date.today()
    
    return render_template('abbonamenti/dettaglio.html',
                         abbonamento=abbonamento,
                         cliente=cliente,
                         rate=rate,
                         lezioni=lezioni,
                         oggi=oggi)

@app.route('/abbonamenti/<int:abbonamento_id>/registra-lezione', methods=['GET', 'POST'])
def registra_lezione(abbonamento_id):
    # Ottieni l'abbonamento
    abbonamento = db.get_abbonamento(abbonamento_id)
    if not abbonamento:
        flash('Abbonamento non trovato', 'error')
        return redirect(url_for('lista_clienti'))
    
    # Ottieni il cliente
    cliente = db.get_cliente(abbonamento['cliente_id'])
    if not cliente:
        flash('Cliente non trovato', 'error')
        return redirect(url_for('lista_clienti'))
    
    # Verifica se l'abbonamento è ancora valido
    oggi = datetime.now().date()
    data_scadenza = datetime.strptime(abbonamento['data_fine'], '%Y-%m-%d').date()
    
    if data_scadenza < oggi:
        flash('Abbonamento scaduto', 'error')
        return redirect(url_for('dettaglio_cliente', cliente_id=cliente['id']))
    
    # Verifica se ci sono ancora lezioni disponibili
    lezioni_rimanenti = abbonamento['numero_lezioni'] - abbonamento['lezioni_utilizzate']
    if lezioni_rimanenti <= 0:
        flash('Nessuna lezione rimanente', 'error')
        return redirect(url_for('dettaglio_cliente', cliente_id=cliente['id']))
    
    if request.method == 'POST':
        data = request.form.get('data')
        note = request.form.get('note', '')
        
        # Registra la lezione
        if db.registra_lezione(abbonamento_id, data, note):
            flash('Lezione registrata con successo', 'success')
            return redirect(url_for('dettaglio_cliente', cliente_id=cliente['id']))
        else:
            flash('Errore durante la registrazione della lezione', 'error')
    
    return render_template('lezioni/registra.html',
                         cliente=cliente,
                         abbonamento=abbonamento,
                         oggi=oggi.strftime('%Y-%m-%d'))

@app.route('/abbonamenti/<int:abbonamento_id>/nuova-lezione', methods=['GET', 'POST'])
def nuova_lezione(abbonamento_id):
    abbonamento = db.get_abbonamento(abbonamento_id)
    if not abbonamento:
        abort(404)
    
    if request.method == 'POST':
        data = request.form['data']
        ora_inizio = request.form['ora_inizio']
        ora_fine = request.form['ora_fine']
        note = request.form['note']
        
        lezione_id = db.add_lezione(abbonamento_id, data, ora_inizio, ora_fine, note)
        
        flash('Lezione aggiunta con successo!', 'success')
        return redirect(url_for('dettaglio_abbonamento', abbonamento_id=abbonamento_id))
    
    cliente = db.get_cliente(abbonamento['cliente_id'])
    return render_template('abbonamenti/nuova_lezione.html', abbonamento=abbonamento, cliente=cliente)

@app.route('/lezioni/<int:lezione_id>/completa', methods=['POST'])
def completa_lezione(lezione_id):
    db.completa_lezione(lezione_id)
    flash('Lezione completata con successo!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/rate/<int:rata_id>/paga', methods=['GET', 'POST'])
def paga_rata(rata_id):
    rata = db.get_rata(rata_id)
    if not rata:
        flash('Rata non trovata', 'error')
        return redirect(url_for('lista_clienti'))
    
    if rata['pagato']:
        flash('Questa rata è già stata pagata', 'warning')
        return redirect(url_for('dettaglio_abbonamento', abbonamento_id=rata['abbonamento_id']))
    
    if request.method == 'POST':
        data_pagamento = request.form.get('data_pagamento', datetime.now().strftime('%Y-%m-%d'))
        
        if db.registra_pagamento_rata(rata_id, data_pagamento):
            flash('Pagamento registrato con successo', 'success')
            return redirect(url_for('dettaglio_abbonamento', abbonamento_id=rata['abbonamento_id']))
        else:
            flash('Errore durante la registrazione del pagamento', 'error')
    
    return render_template('rate/paga.html', rata=rata)

# --- CALENDARIO E SCADENZIARIO ---
@app.route('/calendario')
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
    
    # Ottieni le scadenze dal database
    scadenze = db.get_rate_calendario(mese, anno)
    scadenze_dict = {}
    
    # Creiamo un dizionario con la data come chiave
    for scadenza in scadenze:
        data = datetime.strptime(scadenza['data_scadenza'], '%Y-%m-%d').date()
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

@app.route('/scadenziario')
def scadenziario():
    rate = db.get_rate_scadenza()
    oggi = date.today()
    return render_template('scadenziario.html', rate=rate, oggi=oggi)

@app.route('/incassi_mese')
def incassi_mese():
    rate = db.get_rate_incassate_mese()
    oggi = date.today()
    return render_template('incassi_mese.html', rate=rate, oggi=oggi)

@app.route('/abbonamenti/<int:abbonamento_id>/elimina', methods=['POST'])
def elimina_abbonamento(abbonamento_id):
    abbonamento = db.get_abbonamento(abbonamento_id)
    if not abbonamento:
        flash('Abbonamento non trovato', 'error')
        return redirect(url_for('index'))
    
    cliente_id = abbonamento['cliente_id']
    
    if db.delete_abbonamento(abbonamento_id):
        flash('Abbonamento eliminato con successo', 'success')
    else:
        flash('Errore durante l\'eliminazione dell\'abbonamento', 'error')
    
    return redirect(url_for('dettaglio_cliente', cliente_id=cliente_id))

# Errori personalizzati
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errori/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errori/500.html'), 500

@app.route('/hierarchy')
def hierarchy():
    user_hierarchy = db.build_hierarchy()
    return render_template('hierarchy.html', hierarchy=user_hierarchy)

@app.route('/update-franchisor/<int:franchisor_id>', methods=['POST'])
@login_required
def update_franchisor_route(franchisor_id):
    nome = request.form['nome']
    email = request.form['email']
    password = request.form['password']
    db.update_franchisor(franchisor_id, nome, email, password)
    flash('Franchisor updated successfully!', 'success')
    return redirect(url_for('hierarchy'))

@app.route('/delete-franchisor/<int:franchisor_id>', methods=['POST'])
@login_required
def delete_franchisor_route(franchisor_id):
    db.delete_franchisor(franchisor_id)
    flash('Franchisor deleted successfully!', 'success')
    return redirect(url_for('hierarchy'))

@app.route('/update-area-manager/<int:area_manager_id>', methods=['POST'])
@login_required
def update_area_manager_route(area_manager_id):
    nome = request.form['nome']
    cognome = request.form['cognome']
    email = request.form['email']
    password = request.form['password']
    db.update_area_manager(area_manager_id, nome, cognome, email, password)
    flash('Area Manager updated successfully!', 'success')
    return redirect(url_for('hierarchy'))

@app.route('/delete-area-manager/<int:area_manager_id>', methods=['POST'])
@login_required
def delete_area_manager_route(area_manager_id):
    db.delete_area_manager(area_manager_id)
    flash('Area Manager deleted successfully!', 'success')
    return redirect(url_for('hierarchy'))

@app.route('/update-company/<int:company_id>', methods=['POST'])
@login_required
def update_company_route(company_id):
    nome = request.form['nome']
    email = request.form['email']
    password = request.form['password']
    db.update_company(company_id, nome, email, password)
    flash('Company updated successfully!', 'success')
    return redirect(url_for('hierarchy'))

@app.route('/delete-company/<int:company_id>', methods=['POST'])
@login_required
def delete_company_route(company_id):
    db.delete_company(company_id)
    flash('Company deleted successfully!', 'success')
    return redirect(url_for('hierarchy'))

@app.route('/update-sede/<int:sede_id>', methods=['POST'])
@login_required
def update_sede_route(sede_id):
    nome = request.form['nome']
    indirizzo = request.form['indirizzo']
    citta = request.form['citta']
    cap = request.form['cap']
    email = request.form['email']
    password = request.form['password']
    db.update_sede(sede_id, nome, indirizzo, citta, cap, email, password)
    flash('Sede updated successfully!', 'success')
    return redirect(url_for('hierarchy'))

@app.route('/delete-sede/<int:sede_id>', methods=['POST'])
@login_required
def delete_sede_route(sede_id):
    db.delete_sede(sede_id)
    flash('Sede deleted successfully!', 'success')
    return redirect(url_for('hierarchy'))

if __name__ == '__main__':
    #db.migrate_database()
    #db.create_user_tables
    db.init_db()
    app.run(debug=True)