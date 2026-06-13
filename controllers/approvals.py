from flask import Blueprint, render_template, session, redirect, url_for

approvals_bp = Blueprint('approvals', __name__)

@approvals_bp.route('/approvals')
def approvals_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('approvals.html', user=session['user'])
