from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension

from models import connect_db, db, User, Note
from forms import NoteForm, RegisterForm, LoginForm, CSRFOnlyForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///hashing_login"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.get("/")
def homepage():
    """Redirects to the /register route."""

    return redirect('/register')


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user: produce form & handle form submission."""

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        pwd = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(
            username,
            pwd,
            email,
            first_name,
            last_name
        )
        db.session.add(user)
        db.session.commit()

        session["username"] = user.username

        return redirect(f"/users/{username}")

    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Produce login form or handle login."""

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        pwd = form.password.data

        user = User.authenticate(username, pwd)
        if user:
            session["username"] = user.username
            return redirect(f"/users/{username}")

        else:
            form.username.errors = ["Bad name/password"]

    return render_template("login.html", form=form)


@app.get("/users/<username>")
def secret(username):
    """hidden page for logged-in users only."""

    if "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/login")

    else:
        user = User.query.get_or_404(username)
        form = CSRFOnlyForm()
        # breakpoint()
        return render_template("user_info.html", user=user, form=form)


@app.post("/logout")
def logout():
    """Logs user out and redirects to homepage."""
    form = CSRFOnlyForm()

    if form.validate_on_submit():
        session.pop("username", None)

    return redirect("/")

#User Routes######################################################
@app.post("/users/<username>/delete")
def delete_user_and_user_posts(username):
    """Logs user out and redirects to homepage."""

    form = CSRFOnlyForm()

    if form.validate_on_submit():

        user = User.query.get_or_404(username)
        notes = user.notes

        for note in notes:
            db.session.delete(note)

        del session["username"]
        db.session.delete(user)
        db.session.commit()

    return redirect("/")


#Note Routes######################################################
@app.route("/users/<username>/notes/add", methods=["GET", "POST"])
def show_add_note_form_or_handle_new_note(username):
    """Shows add new note form or handles new note submission."""

    if "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/login")

    form = NoteForm()

    if form.validate_on_submit(): 

        title = form.title.data
        content = form.content.data
        owner = username

        new_note = Note(title=title, content=content, owner=owner)

        db.session.add(new_note)
        db.session.commit()
        # FIXME: WHy does this route to http://localhost:5000/users/colin/notes/users/colin
        return redirect(f"/users/{owner}")

    else:
        return render_template("note.html", form=form)

@app.route("/notes/<int:note_id>/update", methods=["GET", "POST"])
def show_or_update_note_details(note_id):
    """Produce note edit form or handle edit of note."""

    note = Note.query.get_or_404(note_id)
    form = NoteForm(obj=note)

    if form.validate_on_submit():

        note.title = form.title.data
        note.content = form.content.data

        db.session.add(note)
        db.session.commit()
        return redirect(f"users/{note.user.username}")

    else:
        return render_template("note.html", form=form, note=note)

@app.post("/notes/<int:note_id>/delete")
def delete_note(note_id):
    """Logs user out and redirects to homepage."""
    form = CSRFOnlyForm()

    if form.validate_on_submit():

        note = Note.query.get_or_404(note_id)
        username = note.user.username

        db.session.delete(note)
        db.session.commit()

    return redirect(f"/users/{username}")