import requests
import threading
import time
import os
from flask import Flask

app = Flask(__name__)

# توکن ربات روبیکا
TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}/"

last_update_id = None

def handle_updates():
    global last_update_id
    print("✅ ربات روشن شد و در حال اجراست...")

    while True:
        try:
            response = requests.post(BASE_URL + "getUpdates", data={
                "offset_id": last_update_id or ""
            })
            result = response.json()

            for update in result.get("updates", []):
                last_update_id = update.get("update_id")
                message = update.get("message") or update.get("inline_message")
                if not message:
                    continue

                chat_id = message.get("chat_id")
                text = message.get("text", "")

                # پاسخ‌ها
                if text == "/start":
                    reply = "سلام! 👋 به ربات چت ناشناس خوش اومدی."
                else:
                    reply = "پیامت دریافت شد ✅"

                requests.post(BASE_URL + "sendMessage", data={
                    "chat_id": chat_id,
                    "text": reply
                })

        except Exception as e:
            print("❌ خطا:", e)

        time.sleep(2)  # وقفه بین هر بار چک کردن پیام

@app.route("/")
def index():
    return "🤖 ربات روبیکا فعال است و آماده پاسخگویی ✅"

if __name__ == "__main__":
    threading.Thread(target=handle_updates, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
