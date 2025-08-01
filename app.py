from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
from werkzeug.exceptions import NotFound
import database as db
from datetime import datetime, date
import locale
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from routes import blueprints
from utils.auth import login_required
from waitress import serve

app = Flask(__name__)
app.secret_key = 'sviluppo_palestra_2025'  # Chiave necessaria per flash messages
# Aggiungi questa configurazione per la sessione
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Inizializzazione del database
#db.init_db()

csrf = CSRFProtect(app)

# Set locale for currency formatting (use 'it_IT' for Italian format)
try:
    locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')



# Aggiungi alla funzione init_db
@app.before_request
def setup():
    #db.init_db()
    #db.create_user_tables()
    g.hierarchy = db.build_hierarchy(session.get('user_role'), session.get('user_email'))
    #print("HIERARCHY:", g.hierarchy)





# Route principale e dashboard
@app.route('/')
@login_required
def index():
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    user_ids = []
    sede_ids = []

    # Recupera i filtri dalla query string, altrimenti dalla sessione
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

    hierarchy = db.build_hierarchy(user_role, user_email)
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

    # Determina i sede_ids da usare per le statistiche
    if sede_id:
        sede_ids = [int(sede_id)]
    elif societa_id:
        sedi_societa = db.get_sedi_by_societa(societa_id)
        sede_ids = [sede['id'] for sede in sedi_societa]
    else:
        sede_ids = [sede['id'] for sede in sedi]

    # Recupera gli user_ids dei trainer associati alle sedi selezionate
    for sid in sede_ids:
        trainers_in_sede = db.get_trainers_by_sede(sid)
        for trainer in trainers_in_sede:
            user = db.get_user_by_email(trainer['email'])
            if user:
                user_ids.append(user['id'])

    sede_ids = [sid for sid in sede_ids if sid is not None]
    stats = db.get_statistiche_dashboard(sede_ids)
    oggi = date.today()

    # Appuntamenti di oggi
    appointments_today = []
    if user_ids:
        appointments = db.get_appointments_by_users(user_ids, oggi.strftime('%Y-%m-%d'))
        appointments_today = [a for a in appointments if a['date_time'].date() == oggi]

    nome_societa_corrente = db.get_nome_societa_by_id(societa_id) if societa_id else None
    nome_sede_corrente = db.get_nome_sede_by_id(sede_id) if sede_id else None

    return render_template(
        'dashboard.html',
        stats=stats,
        oggi=oggi,
        appointments_today=appointments_today,
        user_role=user_role,
        user_email=user_email,
        societa=societa,
        sedi=sedi,
        selected_societa_id=str(societa_id) if societa_id else '',
        selected_sede_id=str(sede_id) if sede_id else '',
        nome_societa_corrente=nome_societa_corrente,
        nome_sede_corrente=nome_sede_corrente
    )


@app.context_processor
def inject_societa_sede_names():
    societa_id = session.get('societa_id')
    sede_id = session.get('sede_id')
    nome_societa_corrente = db.get_nome_societa_by_id(societa_id) if societa_id else None
    nome_sede_corrente = db.get_nome_sede_by_id(sede_id) if sede_id else None
    return dict(
        nome_societa_corrente=nome_societa_corrente,
        nome_sede_corrente=nome_sede_corrente
    )

@app.route('/eventi')
@login_required
def lista_eventi():
    eventi = db.get_all_eventi()
    return render_template('eventi/lista.html', eventi=eventi)



@app.template_filter('month_name')
def month_name_filter(month_number):
    mesi = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
            'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    return mesi[month_number - 1]

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
    if isinstance(date_str, datetime):
        return date_str.date()
    if isinstance(date_str, date):
        return date_str
    return datetime.strptime(str(date_str), '%Y-%m-%d').date()

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


# Registra tutti i blueprint
for bp in blueprints:
    app.register_blueprint(bp)

from flask_wtf.csrf import CSRFError

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash("La sessione è scaduta o la pagina è rimasta aperta troppo a lungo. Effettua nuovamente il login.", "danger")
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    with app.app_context():
    #with app.app_context():
    #db.migrate_database()
    #db.create_user_tables
    #db.init_db()
    #db.migrate_appointments_table()
        db.ensure_minimum_hierarchy()
        app.run(host='0.0.0.0', port=5000)