from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from werkzeug.exceptions import NotFound
import database as db
from datetime import datetime, date
import locale
from datetime import datetime, timedelta
from models.abbonamento import Abbonamento
from calendar import monthcalendar
from collections import defaultdict
from flask_wtf.csrf import CSRFProtect


from flask import session, g
from functools import wraps
app = Flask(__name__)
app.secret_key = 'sviluppo_palestra_2025'  # Chiave necessaria per flash messages
# Aggiungi questa configurazione per la sessione
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Inizializzazione del database
db.init_db()

csrf = CSRFProtect(app)

# Set locale for currency formatting (use 'it_IT' for Italian format)
locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')  # Adjust as needed

# Aggiungi questa funzione per il login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Devi effettuare il login per accedere a questa pagina', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Aggiungi alla funzione init_db
@app.before_request
def setup():
    db.init_db()
    db.create_user_tables()
    g.hierarchy = db.build_hierarchy(session.get('user_role'), session.get('user_email'))

# Aggiungi queste route per il login e la registrazione
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Autentica l'utente
        user = db.authenticate_user(email, password)
        print("Utente autenticato:", user)  # Debugging line
        
        if user:
            # Salva i dati dell'utente nella sessione
            session['user_id'] = user['id']
            session['user_name'] = f"{user['nome']} {user['cognome']}"
            session['user_role'] = user['ruolo']
            session['user_email'] = user['email']
            
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
        

            # Create the user in the utenti table

        area_manager_id = db.register_area_manager(franchisor_id, nome, cognome, email, password)
        if area_manager_id:
            flash('Utente ed Area Manager aggiunti con successo!', 'success')
            return redirect(url_for('gestione_gerarchia'))
        else:
            flash('Errore durante la creazione dell\'utente Area Manager', 'error')
  
    
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
    elif user_role == 'area_manager':
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
    stats = db.get_statistiche_dashboard(sede_ids)
    oggi = date.today()
    return render_template('dashboard.html', stats=stats, oggi=oggi)

# --- GESTIONE CLIENTI ---
@app.route('/clienti')
@login_required
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
    elif user_role == 'area_manager':
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

    return render_template('clienti/lista.html', clienti=clienti, titolo=titolo, tipo_attivo=tipo)

@app.route('/clienti/nuovo', methods=['GET', 'POST'])
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
        taglia_giubotto = request.form['taglia_giubotto']
        taglia_cintura = request.form['taglia_cintura']
        taglia_braccia = request.form['taglia_braccia']
        taglia_gambe = request.form['taglia_gambe']
        obiettivo_cliente = request.form['obiettivo_cliente']
        sede_id = request.form['sede_id']
        
        cliente_id = db.add_cliente(nome, cognome, email, telefono, data_nascita, 
                                     indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, sede_id)
        
        db.log_event(session.get('user_id'), session.get('user_email'), 'Aggiunto nuovo cliente', f'Cliente: {nome} {cognome}')
        flash(f'Cliente {nome} {cognome} aggiunto con successo!', 'success')
        return redirect(url_for('dettaglio_cliente', cliente_id=cliente_id))
    
    # Fetch sedi under the logged-in user's hierarchy
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    hierarchy = db.build_hierarchy(user_role=user_role, user_email=user_email)

    sedi = []
    if user_role == 'franchisor':
        for area_manager in hierarchy[0].get('area_managers', []):
            for societa in area_manager.get('societa', []):
                sedi.extend(societa.get('sedi', []))
    elif user_role == 'area_manager':
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

@app.route('/clienti/<int:cliente_id>')
def dettaglio_cliente(cliente_id):
    cliente = db.get_cliente(cliente_id)
    if not cliente:
        flash('Cliente non trovato', 'error')
        return redirect(url_for('lista_clienti'))
    
    abbonamenti = db.get_abbonamenti_by_cliente(cliente_id)
    lezioni = db.get_lezioni_by_cliente(cliente_id)
    
    # Convert rows to dictionaries and fetch the email of the user who registered each lesson
    lezioni = [dict(lezione) for lezione in lezioni]
    for lezione in lezioni:
        print(lezione['registrata_da'])
        lezione['registrata_da'] = db.get_user_email_by_id(lezione['registrata_da'])
    
    oggi = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('clienti/dettaglio.html',
                         cliente=cliente,
                         abbonamenti=abbonamenti,
                         lezioni=lezioni,
                         oggi=oggi)

