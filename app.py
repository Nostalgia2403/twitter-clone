import sqlite3
from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "dev-secret-change-me-later"

DB = "posts.db"   # the database file — this is your whole database, one file on disk

# --- Database setup ---

def init_db():
    """Create the posts table once, if it doesn't already exist."""
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()   # save the change to disk
    conn.close()

# --- Routes ---

@app.route("/")
def home():
    conn = sqlite3.connect(DB)
    cursor = conn.execute("SELECT posts.content, users.username FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.id DESC")
    rows = cursor.fetchall()
    conn.close()

    # Each row is (content, username) from the JOIN.
    posts_html = ""
    for row in rows:
        posts_html += f"<p><b>{row[1]}</b>: {row[0]}</p>"

    # One branch decides everything that depends on being logged in:
    # which nav links to show AND whether the post form appears.
    if "user_id" in session:
        nav = "<a href='/logout'>Logout</a>"
        form = """
            <form action="/add" method="POST">
                <input name="content" placeholder="What's happening?">
                <button type="submit">Post</button>
            </form>
        """
    else:
        nav = "<a href='/signup'>Sign Up</a> | <a href='/login'>Login</a>"
        form = "<p>Log in to post.</p>"

    return f"""
        <h1>My Twitter Clone</h1>
        {nav}
        {form}
        <hr>
        {posts_html}
    """

@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:        # bounce before touching anything
        return redirect("/login")

    content = request.form["content"]
    user_id = session["user_id"]

    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO posts (content, user_id) VALUES (?, ?)",
        (content, user_id),
    )
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/signup")
def signup_form():
    return """
        <h1>Sign Up</h1>
        <a href="/">Home</a>
        <form action="/signup" method="POST">
            <input name="username" placeholder="Username">
            <input name="password" type="password" placeholder="Password">
            <button type="submit">Sign Up</button>
        </form>
    """

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]

    # Hash the password — salt + slow hash, handled for us.
    # The plaintext never goes anywhere near the database.
    pw_hash = generate_password_hash(password)

    conn = sqlite3.connect(DB)
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, pw_hash),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # UNIQUE constraint fired — username is taken
        conn.close()
        return "Username already taken. <a href='/signup'>Try again</a>"
    conn.close()

    return redirect("/")

@app.route("/login")
def login_form():
    return """
        <h1>Login</h1>
        <a href="/">Home</a>
        <form action="/login" method="POST">
            <input name="username" placeholder="Username">
            <input name="password" type="password" placeholder="Password">
            <button type="submit">Login</button>
        </form>
    """

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect(DB)
    cursor = conn.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (username,)
    )
    row = cursor.fetchone()   # one row or None — username is UNIQUE
    conn.close()

    # Reject if user doesn't exist OR password doesn't match the hash
    if row is None or not check_password_hash(row[1], password):
        return "Invalid username or password. <a href='/login'>Try again</a>"

    session["user_id"] = row[0]     # <-- THE login. Signed cookie now carries their id.
    return redirect("/")

@app.route("/logout")
def logout():
    session.pop("user_id", None)    # remove the id; the cookie no longer proves anything
    return redirect("/")

if __name__ == "__main__":
    init_db()              # make sure the table exists before serving
    app.run(debug=True)