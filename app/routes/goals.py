"""
Goals Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from app.extensions import db
from app.models import Goal

goals_bp = Blueprint('goals', __name__, url_prefix='/goals')

GOAL_COLORS = ['#6c63ff', '#00d4a8', '#ffa502', '#ff4757', '#2ed573', '#1e90ff', '#eccc68']
GOAL_ICONS = ['target', 'home', 'car', 'plane', 'graduation-cap', 'heart', 'gift', 'smartphone', 'briefcase']


@goals_bp.route('/')
def index():
    goals = Goal.query.order_by(Goal.status, Goal.target_date).all()
    active = [g for g in goals if g.status == 'active']
    completed = [g for g in goals if g.status == 'completed']
    total_target = sum(float(g.target_amount) for g in active)
    total_saved = sum(float(g.current_amount) for g in active)
    return render_template('goals.html', goals=active, completed=completed,
                           total_target=total_target, total_saved=total_saved,
                           colors=GOAL_COLORS, icons=GOAL_ICONS)


@goals_bp.route('/add', methods=['POST'])
def add():
    try:
        target_date = None
        if request.form.get('target_date'):
            target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d').date()

        goal = Goal(
            name=request.form['name'].strip(),
            description=request.form.get('description', '').strip() or None,
            target_amount=float(request.form['target_amount']),
            current_amount=float(request.form.get('current_amount', 0)),
            target_date=target_date,
            color=request.form.get('color', '#6c63ff'),
            icon=request.form.get('icon', 'target'),
        )
        db.session.add(goal)
        db.session.commit()
        flash(f'Goal "{goal.name}" created!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating goal: {str(e)}', 'error')
    return redirect(url_for('goals.index'))


@goals_bp.route('/<int:goal_id>/contribute', methods=['POST'])
def contribute(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    try:
        amount = float(request.form.get('amount', 0))
        goal.current_amount = float(goal.current_amount) + amount
        if float(goal.current_amount) >= float(goal.target_amount):
            goal.status = 'completed'
        db.session.commit()
        return jsonify({'success': True, 'progress': goal.progress_percentage,
                        'current': float(goal.current_amount), 'status': goal.status})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@goals_bp.route('/<int:goal_id>/delete', methods=['POST'])
def delete(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'success': True})
