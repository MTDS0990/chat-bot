from flask import Flask
import threading, requests, time, os

app = Flask(__name__)

TOKEN = 'BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF'
API_URL = f'https://messengerg2c37.iranl.ms/bot{TOKEN}/'

waiting_users = []
active_chats = {}

def bot_loop():
    last_update_id = None
    print("✅ ربات راه‌اندازی شد و در حال اجراست...")
    while True:
        try:
            res = requests.get(API_URL + 'getUpdates', params={'offset': last_update_id}, timeout=10)
            data = res.json()

            if data.get('ok'):
                for upd in data['result']:
                    last_update_id = upd['update_id'] + 1
                    msg = upd.get('message', {})
                    user_id = msg.get('chat', {}).get('id')
                    text = msg.get('text', '')

                    if not user_id or not text:
                        continue

                    if text == '/start':
                        if user_id in active_chats:
                            continue
                        if user_id not in waiting_users:
                            waiting_users.append(user_id)
                            requests.post(API_URL + 'sendMessage', data={
                                'chat_id': user_id,
                                'text': '⏳ منتظر اتصال به فرد دیگر هستی...'
                            })
                        if len(waiting_users) >= 2:
                            u1 = waiting_users.pop(0)
                            u2 = waiting_users.pop(0)
                            active_chats[u1] = u2
                            active_chats[u2] = u1
                            for uid in (u1, u2):
                                requests.post(API_URL + 'sendMessage', data={
                                    'chat_id': uid,
                                    'text': '✅ شما به یک نفر متصل شدید. شروع کنید به چت!'
                                })

                    elif text == '/end':
                        if user_id in active_chats:
                            partner = active_chats.pop(user_id)
                            active_chats.pop(partner, None)
                            for uid in (user_id, partner):
                                requests.post(API_URL + 'sendMessage', data={
                                    'chat_id': uid,
                                    'text': '❌ چت پایان یافت. برای چت جدید /start را بزن.'
                                })
                        else:
                            requests.post(API_URL + 'sendMessage', data={
                                'chat_id': user_id,
                                'text': 'شما در حال حاضر با کسی در ارتباط نیستید.'
                            })

                    elif user_id in active_chats:
                        partner = active_chats.get(user_id)
                        if partner:
                            requests.post(API_URL + 'sendMessage', data={
                                'chat_id': partner,
                                'text': text
                            })

        except Exception as e:
            print('❌ خطا:', e)
        time.sleep(1)


if __name__ == '__main__':
    threading.Thread(target=bot_loop, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
