from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from todolist.auth import login_required
from todolist.db import get_db

bp = Blueprint('todo', __name__)

@bp.route('/')
def index():
    db = get_db()
    lists = db.execute(
        'SELECT l.id, author_id, created, title, body, username FROM list l JOIN user u ON l.author_id = u.id ORDER BY created DESC'
    ).fetchall()
    return render_template('todo/index.html', posts=lists)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None
        
        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO list (title, body, author_id) VALUES (?, ?, ?)', (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('todo.index'))
    return render_template('todo/create.html')

def get_list(id, check_author=True):
    list = get_db().execute(
        'SELECT l.id, title, body, created, author_id, username FROM list l JOIN user u ON l.author_id = u.id WHERE l.id = ?', (id, )
    ).fetchone()
    if list is None:
        abort(404, f"List id {id} doesn't exist.")
    if check_author and list['author_id']!=g.user['id']:
        abort(403)
    
    return list

@bp.route('/int:id/update', methods=('GET', 'POST'))
@login_required
def update(id):
    list = get_list(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE list SET title = ?, body = ? WHERE id = ?', (title, body, id)
            )
            db.commit()
            return redirect(url_for('todo.index'))
    return render_template('todo/update.html', post=list)

@bp.route('/<int:id>/delete', methods=('POST', ))
@login_required
def delete(id):
    get_list(id)
    db = get_db()
    db.execute('DELETE FROM list WHERE id = ?', (id, ))
    db.commit()
    return redirect(url_for('blog.index'))