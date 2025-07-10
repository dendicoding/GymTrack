from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date
from utils.auth import login_required
# ... altri import ...

gerarchie_bp = Blueprint('gerarchie', __name__)

#GERARCHIA
@gerarchie_bp.route('/gestione-gerarchia')
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

#GERARCHIA

@gerarchie_bp.route('/add-area-manager', methods=['GET', 'POST'])
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

        area_manager_id = db.register_area_manager(nome, cognome, email, password, franchisor_id)
        if area_manager_id:
            flash('Utente ed Area Manager aggiunti con successo!', 'success')
            return redirect(url_for('gerarchie.hierarchy'))
        else:
            flash('Errore durante la creazione dell\'utente Area Manager', 'error')
  
    
    return render_template('auth/add_area_manager.html')

#GERARCHIA
@gerarchie_bp.route('/add-societa', methods=['GET', 'POST'])
@login_required
def add_societa():
    
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = request.form['password']
        area_manager_id = request.form['area_manager_id']
        
        societa_id = db.register_societa(area_manager_id, nome, email, password)
        if societa_id:
            flash('Società aggiunta con successo!', 'success')
            return redirect(url_for('gerarchie.hierarchy'))
        else:
            flash('Errore durante l\'aggiunta della Società', 'error')
    
    return render_template('auth/add_societa.html')

#GERARCHIA
@gerarchie_bp.route('/add-sede', methods=['GET', 'POST'])
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
            return redirect(url_for('gerarchie.hierarchy'))
        else:
            flash('Errore durante l\'aggiunta della Sede', 'error')
    
    return render_template('auth/add_sede.html')

@gerarchie_bp.route('/hierarchy')
@login_required
def hierarchy():
    user_role = session.get('user_role')
    user_email = session.get('user_email')
    user_hierarchy = db.build_hierarchy(user_role=user_role, user_email=user_email)
    if not user_hierarchy:
        flash('Non ci sono dati disponibili per la tua gerarchia.', 'info')
    return render_template('hierarchy.html', hierarchy=user_hierarchy)

@gerarchie_bp.route('/update-franchisor/<int:franchisor_id>', methods=['POST'])
@login_required
def update_franchisor_route(franchisor_id):
    nome = request.form['nome']
    email = request.form['email']
    password = request.form['password']
    db.update_franchisor(franchisor_id, nome, email, password)
    flash('Franchisor updated successfully!', 'success')
    return redirect(url_for('gerarchie.hierarchy'))

@gerarchie_bp.route('/delete-franchisor/<int:franchisor_id>', methods=['POST'])
@login_required
def delete_franchisor_route(franchisor_id):
    db.delete_franchisor(franchisor_id)
    flash('Franchisor deleted successfully!', 'success')
    return redirect(url_for('gerarchie.hierarchy'))

@gerarchie_bp.route('/update-area-manager/<int:area_manager_id>', methods=['POST'])
@login_required
def update_area_manager_route(area_manager_id):
    nome = request.form['nome']
    cognome = request.form['cognome']
    email = request.form['email']
    password = request.form['password']
    db.update_area_manager(area_manager_id, nome, cognome, email, password)
    flash('Area Manager updated successfully!', 'success')
    return redirect(url_for('gerarchie.hierarchy'))

@gerarchie_bp.route('/delete-area-manager/<int:area_manager_id>', methods=['POST'])
@login_required
def delete_area_manager_route(area_manager_id):
    result = db.delete_area_manager(area_manager_id)
    if result:
        flash('Area manager eliminato con successo!', 'success')
    # Se fallisce, il messaggio di errore è già stato flashato dalla funzione delete_area_manager
    return redirect(url_for('gerarchie.hierarchy'))

@gerarchie_bp.route('/update-company/<int:company_id>', methods=['POST'])
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
    return redirect(url_for('gerarchie.hierarchy'))

@gerarchie_bp.route('/delete-company/<int:company_id>', methods=['POST'])
@login_required
def delete_company_route(company_id):
    result = db.delete_company(company_id)
    if result:
        flash('Company deleted successfully!', 'success')
    # Se la funzione ritorna False, il messaggio di errore è già stato flashato da delete_company
    return redirect(url_for('gerarchie.hierarchy'))

@gerarchie_bp.route('/update-sede/<int:sede_id>', methods=['POST'])
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
    return redirect(url_for('gerarchie.hierarchy'))

@gerarchie_bp.route('/delete-sede/<int:sede_id>', methods=['POST'])
@login_required
def delete_sede_route(sede_id):
    result = db.delete_sede(sede_id)
    if result:
        flash('Sede eliminata con successo!', 'success')
    # Se fallisce, il messaggio di errore è già stato flashato dalla funzione delete_sede
    return redirect(url_for('gerarchie.hierarchy'))

@gerarchie_bp.route('/all-utenti')
@login_required
def all_utenti():
    utenti = db.get_all_utenti()
    return render_template('all_data.html', utenti=utenti)

@gerarchie_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user_route(user_id):
    db.delete_user(user_id)  
    flash('User deleted successfully!', 'success')
    return redirect(url_for('all_utenti'))

@gerarchie_bp.route('/add-trainer', methods=['GET', 'POST'])
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
            return redirect(url_for('gerarchie.hierarchy'))  # Redirect to the hierarchy management page
        else:
            flash('Errore durante l\'aggiunta del trainer', 'error')
    
    # Render the form for adding a trainer
    return render_template('auth/add_trainer.html')  # Create this template for the form


@gerarchie_bp.route('/update-trainer/<int:trainer_id>', methods=['POST'])
@login_required
def update_trainer_route(trainer_id):
    nome = request.form['nome']
    cognome = request.form['cognome']
    email = request.form['email']
    password = request.form['password']
    db.update_trainer(trainer_id, nome, cognome, email, password)
    flash('Trainer updated successfully!', 'success')
    return redirect(url_for('gerarchie.hierarchy'))  # Redirect to the hierarchy management page

@gerarchie_bp.route('/delete-trainer/<int:trainer_id>', methods=['POST'])
@login_required
def delete_trainer_route(trainer_id):
    db.delete_trainer(trainer_id)
    flash('Trainer deleted successfully!', 'success')
    return redirect(url_for('gerarchie.hierarchy'))  # Redirect to the hierarchy management page