@app.route('/clienti/<int:cliente_id>/modifica', methods=['GET', 'POST'])
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
        
        return redirect(url_for('dettaglio_cliente', cliente_id=cliente_id))
    
    return render_template('clienti/modifica.html', cliente=cliente)

@app.route('/clienti/<int:cliente_id>/elimina', methods=['POST'])
def elimina_cliente(cliente_id):
    cliente = db.get_cliente(cliente_id)
    if not cliente:
        abort(404)
    
    db.delete_cliente(cliente_id)
    db.log_event(session.get('user_id'), session.get('user_email'), 'Eliminato cliente', f'Cliente ID: {cliente_id}')
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
        # Recupera i dati dal form
        nome = request.form.get('nome')
        descrizione = request.form.get('descrizione')
        prezzo = request.form.get('prezzo', type=float)
        numero_lezioni = request.form.get('numero_lezioni', type=int)
        durata_giorni = request.form.get('durata_giorni', type=int)
        attivo = 'attivo' in request.form
        pagamento_unico = 'pagamento_unico' in request.form

        # Aggiungi il pacchetto al database
        try:
            db.add_pacchetto(nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo, pagamento_unico)
            flash('Pacchetto aggiunto con successo!', 'success')
            return redirect(url_for('lista_pacchetti'))
        except Exception as e:
            flash(f'Errore durante l\'aggiunta del pacchetto: {e}', 'danger')

    # In caso di richiesta GET o errore, mostra il form
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
        pagamento_unico = 'pagamento_unico' in request.form
        
        if db.update_pacchetto(pacchetto_id, nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo, pagamento_unico):
            db.log_event(session.get('user_id'), session.get('user_email'), 'Modificato pacchetto', f'Pacchetto ID: {pacchetto_id}')
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

@app.route('/abbonamenti/<int:abbonamento_id>/registra-lezione', methods=['GET', 'POST'])
@login_required
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
        user_id = session.get('user_id')
        
        # Registra la lezione
        if db.add_lezione(abbonamento_id, data, note, user_id):
            db.log_event(session.get('user_id'), session.get('user_email'), 'Registrata lezione', f'Abbonamento ID: {abbonamento_id}')
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
        note = request.form['note']
        user_email = session.get('user_email')  # Get the current user's email
        
        lezione_id = db.add_lezione(abbonamento_id, data, note, user_email)
        
        flash('Lezione aggiunta con successo!', 'success')
        return redirect(url_for('dettaglio_abbonamento', abbonamento_id=abbonamento_id))
    
    cliente = db.get_cliente(abbonamento['cliente_id'])
    return render_template('abbonamenti/nuova_lezione.html', abbonamento=abbonamento, cliente=cliente)

