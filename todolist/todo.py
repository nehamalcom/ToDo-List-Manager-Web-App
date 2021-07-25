from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from todolist.auth import login_required
from todolist.db import get_db
import jsonify

bp = Blueprint('todo', __name__)

@bp.route('/')
@login_required
def index():
    db = get_db()
    userid = g.user['id']
    lists = db.execute(
        'SELECT l.id, author_id, created, title, body, username FROM list l JOIN user u ON l.author_id = u.id WHERE u.id = ? ORDER BY created DESC',(userid, )
    ).fetchall()
    if (request.accept_mimetypes.best == "application/json"):
        return jsonify(dict(list = [dict(title = title, body=body) for _ , _ , _ , title, body, _ in lists]))
    else:
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
    item = get_db().execute(
        'SELECT id AS itemid, title, date_created, date_due, description, listid, completed FROM item WHERE listid = ? AND id = ?', (listid, itemid)
    ).fetchone()
    if item is None:
        abort(404, f"Item id {itemid} doesn't exist.")
    list = get_db().execute(
        'SELECT author_id, i.id AS itemid, i.title, date_created, date_due, description, listid, completed FROM item i JOIN list l ON listid = l.id WHERE listid = ? AND i.id = ?', (listid, itemid)
    ).fetchone()
    if check_author and list['author_id']!=g.user['id']:
        abort(403)
    
    return item


@bp.route('/<int:listid>')
@login_required
def itemsindex(listid):
    db = get_db()
    itemsoflist = db.execute(
        'SELECT l.id AS listid, author_id, created, l.title AS listtitle, body, i.id AS itemid, i.title AS itemtitle, date_created, date_due, description, completed FROM list l JOIN item i ON listid = l.id WHERE listid = ? ORDER BY date_due',(listid, )
    ).fetchall()
    listtitle = db.execute(
        'SELECT title FROM list WHERE id = ?',(listid, )
    ).fetchone()
    return render_template('todo/itemsindex.html', items=itemsoflist, listid=listid, listtitle=listtitle)

@bp.route('/today')
@login_required
def todayitems():
    db = get_db()
    todayitems = db.execute(
        "SELECT l.id AS listid, author_id, created, l.title AS listtitle, body, i.id AS itemid, i.title AS itemtitle, date_created, date_due, description, completed FROM list l JOIN item i ON listid = l.id WHERE date_due = DATE('now') ORDER BY date_due"
    ).fetchall()
    return render_template('todo/todayitems.html', items=todayitems, listid=0, listtitle="Today")

@bp.route('/<int:listid>/createitem', methods=('GET', 'POST'))
@login_required
def createitem(listid):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_due = request.form['date_due']
        listid = listid
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
                'INSERT INTO item (title, date_due, description, listid) VALUES (?, ?, ?, ?)', (title, date_due, description, listid)
            )
            db.commit()
            return redirect(url_for('todo.itemsindex', listid=listid))
    return render_template('todo/createitem.html')


@bp.route('/<int:listid>/<int:itemid>/update', methods=('GET', 'POST'))
@login_required
def updateitem(listid, itemid):
    item = get_item(listid, itemid)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        doneornot =  request.form['options']
        #date_due = request.form['datedue']
        error = None

        if not title:
            error = 'Title is required.'
        #if not date_due:
        #    error = 'Date due is required.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            if doneornot == "completed":
                completed = 1
                db.execute(
                    'UPDATE item SET title = ?, description = ?, completed = ? WHERE listid = ? AND id = ?', (title, description, completed, listid, itemid)
                )
            else:
                completed = 0
                db.execute(
                    #'UPDATE item SET title = ?, description = ?, date_due = ? WHERE listid = ? AND id = ?', (title, description, date_due, listid, itemid)
                    'UPDATE item SET title = ?, description = ?, completed = ? WHERE listid = ? AND id = ?', (title, description, completed, listid, itemid)
                )
            db.commit()
            return redirect(url_for('todo.itemsindex', listid = listid))
    return render_template('todo/updateitem.html', item=item)



@bp.route('/<int:listid>/<int:itemid>/delete', methods=('POST', ))
@login_required
def deleteitem(listid, itemid):
    list = get_list(listid)
    item = get_item(listid, itemid)
    db = get_db()
    db.execute('DELETE FROM item WHERE listid = ? AND id = ?', (listid, itemid))
    db.commit()
    return redirect(url_for('todo.itemsindex', listid=listid))