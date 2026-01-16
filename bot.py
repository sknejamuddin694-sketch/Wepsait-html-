import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import random
import hashlib
# --- Flask Keep Alive ---
from flask import Flask
from threading import Thread
app = Flask('')
@app.route('/')
def home():
    return "🤖 𝙺𝙰𝙰𝙻𝙸𝚇 𝙷𝙾𝚂𝚃𝙸𝙽𝙶 𝙱𝙾𝚃 𝙸𝚂 𝚁𝚄𝙽𝙽𝙸𝙽𝙶 "
@app.route('/health')
def health():
    return {"status": "healthy", "uptime": get_uptime()}
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("✅ Flask Keep-Alive server started.")
# --- End Flask Keep Alive ---
# --- Configuration ---
TOKEN =  '8442419763:AAE1eRI3gNOfbVL9GUcHXyD-kK2s586qJ9s'
OWNER_ID = 8465446299
ADMIN_ID = 8465446299
YOUR_USERNAME = '@ROCKY_BHAI787'
UPDATE_CHANNEL = 'https://t.me/+Q6VZH2DQsmswMmY1'
# Folder setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
# File upload limits
FREE_USER_LIMIT = 10
SUBSCRIBED_USER_LIMIT = 15
ADMIN_LIMIT = 999
OWNER_LIMIT = float('inf')
# Create necessary directories
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
# Initialize bot

callback_file_map = {}

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
# --- Data structures ---
bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False
bot_start_time = datetime.now()
# Animation States
user_operations = {}  # Track ongoing operations per user
# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# --- Animation Classes ---
class ProgressAnimation:
    """Handles progress bar animations"""
    @staticmethod
    def create_progress_bar(current, total, length=4, style='blocks'):
        """Create a progress bar string using ▰ and ▱ (fixed 4-length, no % in bar)"""
        progress = int((current / total) * length)
        bar = "▰" * progress + "▱" * (length - progress)
        return f"[{bar}]"

class TerminalAnimation:
    """Creates terminal-style animations and outputs"""
    @staticmethod
    def create_terminal_box(title, content, status="running"):
        """Create a terminal-style box"""
        status_icons = {
            "running": "🟢",
            "stopped": "🔴",
            "error": "⚠️",
            "success": "✅",
            "loading": "⏳"
        }
        icon = status_icons.get(status, "📦")
        box = f"""
╔═══════════════
║ {icon} {title[:30]:<30}
╠═══════════════
║ {content[:32]:<32} 
╚═══════════════
"""
        return box

    @staticmethod
    def create_log_entry(action, details, timestamp=None):
        """Create a log-style entry"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        return f"[{timestamp}] {action}: {details}"

    @staticmethod
    def create_ascii_header(text):
        """Create a simple ASCII header"""
        border = "═" * (len(text) + 4)
        return f"╔{border}╗\n║  {text}  ║\n╚{border}╝"

# --- Animated Message Functions ---
def send_animated_message(chat_id, final_text, animation_type="loading", duration=2, steps=4):
    """Send animated message using the new ⚙️ 𝐋ᴏᴀᴅɪɴɢ... style"""
    try:
        # Map animation types to action texts
        action_map = {
            "loading": "Authenticating session",
            "upload": "Uploading file",
            "download": "Downloading file",
            "delete": "Deleting file",
            "run": "Starting script",
            "stop": "Stopping script",
            "install": "Installing dependencies",
            "terminal": "Initializing terminal"
        }
        action_text = action_map.get(animation_type, "Processing")

        msg = None
        for i in range(steps + 1):
            percent = int((i / steps) * 100)
            bar = "▰" * i + "▱" * (steps - i)
            display = f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({percent}%)\n[{bar}] {action_text}..."
            if i == 0:
                msg = bot.send_message(chat_id, display)
            else:
                try:
                    bot.edit_message_text(display, chat_id, msg.message_id)
                except:
                    pass
            time.sleep(duration / steps)

        # Final message
        try:
            bot.edit_message_text(final_text, chat_id, msg.message_id, parse_mode='HTML')
        except:
            bot.send_message(chat_id, final_text, parse_mode='HTML')
        return msg
    except Exception as e:
        logger.error(f"Animation error: {e}")
        return bot.send_message(chat_id, final_text, parse_mode='HTML')

def send_progress_animation(chat_id, action_text, total_steps=4, callback=None):
    """Send progress using new style: ⚙️ 𝐋ᴏᴀᴅɪɴɢ... + [▰...]"""
    try:
        msg = None
        for step in range(total_steps + 1):
            percent = int((step / total_steps) * 100)
            bar = "▰" * step + "▱" * (total_steps - step)
            display = f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({percent}%)\n[{bar}] {action_text}..."
            if step == 0:
                msg = bot.send_message(chat_id, display)
            else:
                try:
                    bot.edit_message_text(display, chat_id, msg.message_id)
                except:
                    pass
            time.sleep(0.4)
            if callback:
                callback(step, total_steps)
        return msg
    except Exception as e:
        logger.error(f"Progress animation error: {e}")
        return None

def send_spinner_animation(chat_id, text, duration=3):
    """Fallback: use loading animation if spinner is called"""
    return send_animated_message(chat_id, text, animation_type="loading", duration=duration)

def send_terminal_animation(chat_id, commands, final_output):
    """Use standard loading animation for terminal too"""
    return send_animated_message(chat_id, final_output, animation_type="terminal", duration=2)

# --- Utility Functions ---
def get_uptime():
    """Get bot uptime as string"""
    uptime = datetime.now() - bot_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def format_size(size_bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def get_system_stats():
    """Get system statistics"""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        'cpu': cpu,
        'memory_used': memory.percent,
        'memory_total': format_size(memory.total),
        'disk_used': disk.percent,
        'disk_total': format_size(disk.total),
        'uptime': get_uptime()
    }

def create_system_stats_message():
    """Create formatted system stats message"""
    stats = get_system_stats()
    running_bots = len([k for k, v in bot_scripts.items() if v.get('process') and is_bot_running_check(k)])
    msg = f"""
