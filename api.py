from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def db():
    return sqlite3.connect("db.sqlite")

@app.route("/auth", methods=["POST"])
def auth():
    data = request.json
    key = data.get("key")

    con = db()
    cur = con.cursor()

    cur.execute("SELECT key FROM keys WHERE key=? AND revoked=0", (key,))
    row = cur.fetchone()

    if row:
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False})

app.run(port=5000)