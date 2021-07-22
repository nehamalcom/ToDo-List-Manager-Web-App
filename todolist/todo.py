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
    return render_template('todo/index.html', lists=lists)

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
            listid = db.execute(
                'SELECT last_insert_rowid()'
            ).fetchone()
            db.commit()
            return redirect(url_for('todo.itemsindex', listid=int(listid[0])))
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

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
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
    return render_template('todo/update.html', list=list)

@bp.route('/<int:id>/delete', methods=('POST', ))
@login_required
def delete(id):
    get_list(id)
    db = get_db()
    db.execute('DELETE FROM list WHERE id = ?', (id, ))
    db.commit()
    return redirect(url_for('todo.index'))

def get_item(listid, itemid, check_author=True):
    list = get_db().execute(
        'SELECT id, title, date_created, date_due, description, listid, completed FROM item WHERE listid = ? AND id = ?', (listid, itemid)
    ).fetchone()
    if list is None:
        abort(404, f"Item id {itemid} doesn't exist.")
    if check_author and list['author_id']!=g.user['id']:
        abort(403)
    
    return list


@bp.route('/<int:listid>')
@login_required
def itemsindex(listid):
    db = get_db()
    itemsoflist = db.execute(
        'SELECT l.id, author_id, created, l.title, body, i.id, i.title, date_created, date_due, description, completed FROM list l JOIN item i ON listid = l.id WHERE listid = ? ORDER BY completed, date_due',(listid, )
    ).fetchall()
    return render_template('todo/itemsindex.html', items=itemsoflist, listid=listid)


@bp.route('/<int:listid>/createitem', methods=('GET', 'POST'))
@login_required
def createitem(listid):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_due = request.form['date_due']
        listid = listid
        completed = 0
        error = None
        
        if not title:
            error = 'Title is required.'
        if not date_due:
            error = 'Date due is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO item (title, date_due, description, listid, completed) VALUES (?, ?, ?, ?, ?)', (title, date_due, description, listid, completed)
            )
            db.commit()
            return redirect(url_for('todo.itemsindex', listid=listid))
    return render_template('todo/createitem.html')


@bp.route('/<int:listid>/<int:itemid>/update', methods=('GET', 'POST'))
@login_required
def updateitem(listid, itemid):
    list = get_list(listid)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_due = request.form['date_due']
        error = None

        if not title:
            error = 'Title is required.'
        if not date_due:
            error = 'Date due is required.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE item SET title = ?, description = ? WHERE listid = ? AND itemid = ?', (title, description, listid, itemid)
            )
            db.commit()
            return redirect(url_for('todo.itemsindex', listid = listid))
    return render_template('todo/updateitem.html', list=list)



@bp.route('/<int:listid>/<int:itemid>/delete', methods=('POST', ))
@login_required
def deleteitem(listid, itemid):
    get_list(listid)
    get_item(itemid)
    db = get_db()
    db.execute('DELETE FROM item WHERE listid = ? AND itemid = ?', (listid, itemid))
    db.commit()
    return redirect(url_for('todo.itemsindex', listid=listid))