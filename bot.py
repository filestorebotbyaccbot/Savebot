# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, LOGIN_SYSTEM

# --- SAFE WEB SERVER PORT BINDING ---
def run_web_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        server_address = ("", port)
        
        class HealthCheckHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Bot is Running Alive 24/7 Powered by @VJ_Bots")

        httpd = HTTPServer(server_address, HealthCheckHandler)
        print(f"🌍 Web Service Port Binding Successful on Port: {port}")
        httpd.serve_forever()
    except OSError:
        # Agar port pehle se gunicorn ya flask ne le rakha hai, toh yeh error ignore ho jayega
        print("ℹ️ Port already bound by another service, skipping custom server.")
    except Exception as e:
        print(f"ℹ️ Web server notice: {e}")

# Thread ko start karenge, agar error aayega toh background mein handle ho jayega, bot crash nahi hoga
web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()
# --------------------------------------

if STRING_SESSION is not None and LOGIN_SYSTEM == False:
    TechVJUser = Client("TechVJ", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    TechVJUser.start()
else:
    TechVJUser = None

class Bot(Client):

    def __init__(self):
        super().__init__(
            "techvj login",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="TechVJ"),
            workers=150,
            sleep_threshold=5
        )

    async def start(self):
        await super().start()
        print('Bot Started Powered By @VJ_Bots')

    async def stop(self, *args):
        await super().stop()
        print('Bot Stopped Bye')

if __name__ == "__main__":
    bot = Bot()
    bot.run()

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
