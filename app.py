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

app = Flask(__name__)
app.secret_key = 'sviluppo_palestra_2025'  # Chiave necessaria per flash messages
# Aggiungi questa configurazione per la sessione
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Inizializzazione del database
db.init_db()

csrf = CSRFProtect(app)

# Set locale for currency formatting (use 'it_IT' for Italian format)
locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')  # Adjust as needed

# Aggiungi alla funzione init_db
@app.before_request
def setup():
    db.init_db()
    db.create_user_tables()
    g.hierarchy = db.build_hierarchy(session.get('user_role'), session.get('user_email'))

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
    stats = db.get_statistiche_dashboard(sede_ids)
    oggi = date.today()
    return render_template('dashboard.html', stats=stats, oggi=oggi)


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
    if not date_str:
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()

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

if __name__ == '__main__':
    db.migrate_database()
    #db.create_user_tables
    #db.init_db()
    #db.migrate_appointments_table()
    app.run(debug=True)