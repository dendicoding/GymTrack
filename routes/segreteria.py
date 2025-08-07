from flask import Blueprint, abort, jsonify, render_template, request, redirect, url_for, flash, session
import database as db
from datetime import datetime, timedelta

segreteria_bp = Blueprint('segreteria', __name__)

@segreteria_bp.route('/segreteria/crea', methods=['GET', 'POST'])
def crea_segreteria():
    if request.method == 'POST':
        nome = request.form['nome']
        cognome = request.form['cognome']
        email = request.form['email']
        password = request.form['password']
        # Usa la funzione generica per creare utenti
        db.create_user(db.get_db_connection().cursor(), nome, cognome, email, password, 'segreteria')
        flash('Utente segreteria creato con successo!', 'success')
        return redirect(url_for('segreteria.lista_segreteria'))
    return render_template('segreteria/crea.html')




@segreteria_bp.route('/segreteria/eventi')
def eventi_segreteria():
    if session.get('user_role') != 'area manager':
        abort(403)
    user_email = session.get('user_email')
    # Recupera le sedi gestite dall'area manager
    societa = db.get_societa_by_area_manager_email(user_email)
    sedi_ids = []
    for soc in societa:
        sedi = db.get_sedi_by_societa(soc['id'])
        sedi_ids.extend([s['id'] for s in sedi])
    # Recupera eventi relativi a queste sedi
    eventi = db.get_eventi_segreteria(sedi_ids)
    return render_template('segreteria/eventi.html', eventi=eventi)


@segreteria_bp.route('/segreteria/eventi/nuovi')
def eventi_segreteria_nuovi():
    if session.get('user_role') != 'area manager':
        return jsonify({'nuovi_eventi': []})
        
    user_email = session.get('user_email')
    minuti = int(request.args.get('minuti', 5))
    cutoff = (datetime.now() - timedelta(minutes=minuti)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Recupera le sedi gestite dall'area manager (stessa logica di eventi_segreteria)
    societa = db.get_societa_by_area_manager_email(user_email)
    sedi_ids = []
    for soc in societa:
        sedi = db.get_sedi_by_societa(soc['id'])
        sedi_ids.extend([s['id'] for s in sedi])
    
    # Recupera solo gli eventi relativi a queste sedi e recenti
    eventi = db.get_eventi_segreteria(sedi_ids)
    nuovi_eventi = [
        e for e in eventi 
        if e['azione'] in ['spostamento appuntamento', 'modifica appuntamento', 'entra', 'esci']
        and str(e['data_evento']) >= cutoff
    ]
    
    return jsonify({'nuovi_eventi': nuovi_eventi})