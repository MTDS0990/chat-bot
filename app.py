# app.py
from flask import Flask, request, jsonify
import requests
import sqlite3
import os
import threading
import time

app = Flask(__name__)

# ====== تنظیمات ======
BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
API_BASE = "https://botapi.rubika.ir/v3"
API_PREFIX = f"{API_BASE}/{BOT_TOKEN}"   # -> https://botapi.rubika.ir/v3/{token}

DB_PATH = os.environ.get("BOT_DB", "bot.db")  # می‌تونی با env تغییرش بدی

# ====== دیتابیس ساده SQLite برای ذخیره کاربران و وضعیت چت ======
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id TEXT PRIMARY KEY,
        gender TEXT,
        target TEXT,
        step TEXT,
        partner TEXT
    )
    """)
    conn.commit()
    conn.close()

def db_get_user(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT chat_id,gender,target,step,partner FROM users WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"chat_id": row[0], "gender": row[1], "target": row[2], "step": row[3], "partner": row[4]}

def db_upsert_user(chat_id, gender=None, target=None, step=None, partner=None):
    u = db_get_user(chat_id)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if u:
        cur.execute("""
            UPDATE users SET gender=COALESCE(?,gender), target=COALESCE(?,target), step=COALESCE(?,step), partner=COALESCE(?,partner)
            WHERE chat_id=?
        """, (gender, target, step, partner, chat_id))
    else:
        cur.execute("INSERT INTO users(chat_id,gender,target,step,partner) VALUES (?,?,?,?,?)",
                    (chat_id, gender, target, step, partner))
    conn.commit()
    conn.close()

def db_set_partner(a, b):
    db_upsert_user(a, partner=b, step="chatting")
    db_upsert_user(b, partner=a, step="chatting")

def db_clear_partner(a):
    u = db_get_user(a)
    partner = u.get("partner") if u else None
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET partner=NULL, step='choose_gender' WHERE chat_id=?", (a,))
    if partner:
        cur.execute("UPDATE users SET partner=NULL, step='choose_gender' WHERE chat_id=?", (partner,))
    conn.commit()
    conn.close()

def db_list_waiting():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT chat_id,gender,target FROM users WHERE step='waiting'")
    rows = cur.fetchall()
    conn.close()
    return [{"chat_id": r[0], "gender": r[1], "target": r[2]} for r in rows]

# ====== توابع کمکی برای صدا زدن API روبیکا ======
def rubika_post(method, payload):
    url = f"{API_PREFIX}/{method}"
    try:
        res = requests.post(url, json=payload, timeout=10)
        # لاگ وضعیت برای دیباگ در لاگ‌های Render
        print(f"Rubika POST {method} -> status: {res.status_code}, text: {res.text}")
        return res
    except Exception as e:
        print("ERROR calling rubika:", e)
        return None

def send_text(chat_id, text, inline_keypad=None):
    data = {"chat_id": chat_id, "text": text}
    if inline_keypad:
        # ساختار inline_keypad طبق مستندات: {"rows":[[button,...],[...]]}
        data["inline_keypad"] = {"rows": inline_keypad}
    return rubika_post("sendMessage", data)

def forward_message(from_chat_id, message_id, to_chat_id):
    data = {"from_chat_id": from_chat_id, "message_id": message_id, "to_chat_id": to_chat_id}
    return rubika_post("forwardMessage", data)

# ====== منطق جفت‌کردن (matching) ======
def match_once():
    waiting = db_list_waiting()
    used = set()
    for i in range(len(waiting)):
        a = waiting[i]
        if a["chat_id"] in used: continue
        for j in range(i+1, len(waiting)):
            b = waiting[j]
            if b["chat_id"] in used: continue

            # تطابق براساس ترجیحات: اگر a.target == 'any' یا برابر جنس b و بالعکس
            a_target = a["target"]
            b_target = b["target"]
            a_gender = a["gender"]
            b_gender = b["gender"]

            def match_pref(t, g_other):
                return (t == "any") or (t == g_other)

            if match_pref(a_target, b_gender) and match_pref(b_target, a_gender):
                # جفت‌شون کن
                db_set_partner(a["chat_id"], b["chat_id"])
                # پیام اطلاع‌رسانی به هر دو
                send_text(a["chat_id"], "🎉 به یک نفر وصل شدی! حالا می‌تونی پیام بدی.\nبرای پایان چت از دکمه زیر استفاده کن.",
                          inline_keypad=[[{"text":"❌ پایان چت","command":"end"}]])
                send_text(b["chat_id"], "🎉 به یک نفر وصل شدی! حالا می‌تونی پیام بدی.\nبرای پایان چت از دکمه زیر استفاده کن.",
                          inline_keypad=[[{"text":"❌ پایان چت","command":"end"}]])
                used.add(a["chat_id"]); used.add(b["chat_id"])
                break

# می‌تونیم یک ری‌تایمر در پس‌زمینه برای تلاش matching بزنیم (اختیاری)
def background_matcher():
    while True:
        try:
            match_once()
        except Exception as e:
            print("Matcher error:", e)
        time.sleep(2)

# ====== پردازش آپدیت ورودی روبیکا ======
@app.route("/", methods=["GET"])
def index():
    return "ربات ناشناس روبیکا فعال است ✅"

@app.route("/receiveUpdate", methods=["POST"])
def receive_update():
    data = request.get_json() or {}
    # بعضی‌ها payload را مستقیم با کلید 'update' می‌فرستن و بعضی‌ها مستقیم، سازگارسازی:
    update = data.get("update") or data

    print("📥 update:", update)

    try:
        if update.get("type") != "NewMessage":
            return jsonify({"status":"OK"})

        chat_id = update.get("chat_id")
        msg = update.get("new_message", {})
        text = msg.get("text", "")
        message_id = msg.get("message_id")
        # ممکن است فایل در new_message باشد:
        file_inline = msg.get("file_inline")  # اگر روبیکا این فیلد را فرستاد
        # بعضی ورژن‌ها ممکنه فیلدهای مختلف داشته باشند؛ چک محافظه‌کارانه:
        if not file_inline and msg.get("type") == "file":
            file_inline = msg.get("file_inline")

        # اگر کاربر جدید است، ایجاد رکورد
        if not db_get_user(chat_id):
            db_upsert_user(chat_id, gender=None, target=None, step="choose_gender", partner=None)

        user = db_get_user(chat_id)

        # اگر کاربر در چت است (partner دارد)، پیام یا فایل باید فوروارد شود
        if user and user.get("partner"):
            partner = user.get("partner")
            if file_inline and message_id:
                # از forwardMessage استفاده می‌کنیم (فراخوانی API)
                forward_message(chat_id, message_id, partner)
                return jsonify({"status":"OK"})
            if text:
                send_text(partner, text)
                return jsonify({"status":"OK"})
            return jsonify({"status":"OK"})

        # مرحله‌ها: choose_gender -> waiting (پس از انتخاب target) -> chatting
        # دستور استارت
        if text == "/start":
            db_upsert_user(chat_id, gender=None, target=None, step="choose_gender", partner=None)
            keyboard = [[{"text":"👨 پسر","command":"gender_male"}, {"text":"👩 دختر","command":"gender_female"}]]
            send_text(chat_id, "سلام! جنسیت خود را انتخاب کن:", inline_keypad=keyboard)
            return jsonify({"status":"OK"})

        # دریافت انتخاب جنسیت (ارسال کاربر با متن یا با دکمه)
        if user.get("step") == "choose_gender" and text in ["👨 پسر","👩 دختر","پسر","دختر","male","female"]:
            # نرمالایز کن
            gender = "male" if "پسر" in text or "male" in text else "female"
            db_upsert_user(chat_id, gender=gender, step="choose_target")
            keyboard = [[{"text":"🚀 شروع چت","command":"start_chat"}]]
            send_text(chat_id, "خوبه ✅\nحالا روی «شروع چت» بزن:", inline_keypad=keyboard)
            return jsonify({"status":"OK"})

        # کاربر روی شروع چت زده
        if text == "🚀 شروع چت" or text.lower() == "start_chat":
            # ارسال انتخاب target
            keyboard = [[
                {"text":"👩 دختر","command":"target_female"},
                {"text":"👨 پسر","command":"target_male"},
                {"text":"🎯 فرقی نداره","command":"target_any"}
            ]]
            send_text(chat_id, "می‌خوای با چه کسی چت کنی؟", inline_keypad=keyboard)
            return jsonify({"status":"OK"})

        # دریافت انتخاب target
        if user.get("step") == "choose_target" and text in ["👩 دختر","👨 پسر","🎯 فرقی نداره","دختر","پسر","فرقی نداره","any"]:
            if "دختر" in text or "female" in text:
                target = "female"
            elif "پسر" in text or "male" in text:
                target = "male"
            else:
                target = "any"
            db_upsert_user(chat_id, target=target, step="waiting")
            send_text(chat_id, "⏳ در حال جستجو برای یافتن یک هم‌صحبت مناسب... لطفاً صبور باشید.", inline_keypad=[[{"text":"❌ پایان چت","command":"end"}]])
            # تلاش برای جفت‌کردن
            match_once()
            return jsonify({"status":"OK"})

        # پایان چت (اگر کاربر خودش دستور پایان فرستاد)
        if text in ["❌ پایان چت","end","پایان چت"]:
            partner = user.get("partner")
            if partner:
                send_text(partner, "❌ طرف مقابل چت را پایان داد. اگر خواستی دوباره شروع کن.", inline_keypad=[[{"text":"🚀 شروع چت","command":"start_chat"}]])
            db_clear_partner(chat_id)
            send_text(chat_id, "✅ چت پایان یافت. برای شروع دوباره /start بزن یا از دکمه‌ها استفاده کن.", inline_keypad=[[{"text":"👨 پسر","command":"gender_male"}, {"text":"👩 دختر","command":"gender_female"}]])
            return jsonify({"status":"OK"})

        # حالت پیش‌فرض: اگر کاربر قبلاً مرحله‌ای داشت، راهنمایی کن
        if user.get("step") == "choose_gender":
            keyboard = [[{"text":"👨 پسر","command":"gender_male"}, {"text":"👩 دختر","command":"gender_female"}]]
            send_text(chat_id, "لطفاً جنسیت خود را انتخاب کن:", inline_keypad=keyboard)
            return jsonify({"status":"OK"})

        if user.get("step") == "choose_target":
            keyboard = [[
                {"text":"👩 دختر","command":"target_female"},
                {"text":"👨 پسر","command":"target_male"},
                {"text":"🎯 فرقی نداره","command":"target_any"}
            ]]
            send_text(chat_id, "می‌خوای با چه کسی چت کنی؟", inline_keypad=keyboard)
            return jsonify({"status":"OK"})

    except Exception as e:
        print("ERROR in receive_update:", e)

    return jsonify({"status":"OK"})

# ====== اجرا و راه‌اندازی دیتابیس و تایمر matching ======
if __name__ == "__main__":
    init_db()
    # اجرای matcher در پس‌زمینه (اختیاری ولی مفید)
    t = threading.Thread(target=background_matcher, daemon=True)
    t.start()
    # Render پورتی به صورت ENV می‌دهد؛ نیازی به ست کردن دستی نیست.
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
