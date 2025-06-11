import calendar
from collections import OrderedDict
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date
from utils.auth import login_required
# ... altri import ...

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/incassi_mese')
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

    rate = db.get_rate_incassate_mese(sede_ids)
    oggi = date.today()
    return render_template('incassi_mese.html', rate=rate, oggi=oggi)


@stats_bp.route('/statistiche')
@login_required
def statistiche():
    oggi = date.today()
    # Recupera tutte le sedi sotto la gerarchia dell'utente
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
        for manager in area_managers:
            societa = db.get_societa_by_area_manager(manager['id'])
            for company in societa:
                sedi.extend(db.get_sedi_by_societa(company['id']))

    sede_ids = [sede['id'] for sede in sedi if sede and 'id' in sede]

    # Clienti attivi: hanno almeno un appuntamento da oggi in poi
    appointments = db.get_appointments_by_sedi(sede_ids, oggi.strftime('%Y-%m-%d'))
    clienti_attivi_ids = set([a['client_id'] for a in appointments if a['date_time'].date() >= oggi])
    clienti_attivi = [db.get_cliente(cid) for cid in clienti_attivi_ids]

    # Clienti effettivi della sede
    clienti_effettivi = db.get_clienti_effettivi(sede_ids)
    clienti_effettivi_ids = set([c['id'] for c in clienti_effettivi])

    # Clienti non attivi: effettivi che NON hanno appuntamenti da oggi in poi
    clienti_non_attivi_ids = clienti_effettivi_ids - clienti_attivi_ids
    clienti_non_attivi = [db.get_cliente(cid) for cid in clienti_non_attivi_ids]

    # Pie chart abbonamenti venduti
    abbonamenti = db.get_all_pacchetti()
    abbonamenti_venduti = {}
    for ab in abbonamenti:
        nome = ab['nome']
        count = db.get_abbonamenti_by_pacchetto(ab['id'])
        abbonamenti_venduti[nome] = len(count)

    # Appuntamenti di prova (is_trial)
    prove = [a for a in appointments if a.get('is_trial')]
    clienti_prove = []
    for p in prove:
        cliente = db.get_cliente(p['client_id'])
        clienti_prove.append({
            'cliente': f"{cliente['nome']} {cliente['cognome']}" if cliente else 'N/D',
            'data': p['date_time'],
            'note': p.get('notes', ''),
            'stato': p.get('status', ''),
        })

    

    clienti_registrati = db.get_clienti_effettivi(sede_ids)
    registrazioni_per_mese = OrderedDict()
    oggi = date.today()
    for i in range(11, -1, -1):
        mese = (oggi.month - i - 1) % 12 + 1
        anno = oggi.year if oggi.month - i > 0 else oggi.year - 1
        key = f"{anno}-{mese:02d}"
        registrazioni_per_mese[key] = 0

    for c in clienti_registrati:
        data_reg = c['data_registrazione'][:7]  # 'YYYY-MM'
        if data_reg in registrazioni_per_mese:
            registrazioni_per_mese[data_reg] += 1

    mesi_labels = [f"{calendar.month_abbr[int(k[-2:])]} {k[:4]}" for k in registrazioni_per_mese.keys()]
    mesi_values = list(registrazioni_per_mese.values())

    return render_template(
        'statistiche.html',
        n_clienti_attivi=len(clienti_attivi),
        clienti_attivi=clienti_attivi,
        n_clienti_non_attivi=len(clienti_non_attivi),
        clienti_non_attivi=clienti_non_attivi,
        abbonamenti_venduti=abbonamenti_venduti,
        n_prove=len(prove),
        prove=prove,
        clienti_prove=clienti_prove,
        mesi_labels=mesi_labels,
        mesi_values=mesi_values
    )
