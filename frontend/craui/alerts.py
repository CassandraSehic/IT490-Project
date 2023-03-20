import json
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from .auth import login_required
from .fermq import get_alerts, set_alert, delete_alert

bp = Blueprint('alerts', __name__)

@bp.route('/')
def index():
    user_email = session.get('user_email')
    if user_email is None:
        return render_template('index.html')
    else:
        user_alerts = json.loads(get_alerts(user_email))
        return render_template('alerts/index.html', alerts=user_alerts)

@bp.route('/set', methods=('POST',))
@login_required
def set_a():
    user_email = session.get('user_email')
    numerator = request.form['numerator']
    denominator = request.form['denominator']
    treshold = request.form['treshold']
    set_alert(user_email, numerator, denominator, treshold)
    return redirect(url_for('alerts.index'))

@bp.route('/delete/<numerator>/<denominator>/<treshold>', methods=('POST',))
@login_required
def delete_a(numerator, denominator, treshold):
    user_email = session.get('user_email')
    delete_alert(user_email, numerator, denominator, treshold)
    return redirect(url_for('alerts.index'))