from flask import render_template, request, redirect, url_for, flash
from flask.ext.login import login_user, login_required, current_user, logout_user
from werkzeug.security import check_password_hash

from . import app
from .database import session, Entry, User

DEFAULT_PAGINATE_BY = 10

@app.route("/", methods=['GET'])
@app.route("/page/<int:page>", methods=['GET'])
def entries_get(page=1):
    page_index = page - 1
    paginate_by = DEFAULT_PAGINATE_BY
    if request.args.get('limit'):
        try:
            paginate_by = float(request.args.get('limit'))
        except ValueError:
            paginate_by = DEFAULT_PAGINATE_BY
        paginate_by = int(round(paginate_by))
        if paginate_by < 1:
            paginate_by = 1
        if paginate_by > 100:
            paginate_by = 100
    
    count = session.query(Entry).count()

    start = page_index * paginate_by
    end = start + paginate_by

    total_pages = (count - 1) // paginate_by + 1
    has_next = page_index < total_pages - 1
    has_prev = page_index > 0

    entries = session.query(Entry)
    entries = entries.order_by(Entry.datetime.desc())
    entries = entries[start:end]

    return render_template("entries.html",
        entries=entries,
        has_next=has_next,
        has_prev=has_prev,
        page=page,
        total_pages=total_pages,
    )

@app.route("/", methods=['POST'])
@app.route("/page/<int:page>", methods=['POST'])
def entries_post(page=1):
    return redirect(url_for('entries_get', limit=request.form['limit']))

@app.route("/entry/add", methods=["GET"])
@login_required
def add_entry_get():
    return render_template("add_entry.html")

@app.route("/entry/add", methods=["POST"])
@login_required
def add_entry_post():
    entry = Entry(
        title=request.form["title"],
        content=request.form["content"],
        author=current_user
    )
    session.add(entry)
    session.commit()
    flash("Article added.", "success")
    return redirect(url_for("entries_get"))

@app.route("/entry/<id>")
def single_entry(id):
    
    count = session.query(Entry).count()

    has_next = int(id) > 1
    has_prev = int(id) < count

    entry = session.query(Entry).filter(Entry.id==id)
    return render_template("single_entry.html",
        entry=entry[0],
        id = int(id),
        has_next=has_next,
        has_prev=has_prev,
    )

@app.route("/entry/<id>/edit", methods=["GET"])
@login_required
def edit_entry_get(id):
    if current_user.name == session.query(Entry).filter(Entry.id==id).one().author.name:
        entry = session.query(Entry).filter(Entry.id==id)
        return render_template("edit_entry.html", entry=entry[0])
    else:
        flash("You cannot edit an article you did not author.", "danger")
        return redirect(url_for('single_entry', id=id))

@app.route("/entry/<id>/edit", methods=["POST"])
@login_required
def edit_entry_post(id):
    if current_user.name == session.query(Entry).filter(Entry.id==id).one().author.name:
        session.query(Entry).filter(Entry.id==id).update({Entry.title: request.form["title"]})
        session.query(Entry).filter(Entry.id==id).update({Entry.content: request.form["content"]})
        session.commit()
        flash("Article edited.", "success")
        return redirect(url_for('single_entry', id=id))
    else:
        flash("You cannot edit an article you did not author.", "danger")
        return redirect(url_for('single_entry', id=id))

@app.route("/entry/<id>/delete", methods=["GET"])
@login_required
def delete_entry_get(id):
    if current_user.name == session.query(Entry).filter(Entry.id==id).one().author.name:
        return render_template("delete_entry.html")
    else:
        flash("You cannot delete an article you did not author.", "danger")
        return redirect(url_for('single_entry', id=id))

@app.route("/entry/<id>/delete", methods=["POST"])
@login_required
def delete_entry_post(id):
    if current_user.name == session.query(Entry).filter(Entry.id==id).one().author.name:
        session.query(Entry).filter(Entry.id==id).delete()
        session.commit()
        flash("Article deleted.", "success")
        return redirect(url_for("entries_get"))
    else:
        flash("You cannot delete an article you did not author.", "danger")
        return redirect(url_for('single_entry', id=id))

@app.route("/login", methods=["GET"])
def login_get():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    email = request.form["email"]
    password = request.form["password"]
    user = session.query(User).filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        flash("Incorrect username or password", "danger")
        return redirect(url_for("login_get"))

    login_user(user)
    return redirect(request.args.get('next') or url_for("entries_get"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("entries_get"))
