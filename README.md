# 🐺 Telegram Werewolf Game Bot

Bot Telegram interaktif berbasis Python untuk memainkan game party **Werewolf** di grup obrolan secara otomatis dan *real-time*. Bot mengelola sesi permainan, pendaftaran pemain, hingga pembagian peran rahasia melalui pesan pribadi (*Private Message*).

---

## 🚀 Fitur Utama
- **Group Game Management:** Sistem lobby permainan menggunakan perintah `/newgame`, `/join`, dan `/startgame`.
- **Private Role Assignment:** Pembagian peran rahasia dikirimkan langsung ke obrolan pribadi masing-masing pemain.
- **Asynchronous Processing:** Menangani banyak input perintah dari beberapa pemain sekaligus secara *real-time*.
- **24/7 Cloud Deployment:** Berjalan tanpa henti di infrastruktur server cloud (PythonAnywhere).

---

## 🛠️ Tech Stack
- **Language:** Python 3.x
- **Library:** `python-telegram-bot`
- **Version Control:** Git & GitHub
- **Hosting:** PythonAnywhere (Linux Cloud Server)

---

## 📦 Cara Menjalankan Secara Lokal

1. **Clone repository ini:**
   ```bash
   git clone [https://github.com/rafizaki016-sys/werewolf-bot.git](https://github.com/rafizaki016-sys/werewolf-bot.git)
   cd werewolf-bot

   Install dependensi:

Bash
pip install -r requirements.txt
Atur Token Bot:
Buka file bot.py dan masukkan API Token dari @BotFather pada variabel TOKEN:

Python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
Jalankan Bot:

Bash
python bot.py
☁️ Deployment
Bot ini dirancang untuk dapat dijalankan secara permanen (24/7) di server cloud menggunakan Bash Console pada PythonAnywhere.
