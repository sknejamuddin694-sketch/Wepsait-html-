# ===============================
# ROCKY BYPASS FULL SYSTEM
# Dynamic GitHub API Version
# Termux / VPS Safe
# ===============================

import telebot
import requests
import time
import re
import sqlite3
import os
import sys
import subprocess
from telebot import types
from urllib.parse import urlparse
from flask import Flask, request, jsonify
import threading

# ================= CONFIG =================
BOT_TOKEN = "8222118299:AAF8Zt9upqfa1gs7ouWijRaCBm_wsMfmFRA"
ADMIN_ID = 8465446299
OWNER_NAME = "@ROCKY_BHAI787"

GITHUB_API_JSON = "https://raw.githubusercontent.com/sknejamuddin694-sketch/Expiry/refs/heads/main/html.json"

FREE_LIMIT = 10
REF_REWARD = 3

# ================= INIT =================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
LINK_RE = re.compile(r"https?://\S+")

BYPASS_API = None
LAST_FETCH = 0

# ================= DATABASE =================
db = sqlite3.connect("rocky_users.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    used INTEGER DEFAULT 0,
    tokens INTEGER DEFAULT 0,
    referred INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS redeem(
    code TEXT PRIMARY KEY,
    value INTEGER
)
""")

db.commit()

# ================= HELPERS =================
def get_user(uid):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    u = cur.fetchone()
    if not u:
        cur.execute("INSERT INTO users(id) VALUES(?)", (uid,))
        db.commit()
        return get_user(uid)
    return list(u)

def user_limit(u):
    return FREE_LIMIT + u[2]

def domain(url):
    return urlparse(url).netloc

def get_bypass_api():
    global BYPASS_API, LAST_FETCH

    if BYPASS_API and time.time() - LAST_FETCH < 27:
        return BYPASS_API

    try:
        r = requests.get(GITHUB_API_JSON, timeout=20).json()
        api = r.get("bypass_api")
        if api:
            BYPASS_API = api
            LAST_FETCH = time.time()
            return api
    except:
        pass

    return BYPASS_API

# ================= KEYBOARDS =================
def main_kb(uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📊 𝚂𝚃𝙰𝚃𝚂", callback_data="stats"),
        types.InlineKeyboardButton("🎁 𝚁𝙴𝙳𝙴𝙴𝙼", callback_data="redeem")
    )
    kb.add(
        types.InlineKeyboardButton(
            "📟 𝚆𝙴𝙱𝚂𝙸𝚃𝙴",
            url=f"https://t.me/Mr_rocky_99_bot/Google"
        )
    )
    if uid == ADMIN_ID:
        kb.add(types.InlineKeyboardButton("👑 𝙰𝙳𝙼𝙸𝙽 𝙿𝙰𝙽𝙴𝙻", callback_data="admin"))
    return kb

def admin_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📊 𝙳𝙰𝚂𝙷𝙱𝙾𝙰𝚁𝙳", callback_data="dash"),
        types.InlineKeyboardButton("🎟 𝙲𝚁𝙴𝙰𝚃𝙴 𝚁𝙴𝙳𝙴𝙴𝙼", callback_data="make_redeem")
    )
    kb.add(types.InlineKeyboardButton("🤖 𝙲𝙻𝙾𝙽𝙴 𝙱𝙾𝚃", callback_data="clone"))
    return kb

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    args = m.text.split()
    u = get_user(uid)

    if len(args) > 1 and args[1].startswith("ref_") and u[3] == 0:
        ref = int(args[1].split("_")[1])
        if ref != uid:
            ru = get_user(ref)
            cur.execute("UPDATE users SET tokens=? WHERE id=?", (ru[2] + REF_REWARD, ref))
            cur.execute("UPDATE users SET referred=1 WHERE id=?", (uid,))
            db.commit()
            bot.send_message(ref, f"👁️‍🗨️ 𝙽𝙴𝚆 𝚁𝙴𝙵𝙰𝚁𝚁𝙰𝙻 𝙹𝙾𝙸𝙽𝙴𝙳\n+{REF_REWARD} tokens")

    bot.send_message(
        uid,
        f"""
<b>╭──  🚀 𝙻𝙸𝙽𝙺 𝙱𝚈𝙿𝙰𝚂𝚂 ──╮</b>

👋 𝙷𝙸 <b>{m.from_user.first_name}</b>

⭐ 𝚄𝚂𝙴𝙳 : <b>{u[1]} / {user_limit(u)}</b>
🎁 𝚃𝙾𝙺𝙴𝙽𝚂 : <b>{u[2]}</b>

📨 𝚂𝙴𝙽𝙳 𝙰𝙽𝚈 𝙻𝙸𝙽𝙺 𝚃𝙾 𝙱𝚈𝙿𝙰𝚂𝚂
    𝚆𝙴𝙱𝚂𝙸𝚃𝙴 𝙺𝙴𝚈 𝙱𝚈 𝙾𝚆𝙽𝙴𝚁 👇🏻
<b>╰── 𝙾𝚆𝙽𝙴𝚁: {OWNER_NAME} ──╯</b>
""",
        reply_markup=main_kb(uid)
    )

# ================= BYPASS =================
@bot.message_handler(func=lambda m: m.text and LINK_RE.search(m.text))
def bypass(m):
    uid = m.from_user.id
    u = get_user(uid)

    if u[1] >= user_limit(u):
        bot.reply_to(m, "❌ 𝙻𝙸𝙼𝙸𝚃 𝚁𝙴𝙰𝙲𝙷𝙴𝙳. 𝚄𝚂𝙴 𝚁𝙴𝙳𝙴𝙴𝙼 𝙾𝚁 𝚁𝙴𝙵𝙴𝚁.")
        return

    link = LINK_RE.search(m.text).group(0)
    msg = bot.reply_to(m, "⏳ 𝑃𝑟𝑜𝑐𝑒𝑠𝑠𝑖𝑛𝑔......")

    api = get_bypass_api()
    if not api:
        bot.edit_message_text("❌  𝙱𝚈𝙿𝙰𝚂𝚂 𝙰𝙿𝙸 𝙵𝙰𝙸𝙻𝙴𝙳", m.chat.id, msg.message_id)
        return

    try:
        r = requests.get(BYPASS_API + link, timeout=45).json()
        bypassed = r.get("bypassed") or r.get("url")
        if not bypassed:
            raise Exception()
    except:
        bot.edit_message_text("🪫", m.chat.id, msg.message_id)
        return

    bot.edit_message_text(
        f"""
<b>╭── 🔋 𝙻𝙸𝙽𝙺 𝚄𝙽𝙻𝙾𝙲𝙺𝙴𝙳 ──╮</b>

🔗 <b>𝙾𝚁𝙸𝙶𝙸𝙽𝙰𝙻</b>
<code>{link}</code>

🚀 <b>𝙱𝚈𝙿𝙰𝚂𝚂𝙴𝙳</b>
<code>{bypassed}</code>

🌐 Host : <b>{domain(link)}</b>

🔑 <b>𝙰𝙿𝙸 𝙰𝙲𝙲𝙴𝚂𝚂:</b>𝙾𝙽𝙻𝚈<b>₹30</b>
📩 <b>𝙳𝙼 𝚃𝙷𝙴 𝙾𝚆𝙽𝙴𝚁 𝙵𝙾𝚁 𝙰𝙿𝙸 𝙰𝙲𝙲𝙴𝚂𝚂</b>

<b>╰────────────────────╯</b>
""",
        m.chat.id,
        msg.message_id,
        disable_web_page_preview=True
    )

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id

    if c.data == "stats":
        u = get_user(uid)
        bot.answer_callback_query(c.id, f"Used: {u[1]}\nTokens: {u[2]}", show_alert=True)

    elif c.data == "redeem":
        bot.answer_callback_query(c.id, "𝚂𝙴𝙽𝙳 𝚁𝙴𝙳𝙴𝙴𝙼 𝙲𝙾𝙳𝙴", show_alert=True)
        bot.register_next_step_handler(c.message, redeem_code)

    elif c.data == "admin" and uid == ADMIN_ID:
        bot.edit_message_text("👑 𝙰𝙳𝙼𝙸𝙽 𝙿𝙰𝙽𝙴𝙻", c.message.chat.id, c.message.message_id, reply_markup=admin_kb())

    elif c.data == "dash" and uid == ADMIN_ID:
        total = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        bot.answer_callback_query(c.id, f"👥 𝚄𝚂𝙴𝚁𝚂: {total}", show_alert=True)

    elif c.data == "make_redeem" and uid == ADMIN_ID:
        bot.answer_callback_query(c.id, "Send: CODE VALUE", show_alert=True)
        bot.register_next_step_handler(c.message, create_redeem)

    elif c.data == "clone" and uid == ADMIN_ID:
        bot.answer_callback_query(c.id, "Send NEW BOT TOKEN", show_alert=True)
        bot.register_next_step_handler(c.message, clone_bot)

# ================= REDEEM =================
def redeem_code(m):
    code = m.text.strip()
    cur.execute("SELECT value FROM redeem WHERE code=?", (code,))
    r = cur.fetchone()
    if not r:
        bot.reply_to(m, "❌ 𝙸𝙽𝚅𝙰𝙻𝙸𝙳 𝙲𝙾𝙳𝙴")
        return

    u = get_user(m.from_user.id)
    cur.execute("UPDATE users SET tokens=? WHERE id=?", (u[2] + r[0], m.from_user.id))
    cur.execute("DELETE FROM redeem WHERE code=?", (code,))
    db.commit()
    bot.reply_to(m, f"✅ {r[0]} 𝚃𝙾𝙺𝙴𝙽𝚂 𝙰𝙳𝙳𝙴𝙳")

def create_redeem(m):
    try:
        code, val = m.text.split()
        cur.execute("INSERT INTO redeem VALUES(?,?)", (code, int(val)))
        db.commit()
        bot.reply_to(m, "✅ 𝚁𝙴𝙳𝙴𝙴𝙼 𝙲𝚁𝙴𝙰𝚃𝙴𝙳")
    except:
        bot.reply_to(m, "❌ 𝙵𝙾𝚁𝙼𝙰𝚃: 𝙲𝙾𝙳𝙴 𝚅𝙰𝙻𝚄𝙴")

# ================= CLONE =================
def clone_bot(m):
    token = m.text.strip()
    os.makedirs("clones", exist_ok=True)
    newfile = f"clones/clone_{token[:10]}.py"

    with open(sys.argv[0], "r") as f:
        data = f.read().replace(BOT_TOKEN, token)

    with open(newfile, "w") as f:
        f.write(data)

    subprocess.Popen(["python", newfile])
    bot.reply_to(m, "🤖 𝙲𝙻𝙾𝙽𝙴 𝙱𝙾𝚃 𝚂𝚃𝙰𝚁𝚃𝙴𝙳")

# ================= API SERVER =================
app = Flask(__name__)

@app.route("/clone")
def api_clone():
    token = request.args.get("token")
    if not token:
        return jsonify(ok=False)

    os.makedirs("clones", exist_ok=True)
    newfile = f"clones/api_clone_{token[:10]}.py"

    with open(sys.argv[0], "r") as f:
        data = f.read().replace(BOT_TOKEN, token)

    with open(newfile, "w") as f:
        f.write(data)

    subprocess.Popen(["python", newfile])
    return jsonify(ok=True)

def run_api():
    app.run("127.0.0.1", 8000)

# ================= RUN =================
def start_bot():
    try:
        bot.remove_webhook()
    except:
        pass
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    print("🤖 ROCKY SYSTEM STARTED")
    threading.Thread(target=run_api).start()
    start_bot()
