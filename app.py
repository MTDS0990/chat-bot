from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
URL = f"https://messengerg2c37.iranl.ms/bot{TOKEN}/sendMessage"

@app.route('/')
def home():
    return "رو بات روشنه :)"

@app.route('/receiveUpdate', methods=['POST'])
def receive_update():
    try:
        data = request.get_json()
        print("📥 پیام دریافت شد:", data)

        # چک کن که نوع آپدیت NewMessage باشه
        if data.get("update", {}).get("type") == "NewMessage":
            chat_id = data["update"]["chat_id"]
            message = data["update"]["new_message"]
            text = message.get("text", "")

            print("✉️ پیام کاربر:", text)

            reply = "سلام! خوش اومدی به چت‌بات ناشناس طاها 🤖"

            response = requests.post(URL, json={
                "chat_id": chat_id,
                "text": reply
            })

            print("✅ پاسخ ارسال شد.")
        else:
            print("⚠️ نوع آپدیت پشتیبانی نمی‌شود.")
    except Exception as e:
        print("❌ خطا در پردازش:", e)
    return "OK"

if __name__ == '__main__':
    app.run(debug=True)
