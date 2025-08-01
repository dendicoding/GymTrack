import calendar
from collections import OrderedDict
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date, timedelta
from utils.auth import login_required
# ... altri import ...

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/rate_contanti')
@login_required
def rate_contanti():
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

    # Filtro data
    da = request.args.get('da')
    a = request.args.get('a')
    rate = db.get_rate_contanti(sede_ids, da, a)
    oggi = date.today()
    return render_template('rate_contanti.html', rate=rate, oggi=oggi, da=da, a=a)

@stats_bp.route('/incassi_mese')
@login_required
def incassi_mese():
    user_role = session.get('user_role')
    user_email = session.get('user_email')

    societa_id = request.args.get('societa_id')
    sede_id = request.args.get('sede_id')

    # Preselezione dai valori in sessione
    if societa_id is None and sede_id is None:
        societa_id = session.get('societa_id')
        sede_id = session.get('sede_id')

    # Aggiorna la sessione se l'utente cambia filtro
    if request.args.get('societa_id') is not None:
        session['societa_id'] = societa_id
    if request.args.get('sede_id') is not None:
        session['sede_id'] = sede_id

    # Costruisci la gerarchia per i menu a tendina
    societa = []
    sedi = []
    hierarchy = db.build_hierarchy(user_role, user_email)
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

    # Determina i sede_ids da usare per il filtro
    if sede_id:
        sede_ids = [int(sede_id)]
    elif societa_id:
        sedi_societa = db.get_sedi_by_societa(societa_id)
        sede_ids = [sede['id'] for sede in sedi_societa]
    else:
        sede_ids = [sede['id'] for sede in sedi]

    rate = db.get_rate_incassate_mese(sede_ids)
    oggi = date.today()

    return render_template(
        'incassi_mese.html',
        rate=rate,
        oggi=oggi,
        societa=societa,
        sedi=sedi,
        selected_societa_id=str(societa_id) if societa_id else '',
        selected_sede_id=str(sede_id) if sede_id else ''
    )