╔═════════════════════════
║       📊 <b>𝐊𝐀𝐀𝐋𝐈𝐗 𝐁𝐎𝐓 𝐒𝐓𝐀𝐓𝐒</b> 📊         
╠═════════════════════════
║ 🖥️ <b>𝐂𝐏𝐔 𝐔𝐬𝐚𝐠𝐞:</b> {stats['cpu']}%
║ {create_mini_bar(stats['cpu'])}
║
║ 🧠 <b>𝐌𝐞𝐦𝐨𝐫𝐲:</b> {stats['memory_used']}% / {stats['memory_total']}
║ {create_mini_bar(stats['memory_used'])}
║
║ 💾 <b>𝐃𝐢𝐬𝐤:</b> {stats['disk_used']}% / {stats['disk_total']}
║ {create_mini_bar(stats['disk_used'])}
║
║ ⏱️ <b>𝐔𝐩𝐭𝐢𝐦𝐞:</b> {stats['uptime']}
║ 🤖 <b>𝐑𝐮𝐧𝐧𝐢𝐧𝐠 𝐁𝐨𝐭𝐬:</b> {running_bots}
║ 👥 <b>𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬:</b> {len(active_users)}
╚════════════════════════
"""
    return msg

def create_mini_bar(percentage, length=20):
    """Create a mini progress bar for stats"""
    filled = int((percentage / 100) * length)
    bar = '⬤' * filled + '◯' * (length - filled)
    return f"║ [{bar}]"

def is_bot_running_check(script_key):
    """Quick check if bot is running"""
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except:
            return False
    return False

# --- Database Functions ---
def init_db():
    """Initialize the database with required tables"""
    logger.info(f"Initializing database at: {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
(user_id INTEGER PRIMARY KEY, expiry TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
(user_id INTEGER, file_name TEXT, file_type TEXT, upload_time TEXT,
file_size INTEGER, PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_users
(user_id INTEGER PRIMARY KEY, username TEXT, first_seen TEXT, last_seen TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins
(user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS bot_logs
(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT,
details TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS running_scripts
(script_key TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT,
start_time TEXT, pid INTEGER)''')
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)

def load_data():
    """Load data from database into memory"""
    logger.info("Loading data from database...")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT user_id, expiry FROM subscriptions')
        for user_id, expiry in c.fetchall():
            try:
                user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
            except ValueError:
                logger.warning(f"Invalid expiry format for user {user_id}")
        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for user_id, file_name, file_type in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((file_name, file_type))
        c.execute('SELECT user_id FROM active_users')
        active_users.update(user_id for (user_id,) in c.fetchall())
        c.execute('SELECT user_id FROM admins')
        admin_ids.update(user_id for (user_id,) in c.fetchall())
        conn.close()
        logger.info(f"Data loaded: {len(active_users)} users, {len(user_subscriptions)} subs, {len(admin_ids)} admins")
    except Exception as e:
        logger.error(f"❌ Error loading  {e}", exc_info=True)

def save_user_file_db(user_id, file_name, file_type, file_size=0):
    """Save file info to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO user_files
