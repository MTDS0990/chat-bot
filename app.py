from flask import Flask, request import requests import random

app = Flask(name)

API_URL = "https://botapi.rubika.ir/v3" BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"

users = {}  # user_id: {"gender": "male"/"female", "target_gender": "any"/"male"/"female", "partner": None} waiting = []

def send_message(chat_id, text, buttons=None): data = { "bot_token": BOT_TOKEN, "chat_id": chat_id, "text": text, "type": "text" } if buttons: data["inline_buttons"] = buttons requests.post(f"{API_URL}/sendMessage", json=data)

def forward_file(from_chat_id, message_id, to_chat_id): data = { "bot_token": BOT_TOKEN, "from_chat_id": from_chat_id, "message_id": message_id, "chat_id": to_chat_id } requests.post(f"{API_URL}/forwardMessages", json=data)

@app.route("/") def home(): return "✅ Rubika Anonymous Chat Bot Active"

@app.route("/receiveUpdate", methods=["POST"]) def receive_update(): update = request.json.get("update") if not update: return "ok"

if update.get("type") == "NewMessage":
    chat_id = update["chat_id"]
    msg = update["new_message"]
    sender_id = msg["sender_id"]
    text = msg.get("text")
    msg_type = msg.get("type", "text")

    if sender_id not in users:
        users[sender_id] = {"step": "gender"}
        send_message(chat_id, "👋 خوش اومدی! جنسیتتو انتخاب کن:", [[{"text": "🙋‍♂️ پسر", "callback_data": "gender:male"}, {"text": "🙋‍♀️ دختر", "callback_data": "gender:female"}]])
        return "ok"

    if msg_type != "text":
        partner = users.get(sender_id, {}).get("partner")
        if partner:
            forward_file(chat_id, msg["message_id"], partner)
        else:
            send_message(chat_id, "❌ هنوز به کسی وصل نشدی!")
        return "ok"

    if text == "/start":
        users[sender_id] = {"step": "gender"}
        send_message(chat_id, "👋 خوش اومدی! جنسیتتو انتخاب کن:", [[{"text": "🙋‍♂️ پسر", "callback_data": "gender:male"}, {"text": "🙋‍♀️ دختر", "callback_data": "gender:female"}]])

    elif text == "/end":
        partner = users.get(sender_id, {}).get("partner")
        if partner:
            send_message(users[sender_id]["partner"], "❌ چت توسط طرف مقابل پایان یافت.")
            users[partner]["partner"] = None
        users[sender_id]["partner"] = None
        send_message(chat_id, "✅ چت پایان یافت.")

    else:
        partner = users.get(sender_id, {}).get("partner")
        if partner:
            send_message(partner, text)
        else:
            send_message(chat_id, "❌ هنوز به کسی وصل نشدی!")

elif update.get("type") == "CallbackQuery":
    data = update["data"]
    chat_id = update["chat_id"]
    user_id = update["user_id"]

    if data.startswith("gender:"):
        gender = data.split(":")[1]
        users[user_id]["gender"] = gender
        users[user_id]["step"] = "target_gender"
        send_message(chat_id, "میخوای با چه جنسیتی چت کنی؟", [[
            {"text": "👩 دختر", "callback_data": "target:female"},
            {"text": "👨 پسر", "callback_data": "target:male"},
            {"text": "👌 فرقی نداره", "callback_data": "target:any"}
        ]])

    elif data.startswith("target:"):
        target = data.split(":")[1]
        users[user_id]["target_gender"] = target
        users[user_id]["step"] = "chatting"
        users[user_id]["partner"] = None
        match_user(user_id, chat_id)

return "ok"

def match_user(user_id, chat_id): user = users[user_id] for uid in waiting: u = users[uid] if u["partner"] is None and match_condition(user, u): user["partner"] = uid u["partner"] = user_id waiting.remove(uid) send_message(chat_id, "✅ به یه نفر وصل شدی! برای پایان چت /end رو بفرست") send_message(uid, "✅ یه نفر بهت وصل شد! برای پایان چت /end رو بفرست") return

waiting.append(user_id)
send_message(chat_id, "⏳ در حال جستجوی طرف مقابل... لطفا صبور باش.")

def match_condition(user1, user2): # Check gender preferences return ( (user1["target_gender"] == "any" or user1["target_gender"] == user2["gender"]) and (user2["target_gender"] == "any" or user2["target_gender"] == user1["gender"]) )

if name == "main": import os port = int(os.environ.get("PORT", 10000)) app.run(host="0.0.0.0", port=port)

