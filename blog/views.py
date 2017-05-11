from flask import render_template, request, redirect, url_for

from . import app
from .database import session, Entry

DEFAULT_PAGINATE_BY = 10

@app.route("/", methods=['GET'])
@app.route("/page/<int:page>", methods=['GET'])
def entries_get(page=1):
    # Zero-indexed page
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
def add_entry_get():
    return render_template("add_entry.html")

@app.route("/entry/add", methods=["POST"])
def add_entry_post():
    entry = Entry(
        title=request.form["title"],
        content=request.form["content"],
    )
    session.add(entry)
    session.commit()
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
def edit_entry_get(id):
    entry = session.query(Entry).filter(Entry.id==id)
    return render_template("edit_entry.html", entry=entry[0])

@app.route("/entry/<id>/edit", methods=["POST"])
def edit_entry_post(id):
    session.query(Entry).filter(Entry.id==id).update({Entry.title: request.form["title"]})
    session.query(Entry).filter(Entry.id==id).update({Entry.content: request.form["content"]})
    session.commit()
    return redirect(url_for('single_entry', id=id))

@app.route("/entry/<id>/delete", methods=["GET"])
def delete_entry_get(id):
    return render_template("delete_entry.html")

@app.route("/entry/<id>/delete", methods=["POST"])
def delete_entry_post(id):
    session.query(Entry).filter(Entry.id==id).delete()
    session.commit()
    return redirect(url_for("entries_get"))