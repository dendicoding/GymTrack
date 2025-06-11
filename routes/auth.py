import calendar
from collections import OrderedDict
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date
from utils.auth import login_required
# ... altri import ...

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
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

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logout effettuato con successo', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = request.form['password']
        
        franchisor_id = db.register_franchisor(nome, email, password)
        
        if franchisor_id:
            flash('Registrazione completata con successo!', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Errore durante la registrazione', 'error')
    
    return render_template('auth/register.html')