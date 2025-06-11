from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
import database as db
from datetime import date, datetime
from utils.auth import login_required
from flask_wtf.csrf import generate_csrf
from werkzeug.exceptions import NotFound


# ... altri import ...

utils_bp = Blueprint('utils', __name__)

# Errori personalizzati
@utils_bp.errorhandler(404)
def page_not_found(e):
    return render_template('errori/404.html'), 404

@utils_bp.errorhandler(500)
def server_error(e):
    return render_template('errori/500.html'), 500

@utils_bp.context_processor
def inject_csrf_token():
    return dict(csrf=generate_csrf())

@utils_bp.after_request
def set_csrf_cookie(response):
    response.set_cookie('csrf_token', generate_csrf())
    return response