@app.route('/lezioni/<int:lezione_id>/completa', methods=['POST'])
def completa_lezione(lezione_id):
    db.completa_lezione(lezione_id)
    flash('Lezione completata con successo!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/rate/<int:rata_id>/modifica', methods=['GET', 'POST'])
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

        return redirect(url_for('dettaglio_abbonamento', abbonamento_id=rata['abbonamento_id']))

    return render_template('rate/modifica_rata.html', rata=rata)

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
        metodo_pagamento = request.form.get('metodo_pagamento')
        importo_pagato = float(request.form.get('importo_pagato'))
        pagamento_parziale = 'pagamento_parziale' in request.form
        
        if importo_pagato < rata['importo'] and pagamento_parziale:
            importo_rimanente = rata['importo'] - importo_pagato
            nuova_data_scadenza = (datetime.strptime(rata['data_scadenza'], '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
            
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
        
        return redirect(url_for('dettaglio_abbonamento', abbonamento_id=rata['abbonamento_id']))
    
    return render_template('rate/paga.html', rata=rata)

# --- CALENDARIO E SCADENZIARIO ---
@app.route('/calendario')
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
    elif user_role == 'area_manager':
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
    elif user_role == 'area_manager':
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

@app.route('/incassi_mese')
@login_required
def incassi_mese():
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    # Fetch sede_ids based on user role
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
    elif user_role == 'area_manager':
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

    rate = db.get_rate_incassate_mese(sede_ids)
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
        db.log_event(session.get('user_id'), session.get('user_email'), 'Eliminato abbonamento', f'Abbonamento ID: {abbonamento_id}')
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
@login_required
def hierarchy():
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    user_hierarchy = db.build_hierarchy(user_role=user_role, user_email=user_email)
    if not user_hierarchy:
        flash('Non ci sono dati disponibili per la tua gerarchia.', 'info')
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
    indirizzo = request.form['indirizzo']
    provincia = request.form['provincia']
    comune = request.form['comune']
    db.update_company(company_id, nome, email, password, indirizzo, provincia, comune)
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

@app.route('/all-utenti')
@login_required
def all_utenti():
    utenti = db.get_all_utenti()
    return render_template('all_data.html', utenti=utenti)

@app.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user_route(user_id):
    db.delete_user(user_id)  # You need to implement this function in database.py
    flash('User deleted successfully!', 'success')
    return redirect(url_for('all_utenti'))

@app.route('/add-trainer', methods=['GET', 'POST'])
@login_required
def add_trainer():
    # Check if the user has the correct role to add a trainer
    #if session.get('user_role') != 'societa':
        #flash('Non hai i permessi per aggiungere un trainer', 'error')
        #return redirect(url_for('index'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        cognome = request.form['cognome']
        email = request.form['email']
        password = request.form['password']
        sede_id = request.form['sede_id']  # Assuming you have a way to get the sede_id
        
        trainer_id = db.register_trainer(sede_id, nome, cognome, email, password)
        if trainer_id:
            flash('Trainer aggiunto con successo!', 'success')
            return redirect(url_for('gestione_gerarchia'))  # Redirect to the hierarchy management page
        else:
            flash('Errore durante l\'aggiunta del trainer', 'error')
    
    # Render the form for adding a trainer
    return render_template('auth/add_trainer.html')  # Create this template for the form


@app.route('/update-trainer/<int:trainer_id>', methods=['POST'])
@login_required
def update_trainer_route(trainer_id):
    nome = request.form['nome']
    cognome = request.form['cognome']
    email = request.form['email']
    password = request.form['password']
    db.update_trainer(trainer_id, nome, cognome, email, password)
    flash('Trainer updated successfully!', 'success')
    return redirect(url_for('gestione_gerarchia'))  # Redirect to the hierarchy management page

@app.route('/delete-trainer/<int:trainer_id>', methods=['POST'])
@login_required
def delete_trainer_route(trainer_id):
    db.delete_trainer(trainer_id)
    flash('Trainer deleted successfully!', 'success')
    return redirect(url_for('gestione_gerarchia'))  # Redirect to the hierarchy management page

@app.route('/eventi')
@login_required
def lista_eventi():
    eventi = db.get_all_eventi()
    return render_template('eventi/lista.html', eventi=eventi)

@app.route('/trainer/attendance', methods=['GET'])
@login_required
def trainer_attendance():
    if session.get('user_role') != 'trainer':
        abort(403)
    trainer_id = session.get('user_id')
    
    is_present = db.is_trainer_present(trainer_id)
    print(is_present)
    return render_template('trainer_attendance.html', is_present=is_present)

@app.route('/trainer/entrata', methods=['POST'])
@login_required
def trainer_entrata():
    if session.get('user_role') != 'trainer':
        abort(403)
    trainer_id = session.get('user_id')
    db.log_event(trainer_id, session.get('user_email'), 'entra', 'Trainer entrato')
    flash('Entrata registrata con successo!', 'success')
    return redirect(url_for('trainer_attendance'))

@app.route('/trainer/uscita', methods=['POST'])
@login_required
def trainer_uscita():
    if session.get('user_role') != 'trainer':
        abort(403)
    trainer_id = session.get('user_id')
    db.log_event(trainer_id, session.get('user_email'), 'esci', 'Trainer uscito')
    flash('Uscita registrata con successo!', 'success')
    return redirect(url_for('trainer_attendance'))

@app.route('/trainer-status')
@login_required
def trainer_status():
    user_role = session.get('user_role')
    user_email = session.get('user_email')

    # Fetch sede_ids based on user role
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
    elif user_role == 'area_manager':
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

    # Fetch trainers and their status
    trainers = db.get_trainers_with_status(sede_ids)
    print(trainers)
    return render_template('trainer_status.html', trainers=trainers)

@app.route('/trainer/resoconto', methods=['GET', 'POST'])
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
        trainer_id = session.get('user_id')
        
        db.add_resoconto(trainer_id, data, ore_lavoro, ore_buca, attivita_buca)
        flash('Resoconto dichiarato con successo!', 'success')
        return redirect(url_for('trainer_resoconto'))
    
    return render_template('trainer/resoconto.html')

@app.route('/trainers', methods=['GET'])
@login_required
def view_trainers():
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    
    # Fetch sede_ids based on user role
    sede_ids = []
    if user_role == 'sede':
        sede = db.get_sede_by_email(user_email)
        if sede:
            sede_ids.append(sede['id'])
    elif user_role == 'societa':
        societa = db.get_societa_by_email(user_email)
        if societa:
            sedi = db.get_sedi_by_societa(societa['id'])
            sede_ids.extend([sede['id'] for sede in sedi])
    elif user_role == 'area_manager':
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

    sede_ids = [sede_id for sede_id in sede_ids if sede_id is not None]
    trainers = db.get_trainers_with_status(sede_ids)
    return render_template('trainer/view_trainers.html', trainers=trainers)

@app.route('/trainer/<int:trainer_id>/resoconti', methods=['GET'])
@login_required
def trainer_resoconti(trainer_id):
    resoconti = db.get_resoconti_by_trainer(trainer_id)
    return render_template('trainer/resoconti.html', resoconti=resoconti)

@app.route('/trainer/resoconto/<int:resoconto_id>', methods=['GET'])
@login_required
def view_resoconto(resoconto_id):
    resoconto = db.get_resoconto(resoconto_id)
    if not resoconto:
        flash('Resoconto non trovato', 'error')
        return redirect(url_for('view_trainers'))
    return render_template('trainer/view_resoconto.html', resoconto=resoconto)


@app.route('/trainer/calendar', methods=['GET'])
@login_required
def trainer_calendar():
    if session.get('user_role') != 'trainer':
        abort(403)
    
    # Step 1: Get the logged-in trainer's email
    trainer_email = session.get('user_email')

    # Step 2: Find the user ID of the logged-in trainer
    logged_in_user = db.get_user_by_email(trainer_email)
    if not logged_in_user:
        flash('Errore: utente non trovato.', 'error')
        return redirect(url_for('index'))
    logged_in_user_id = logged_in_user['id']

    # Step 3: Fetch the `sede` associated with the logged-in trainer
    sede = db.get_sede_by_trainer_email(trainer_email)
    if not sede:
        flash('Errore: sede non trovata.', 'error')
        return redirect(url_for('index'))
    
    # Step 4: Fetch all trainers in the same `sede`
    trainers_in_sede = db.get_trainers_by_sede(sede['id'])
    
    # Step 5: Get the user IDs linked to these trainers
    user_ids = [db.get_user_by_email(trainer['email'])['id'] for trainer in trainers_in_sede]

    # Get the start date for the calendar (default to today)
    start_date = request.args.get('start_date', date.today().strftime('%Y-%m-%d'))

    # Fetch appointments for all user IDs in the same `sede`
    appointments = db.get_appointments_by_users(user_ids, start_date)

    # Group appointments by date
    grouped_appointments = defaultdict(list)
    for appointment in appointments:
        appointment_date = appointment['date_time'].date()
        grouped_appointments[appointment_date].append(appointment)

    # Render the calendar template
    return render_template(
        'trainer/calendar.html',
        current_date=datetime.strptime(start_date, '%Y-%m-%d'),
        timedelta=timedelta,
        date=date,
        grouped_appointments=grouped_appointments
    )


@app.route('/trainer/appointment/new', methods=['GET', 'POST'])
@login_required
def add_appointment():
    if session.get('user_role') != 'trainer':
        abort(403)

    trainer_id = session.get('user_id')
    sede = db.get_sede_by_trainer_email(session.get('user_email'))
    if not sede:
        flash('Errore: sede non trovata.', 'error')
        return redirect(url_for('index'))

    clienti = db.get_clienti_effettivi([sede['id']])

    # Precompila la data e ora se fornita nella query string
    prefilled_date_time = request.args.get('date_time', '')

    if request.method == 'POST':
        client_id = request.form['client_id']
        title = request.form['title']
        notes = request.form['notes']
        date_time = datetime.strptime(request.form['date_time'], '%Y-%m-%dT%H:%M')
        end_date_time = datetime.strptime(request.form['end_date_time'], '%Y-%m-%dT%H:%M')
        appointment_type = request.form['appointment_type']
        status = request.form['status']
        is_trial = 'is_trial' in request.form
        is_recovery = 'is_recovery' in request.form
        is_lesson_zero = 'is_lesson_zero' in request.form
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
                        trainer_id, client_id, title, notes, current_date, recurring_end_time,
                        appointment_type, status, is_trial, is_recovery, is_lesson_zero
                    )
                current_date += timedelta(days=1)
            flash('Appuntamenti ripetuti creati con successo!', 'success')
        else:
            db.add_appointment(
                trainer_id, client_id, title, notes, date_time, end_date_time,
                appointment_type, status, is_trial, is_recovery, is_lesson_zero
            )
            flash('Appuntamento creato con successo!', 'success')

        return redirect(url_for('trainer_calendar'))

    return render_template('trainer/add_appointment.html', clienti=clienti, prefilled_date_time=prefilled_date_time)

@app.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    if session.get('user_role') != 'trainer':
        abort(403)
    
    appointment = db.get_appointment_by_id(appointment_id)
    
    if not appointment:
        flash('Appuntamento non trovato', 'danger')
        return redirect(url_for('trainer_calendar'))
    
    if appointment['trainer_id'] != session.get('user_id'):
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
        return redirect(url_for('trainer_calendar'))
    
    # Per il metodo GET, mostra il form di modifica
    clients = db.get_all_clienti()
    return render_template(
        'trainer/edit_appointment.html',
        appointment=appointment,
        clients=clients
    )

@app.route('/delete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    print("CSRF Token ricevuto:", request.headers.get('X-CSRFToken'))

    if session.get('user_role') != 'trainer':
        flash('Non hai i permessi per eliminare questo appuntamento.', 'error')
        return redirect(url_for('trainer_calendar'))

    appointment = db.get_appointment_by_id(appointment_id)
    print(appointment)
    if not appointment:
        flash('Appuntamento non trovato.', 'error')
        return redirect(url_for('trainer_calendar'))

    if appointment['trainer_id'] != session.get('user_id'):
        flash('Non sei autorizzato a eliminare questo appuntamento.', 'error')
        return redirect(url_for('trainer_calendar'))

    if db.delete_appointment(appointment_id):
        flash('Appuntamento eliminato con successo.', 'success')
    else:
        flash('Errore durante l\'eliminazione dell\'appuntamento.', 'error')

    return redirect(url_for('trainer_calendar'))

from flask_wtf.csrf import generate_csrf

@app.context_processor
def inject_csrf_token():
    return dict(csrf=generate_csrf())

@app.after_request
def set_csrf_cookie(response):
    response.set_cookie('csrf_token', generate_csrf())
    return response

if __name__ == '__main__':
    #db.migrate_database()
    #db.create_user_tables
    #db.init_db()
    db.create_appointments_table()
    db.migrate_appointments_table()
    app.run(debug=True)