@stats_bp.route('/statistiche')
@login_required
def statistiche():
    oggi = date.today()
    user_role = session.get('user_role')
    user_email = session.get('user_email')

    # Filtri società/sede
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

    # Costruisci la gerarchia per i menu a tendina
    societa = []
    sedi = []
    hierarchy = db.build_hierarchy(user_role, user_email)
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

    # Determina i sede_ids da usare per il filtro
    if sede_id:
        sede_ids = [int(sede_id)]
    elif societa_id:
        sedi_societa = db.get_sedi_by_societa(societa_id)
        sede_ids = [sede['id'] for sede in sedi_societa]
    else:
        sede_ids = [sede['id'] for sede in sedi]

    # Clienti attivi: hanno almeno un appuntamento da oggi in poi
    appointments = db.get_appointments_by_sedi(sede_ids, oggi.strftime('%Y-%m-%d'))
    print(f"Appointments fetched: {len(appointments)}")
    clienti_attivi_ids = set([a['client_id'] for a in appointments if a['date_time'].date() >= oggi])
    clienti_attivi = [db.get_cliente_completo(cid) for cid in clienti_attivi_ids]

    # Clienti effettivi della sede
    clienti_effettivi = db.get_clienti_effettivi(sede_ids)
    clienti_effettivi_ids = set([c['id'] for c in clienti_effettivi])

    # Clienti non attivi: effettivi che NON hanno appuntamenti da oggi in poi
    clienti_non_attivi_ids = clienti_effettivi_ids - clienti_attivi_ids
    clienti_non_attivi = [db.get_cliente_completo(cid) for cid in clienti_non_attivi_ids]

    mese_inizio = oggi.replace(day=1)
    mese_fine = (mese_inizio + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Pie chart abbonamenti venduti
    abbonamenti_venduti = db.get_abbonamenti_venduti_mese(
        sede_ids,
        mese_inizio.strftime('%Y-%m-%d'),
        mese_fine.strftime('%Y-%m-%d')
    )

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



    appointments_mese = db.get_appointments_by_sedi(
        sede_ids,
        mese_inizio.strftime('%Y-%m-%d'),
        mese_fine.strftime('%Y-%m-%d')
    )
    prove_mese = [a for a in appointments_mese if a.get('is_trial')]

    n_prove_annullate = len([
        a for a in prove_mese
        if a.get('status', '').lower().replace(' ', '_') == 'prova_annullata'
    ])
    n_prove_effettuate = len([
        a for a in prove_mese
        if a.get('status', '').lower().replace(' ', '_') == 'confermato'
    ])

    numero_prove_mese = len(prove_mese)

    clienti_registrati = db.get_clienti_effettivi(sede_ids)
    registrazioni_per_mese = OrderedDict()
    oggi = date.today()
    for i in range(11, -1, -1):
        mese = (oggi.month - i - 1) % 12 + 1
        anno = oggi.year if oggi.month - i > 0 else oggi.year - 1
        key = f"{anno}-{mese:02d}"
        registrazioni_per_mese[key] = 0

    for c in clienti_registrati:
        if isinstance(c['data_registrazione'], (date, datetime.datetime)):            data_reg = c['data_registrazione'].strftime('%Y-%m')
        else:
            data_reg = str(c['data_registrazione'])[:7]
        if data_reg in registrazioni_per_mese:
            registrazioni_per_mese[data_reg] += 1

    mesi_labels = [f"{calendar.month_abbr[int(k[-2:])]} {k[:4]}" for k in registrazioni_per_mese.keys()]
    mesi_values = list(registrazioni_per_mese.values())

    n_rate_contanti = len([r for r in db.get_rate_contanti(sede_ids) if r.get('pagato')])

    upgrades = db.get_abbonamenti_upgrade(
        sede_ids,
        mese_inizio.strftime('%Y-%m-%d'),
        mese_fine.strftime('%Y-%m-%d')
    )
    n_upgrade = len(upgrades)

    rinnovi = db.get_rinnovi_effettuati(
        sede_ids,
        mese_inizio.strftime('%Y-%m-%d'),
        mese_fine.strftime('%Y-%m-%d')
    )
    n_rinnovi = len(rinnovi)

    rinnovi_non = db.get_rinnovi_non_effettuati(
        sede_ids,
        mese_inizio.strftime('%Y-%m-%d'),
        mese_fine.strftime('%Y-%m-%d')
    )
    n_rinnovi_non = len(rinnovi_non)

    return render_template(
        'statistiche.html',
        n_clienti_attivi=len(clienti_attivi),
        clienti_attivi=clienti_attivi,
        n_clienti_non_attivi=len(clienti_non_attivi),
        clienti_non_attivi=clienti_non_attivi,
        abbonamenti_venduti=abbonamenti_venduti,
        n_prove=len(prove),
        numero_prove_mese=numero_prove_mese,
        prove=prove,
        clienti_prove=clienti_prove,
        mesi_labels=mesi_labels,
        mesi_values=mesi_values,
        n_rate_contanti=n_rate_contanti,
        n_prove_annullate=n_prove_annullate,
        n_prove_effettuate=n_prove_effettuate,
        n_upgrade=n_upgrade,
        n_rinnovi=n_rinnovi,
        n_rinnovi_non=n_rinnovi_non,
        societa=societa,
        sedi=sedi,
        selected_societa_id=str(societa_id) if societa_id else '',
        selected_sede_id=str(sede_id) if sede_id else ''
    )

@stats_bp.route('/prove_non_prese')
@login_required
def prove_non_prese():
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

    # Filtro data
    da = request.args.get('da')
    a = request.args.get('a')
    oggi = date.today()
    appointments = db.get_appointments_by_sedi(sede_ids, da, a)    # Filtra solo prove non prese (is_trial=True e status='prova annullata')
    prove_non_prese = [
        a for a in appointments
        if a.get('is_trial') and a.get('status', '').lower().replace(' ', '_') == 'prova_annullata'
    ]
    # Filtra per data se richiesto
    if da:
        da_date = datetime.datetime.strptime(da, '%Y-%m-%d').date()
        prove_non_prese = [p for p in prove_non_prese if p['date_time'].date() >= da_date]
    if a:
        a_date = datetime.datetime.strptime(a, '%Y-%m-%d').date()
        prove_non_prese = [p for p in prove_non_prese if p['date_time'].date() <= a_date]

    return render_template('prove_non_prese.html', prove=prove_non_prese, oggi=oggi, da=da, a=a)

@stats_bp.route('/prove_effettuate')
@login_required
def prove_effettuate():
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

    # Filtro data
    da = request.args.get('da')
    a = request.args.get('a')
    oggi = date.today()
    appointments = db.get_appointments_by_sedi(sede_ids, da, a)
    # Filtra solo prove effettuate (is_trial=True e status='confermato')
    prove_effettuate = [
        a for a in appointments
        if a.get('is_trial') and a.get('status', '').lower().replace(' ', '_') == 'confermato'
    ]
    # Filtra per data se richiesto
    if da:
        da_date = datetime.datetime.strptime(da, '%Y-%m-%d').date()
        prove_effettuate = [p for p in prove_effettuate if p['date_time'].date() >= da_date]
    if a:
        a_date = datetime.datetime.strptime(a, '%Y-%m-%d').date()
        prove_effettuate = [p for p in prove_effettuate if p['date_time'].date() <= a_date]

    return render_template('prove_effettuate.html', prove=prove_effettuate, oggi=oggi, da=da, a=a)

@stats_bp.route('/clienti_attivi')
@login_required
def clienti_attivi():
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

    # Filtro data
    da = request.args.get('da')
    a = request.args.get('a')
    oggi = date.today()
    appointments = db.get_appointments_by_sedi(sede_ids, da or oggi.strftime('%Y-%m-%d'), a)
    clienti_attivi_ids = set([a['client_id'] for a in appointments if a['date_time'].date() >= oggi])
    clienti_attivi = [db.get_cliente_completo(cid) for cid in clienti_attivi_ids]

    return render_template('clienti_attivi.html', clienti=clienti_attivi, oggi=oggi, da=da, a=a)


@stats_bp.route('/prove')
@login_required
def prove():
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

    # Recupera tutti gli appuntamenti prova (is_trial=True)
    appointments = db.get_appointments_by_sedi(sede_ids)
    prove = [a for a in appointments if a.get('is_trial')]

    return render_template('prove.html', prove=prove)

@stats_bp.route('/clienti_non_attivi')
@login_required
def clienti_non_attivi():
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

    oggi = date.today()
    appointments = db.get_appointments_by_sedi(sede_ids, oggi.strftime('%Y-%m-%d'))
    clienti_attivi_ids = set([a['client_id'] for a in appointments if a['date_time'].date() >= oggi])

    clienti_effettivi = db.get_clienti_effettivi(sede_ids)
    clienti_effettivi_ids = set([c['id'] for c in clienti_effettivi])

    clienti_non_attivi_ids = clienti_effettivi_ids - clienti_attivi_ids
    clienti_non_attivi = [db.get_cliente_completo(cid) for cid in clienti_non_attivi_ids]

    return render_template('clienti_non_attivi.html', clienti=clienti_non_attivi)

@stats_bp.route('/upgrade_effettuati')
@login_required
def upgrade_effettuati():
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

    oggi = date.today()
    mese_inizio = oggi.replace(day=1)
    mese_fine = (mese_inizio + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Recupera abbonamenti con data_inizio nel mese corrente e pacchetto 'Upgrade'
    abbonamenti_upgrade = db.get_abbonamenti_upgrade(
        sede_ids,
        mese_inizio.strftime('%Y-%m-%d'),
        mese_fine.strftime('%Y-%m-%d')
    )

    return render_template('upgrade_effettuati.html', upgrade=abbonamenti_upgrade)

@stats_bp.route('/rinnovi_effettuati')
@login_required
def rinnovi_effettuati():
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

    oggi = date.today()
    mese_inizio = oggi.replace(day=1)
    mese_fine = (mese_inizio + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    rinnovi = db.get_rinnovi_effettuati(
        sede_ids,
        mese_inizio.strftime('%Y-%m-%d'),
        mese_fine.strftime('%Y-%m-%d')
    )

    return render_template('rinnovi_effettuati.html', rinnovi=rinnovi)

@stats_bp.route('/rinnovi_non_effettuati')
@login_required
def rinnovi_non_effettuati():
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

    oggi = date.today()
    mese_inizio = oggi.replace(day=1)
    mese_fine = (mese_inizio + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    rinnovi_non = db.get_rinnovi_non_effettuati(
        sede_ids,
        mese_inizio.strftime('%Y-%m-%d'),
        mese_fine.strftime('%Y-%m-%d')
    )

    return render_template('rinnovi_non_effettuati.html', rinnovi=rinnovi_non)