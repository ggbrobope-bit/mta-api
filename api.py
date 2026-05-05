from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# ===== CONFIG DB =====
def db():
    return sqlite3.connect("db.sqlite")

# ===== KEYS FIXAS =====
FIXED_KEYS = {
    "VIP-FOREVER-1234": {
        "expires": None,
        "revoked": False
    },
    "DEV-ACCESS-9999": {
        "expires": None,
        "revoked": False
    }
}

# ===== AUTH =====
@app.route("/auth", methods=["POST"])
def auth():
    data = request.json
    key = data.get("key")

    # ===== 1. VERIFICA FIXAS =====
    if key in FIXED_KEYS:
        info = FIXED_KEYS[key]

        if info["revoked"]:
            return jsonify({"ok": False, "reason": "revoked"})

        if info["expires"]:
            if datetime.utcnow() > info["expires"]:
                return jsonify({"ok": False, "reason": "expired"})

        return jsonify({"ok": True})

    # ===== 2. BANCO =====
    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT key, expires_at, revoked
        FROM keys
        WHERE key=?
    """, (key,))

    row = cur.fetchone()
    con.close()

    if not row:
        return jsonify({"ok": False})

    k, exp, revoked = row

    if revoked:
        return jsonify({"ok": False, "reason": "revoked"})

    if exp:
        try:
            exp_dt = datetime.fromisoformat(exp)
            if datetime.utcnow() > exp_dt:
                return jsonify({"ok": False, "reason": "expired"})
        except:
            return jsonify({"ok": False})

    return jsonify({"ok": True})


# ===== LISTAR KEYS =====
@app.route("/keys", methods=["GET"])
def list_keys():
    if request.args.get("admin") != "1234":
        return jsonify({"ok": False})

    con = db()
    cur = con.cursor()

    cur.execute("SELECT key, expires_at, revoked FROM keys")
    data = cur.fetchall()

    con.close()

    return jsonify({"ok": True, "keys": data})


# ===== CRIAR KEY =====
@app.route("/create_key", methods=["POST"])
def create_key():
    data = request.json

    if data.get("admin") != "1234":
        return jsonify({"ok": False})

    key = data["key"]
    exp = data["expires_at"]

    con = db()
    cur = con.cursor()

    try:
        cur.execute(
            "INSERT INTO keys (key, expires_at, revoked) VALUES (?, ?, 0)",
            (key, exp)
        )
        con.commit()
    except:
        return jsonify({"ok": False, "error": "key_exists"})

    con.close()

    return jsonify({"ok": True})


# ===== REVOGAR =====
@app.route("/revoke", methods=["POST"])
def revoke():
    data = request.json

    if data.get("admin") != "1234":
        return jsonify({"ok": False})

    key = data["key"]

    con = db()
    cur = con.cursor()

    cur.execute("UPDATE keys SET revoked=1 WHERE key=?", (key,))
    con.commit()

    con.close()

    return jsonify({"ok": True})


# ===== START =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