(user_id, file_name, file_type, upload_time, file_size)
VALUES (?, ?, ?, ?, ?)''',
                  (user_id, file_name, file_type, datetime.now().isoformat(), file_size))
        conn.commit()
        conn.close()
        log_action(user_id, "FILE_UPLOAD", f"Uploaded {file_name}")
    except Exception as e:
        logger.error(f"Error saving file to DB: {e}")

def remove_user_file_db(user_id, file_name):
    """Remove file from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
        conn.commit()
        conn.close()
        log_action(user_id, "FILE_DELETE", f"Deleted {file_name}")
    except Exception as e:
        logger.error(f"Error removing file from DB: {e}")

def save_active_user(user_id, username=None):
    """Save or update active user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('''INSERT INTO active_users (user_id, username, first_seen, last_seen)
VALUES (?, ?, ?, ?)
ON CONFLICT(user_id) DO UPDATE SET last_seen = ?, username = ?''',
                  (user_id, username, now, now, now, username))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving active user: {e}")

def log_action(user_id, action, details):
    """Log user action to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT INTO bot_logs (user_id, action, details, timestamp)
VALUES (?, ?, ?, ?)''',
                  (user_id, action, details, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging action: {e}")

def save_subscription(user_id, expiry):
    """Save subscription to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)',
                  (user_id, expiry.isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving subscription: {e}")

# Initialize DB and Load Data
init_db()
load_data()

# --- Helper Functions ---
def get_user_folder(user_id):
    """Get or create user's folder"""
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def get_user_file_limit(user_id):
    """Get file upload limit for user"""
    if user_id == OWNER_ID:
        return OWNER_LIMIT
    if user_id in admin_ids:
        return ADMIN_LIMIT
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT

def get_user_file_count(user_id):
    """Get number of files uploaded by user"""
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name):
    """Check if a bot script is running"""
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            is_running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not is_running:
                cleanup_script(script_key)
            return is_running
        except psutil.NoSuchProcess:
            cleanup_script(script_key)
            return False
        except Exception as e:
            logger.error(f"Error checking process: {e}")
            return False
    return False

def cleanup_script(script_key):
    """Clean up script resources"""
    if script_key in bot_scripts:
        script_info = bot_scripts[script_key]
        if 'log_file' in script_info and hasattr(script_info['log_file'], 'close'):
            try:
                if not script_info['log_file'].closed:
                    script_info['log_file'].close()
            except:
                pass
        del bot_scripts[script_key]
        logger.info(f"Cleaned up script: {script_key}")

def kill_process_tree(process_info):
    """Kill a process and all its children"""
    script_key = process_info.get('script_key', 'N/A')
    pid = None
    try:
        if 'log_file' in process_info and hasattr(process_info['log_file'], 'close'):
            try:
                if not process_info['log_file'].closed:
                    process_info['log_file'].close()
            except:
                pass
        process = process_info.get('process')
        if process and hasattr(process, 'pid'):
            pid = process.pid
            try:
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                gone, alive = psutil.wait_procs(children, timeout=2)
                for p in alive:
                    try:
                        p.kill()
                    except:
                        pass
                try:
                    parent.terminate()
                    parent.wait(timeout=2)
                except psutil.TimeoutExpired:
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass
            except psutil.NoSuchProcess:
                logger.warning(f"Process {pid} already gone")
            except Exception as e:
                logger.error(f"Error killing process: {e}")
    except Exception as e:
        logger.error(f"Error in kill_process_tree: {e}")

# --- Package Installation ---
TELEGRAM_MODULES = {
    'telebot': 'pytelegrambotapi',
    'telegram': 'python-telegram-bot',
    'pyrogram': 'pyrogram',
    'telethon': 'telethon',
    'aiogram': 'aiogram',
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'bs4': 'beautifulsoup4',
    'dotenv': 'python-dotenv',
    'yaml': 'pyyaml',
    'aiohttp': 'aiohttp',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'requests': 'requests',
    'flask': 'flask',
    'django': 'django',
    'fastapi': 'fastapi',
}

def attempt_install_pip(module_name, message):
    """Attempt to install a Python package with animation"""
    package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name)
    if package_name is None:
        return False
    try:
        msg = send_spinner_animation(message.chat.id, f"Installing {package_name}...", duration=2)
        command = [sys.executable, '-m', 'pip', 'install', package_name]
        result = subprocess.run(command, capture_output=True, text=True, check=False,
                                encoding='utf-8', errors='ignore', timeout=120)
        if result.returncode == 0:
            try:
                bot.edit_message_text(
                    f"✅ <b>Package Installed!</b>\n📦 <code>{package_name}</code> installed successfully!",
                    message.chat.id, msg.message_id, parse_mode='HTML'
                )
            except:
                bot.send_message(message.chat.id, f"✅ Package {package_name} installed!", parse_mode='HTML')
            return True
        else:
            error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
            try:
                bot.edit_message_text(
                    f"❌ <b>Installation Failed</b>\n<code>{error_msg}</code>",
                    message.chat.id, msg.message_id, parse_mode='HTML'
                )
            except:
                pass
            ret
