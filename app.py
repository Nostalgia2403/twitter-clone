import sqlite3
from flask import Flask, request, redirect

app = Flask(__name__)

DB = "posts.db"   # the database file — this is your whole database, one file on disk

# --- Database setup ---

def init_db():
    """Create the posts table once, if it doesn't already exist."""
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    """)
    conn.commit()   # save the change to disk
    conn.close()

# --- Routes ---

@app.route("/")
def home():
    conn = sqlite3.connect(DB)
    cursor = conn.execute("SELECT content FROM posts ORDER BY id DESC")
    rows = cursor.fetchall()   # get all matching rows as a list
    conn.close()

    # rows is a list of tuples like [("hello",), ("world",)] — note the comma:
    # each row is a tuple, and we want the first (only) column, so row[0].
    posts_html = ""
    for row in rows:
        posts_html += f"<p>{row[0]}</p>"

    return f"""
        <h1>My Twitter Clone</h1>
        <form action="/add" method="POST">
            <input name="content" placeholder="What's happening?">
            <button type="submit">Post</button>
        </form>
        <hr>
        {posts_html}
    """

@app.route("/add", methods=["POST"])
def add():
    content = request.form["content"]

    conn = sqlite3.connect(DB)
    # The ? placeholder = safe. User input is data, never SQL. Prevents injection.
    conn.execute("INSERT INTO posts (content) VALUES (?)", (content,))
    conn.commit()   # actually write it to disk
    conn.close()

    return redirect("/")

if __name__ == "__main__":
    init_db()              # make sure the table exists before serving
    app.run(debug=True)