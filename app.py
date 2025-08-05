from flask import Flask
import threading, requests, time

app = Flask(__name__)

TOKEN = 'BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF'
API_URL = f'https://messengerg2c37.iranl.ms/bot{TOKEN}/'
waiting_users = []
active_chats = {}

def bot_loop():
    last_update_id = None
    while True:
        try:
            res = requests.get(API_URL + 'getUpdates', params={'offset': last_update_id})
            data = res.json()
            if data.get('ok'):
                for upd in data['result']:
                    last_update_id = upd['update_id'] + 1
                    msg = upd.get('message', {})
                    user = msg.get('chat', {}).get('id')
                    text = msg.get('text', '')
                    if text == '/start':
                        requests.post(API_URL + 'sendMessage', data={'chat_id': user, 'text': 'منتظر بقیه‌م...'})
                        if user not in waiting_users and user not in active_chats:
                            waiting_users.append(user)
                        if len(waiting_users) >= 2:
                            u1 = waiting_users.pop(0); u2 = waiting_users.pop(0)
                            active_chats[u1] = u2; active_chats[u2] = u1
                            for u in (u1, u2):
                                requests.post(API_URL + 'sendMessage', data={'chat_id': u, 'text': '✅ وصل شدی! حاضری؟'})
                    elif user in active_chats:
                        partner = active_chats[user]
                        requests.post(API_URL + 'sendMessage', data={'chat_id': partner, 'text': text})
        except Exception as e:
            print("خطا:", e)
        time.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
