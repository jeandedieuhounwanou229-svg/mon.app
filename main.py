import os
import sqlite3
from functools import wraps
from flask import Flask, request, redirect, session, url_for, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deployment")

DATABASE = "ase.db"


def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricule TEXT UNIQUE NOT NULL,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                sexe TEXT NOT NULL,
                date_naissance TEXT NOT NULL,
                lieu_naissance TEXT NOT NULL,
                place_gratuite TEXT NOT NULL,
                motif_gratuite TEXT,
                tuteur_nom TEXT,
                tuteur_prenom TEXT,
                tuteur_whatsapp TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricule TEXT NOT NULL,
                semestre TEXT NOT NULL,
                moyenne REAL NOT NULL
            )
        """)


def founder_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("founder"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    return """
    <h1>AGONKANMEY SCIENCES D’EXCELLENCE</h1>
    <h2>Espace d'inscription</h2>
    <a href="/inscription">Inscrire un élève</a><br>
    <a href="/fondateur">Espace fondateur</a>
    """


@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        data = request.form
        try:
            with db() as conn:
                conn.execute("""
                    INSERT INTO students (
                        matricule, nom, prenom, sexe,
                        date_naissance, lieu_naissance,
                        place_gratuite, motif_gratuite,
                        tuteur_nom, tuteur_prenom, tuteur_whatsapp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["matricule"], data["nom"], data["prenom"],
                    data["sexe"], data["date_naissance"],
                    data["lieu_naissance"], data["place_gratuite"],
                    data.get("motif_gratuite", ""),
                    data.get("tuteur_nom", ""),
                    data.get("tuteur_prenom", ""),
                    data.get("tuteur_whatsapp", "")
                ))
            return "Inscription enregistrée."
        except sqlite3.IntegrityError:
            return "Ce numéro matricule existe déjà."

    return """
    <h1>Formulaire d'inscription</h1>
    <form method="post">
      Matricule : <input name="matricule" required><br>
      Nom : <input name="nom" required><br>
      Prénom : <input name="prenom" required><br>
      Sexe :
      <select name="sexe" required>
        <option value="Masculin">Masculin</option>
        <option value="Féminin">Féminin</option>
      </select><br>
      Date de naissance : <input type="date" name="date_naissance" required><br>
      Lieu de naissance : <input name="lieu_naissance" required><br>
      Place gratuite :
      <select name="place_gratuite">
        <option value="Non">Non</option>
        <option value="Oui">Oui</option>
      </select><br>
      Motif : <input name="motif_gratuite"
        placeholder="Orphelin de père, de mère ou des deux"><br>
      Nom du tuteur : <input name="tuteur_nom"><br>
      Prénom du tuteur : <input name="tuteur_prenom"><br>
      WhatsApp du tuteur : <input name="tuteur_whatsapp"><br>
      <button type="submit">Enregistrer</button>
    </form>
    """


@app.route("/connexion", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = os.environ.get("FOUNDER_USERNAME")
        password_hash = os.environ.get("FOUNDER_PASSWORD_HASH")

        if (username and password_hash
                and request.form["username"] == username
                and check_password_hash(
                    password_hash, request.form["password"]
                )):
            session["founder"] = True
            return redirect(url_for("founder"))

        return "Identifiants incorrects."

    return """
    <h1>Connexion fondateur</h1>
    <form method="post">
      Identifiant : <input name="username" required><br>
      Mot de passe : <input type="password" name="password" required><br>
      <button type="submit">Se connecter</button>
    </form>
    """


@app.route("/fondateur")
@founder_required
def founder():
    with db() as conn:
        students = conn.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()

    return render_template_string("""
      <h1>Espace fondateur ASE</h1>
      <p>Élèves inscrits : {{ students|length }}</p>
      <ul>
      {% for s in students %}
        <li>{{ s['matricule'] }} — {{ s['nom'] }} {{ s['prenom'] }}</li>
      {% endfor %}
      </ul>
      <a href="/deconnexion">Déconnexion</a>
    """, students=students)


@app.route("/deconnexion")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/sante")
def health():
    return {"status": "ok", "application": "ASE"}


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
