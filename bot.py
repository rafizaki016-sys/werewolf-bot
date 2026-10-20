import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

games = {}
ROLES_POOL = ["Werewolf", "Seer", "Doctor", "Villager", "Villager", "Villager"]


def get_alive_players(chat_id):
    if chat_id not in games:
        return {}
    return {uid: p for uid, p in games[chat_id]["players"].items() if p["is_alive"]}


def check_win(chat_id):
    alive = get_alive_players(chat_id)
    werewolves = [uid for uid, p in alive.items() if p["role"] == "Werewolf"]
    others = [uid for uid, p in alive.items() if p["role"] != "Werewolf"]

    if len(werewolves) == 0:
        return "VILLAGERS"
    elif len(werewolves) >= len(others):
        return "WEREWOLVES"
    return None


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Halo {user.first_name}! Bot Werewolf aktif.\n"
        "Tambahkan bot ini ke grup untuk mulai bermain!"
    )


async def newgame_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        await update.message.reply_text("Perintah ini hanya bisa digunakan di dalam GRUP!")
        return

    games[chat_id] = {
        "phase": "LOBBY",
        "players": {},
        "night_actions": {},
        "votes": {},
        "day_count": 1
    }

    await update.message.reply_text(
        "🎮 **GAME WEREWOLF DIBUKA!**\n\n"
        "Ketik `/join` untuk bergabung ke dalam permainan.\n"
        "Minimal butuh 4 pemain untuk memulai."
    )


async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games or games[chat_id]["phase"] != "LOBBY":
        await update.message.reply_text("Tidak ada pendaftaran game yang terbuka di grup ini.")
        return

    if user.id in games[chat_id]["players"]:
        await update.message.reply_text(f"{user.first_name}, kamu sudah bergabung!")
        return

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text="Kamu telah mendaftar di game Werewolf grup!"
        )
    except Exception:
        await update.message.reply_text(
            f"⚠️ {user.first_name}, silakan buka PM ke bot terlebih dahulu dan klik /start agar bot bisa mengirimkan peran rahasiamu!"
        )
        return

    games[chat_id]["players"][user.id] = {
        "name": user.first_name,
        "role": None,
        "is_alive": True
    }

    total = len(games[chat_id]["players"])
    await update.message.reply_text(f"✅ {user.first_name} bergabung! Total pemain: {total}")


async def startgame_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games or games[chat_id]["phase"] != "LOBBY":
        await update.message.reply_text("Tidak ada lobby game aktif.")
        return

    players = games[chat_id]["players"]
    if len(players) < 4:
        await update.message.reply_text(f"Pemain belum cukup! Baru ada {len(players)}/4 pemain.")
        return

    uids = list(players.keys())
    shuffled_roles = random.sample(ROLES_POOL, len(uids)) if len(uids) <= len(ROLES_POOL) else random.choices(
        ROLES_POOL, k=len(uids))

    for uid, role in zip(uids, shuffled_roles):
        players[uid]["role"] = role
        players[uid]["is_alive"] = True
        await context.bot.send_message(
            chat_id=uid,
            text=f"📜 **PERAN RAHASIAMU:** [{role}]\n"
                 f"Jaga rahasia ini dari pemain lain!"
        )

    games[chat_id]["phase"] = "NIGHT"
    games[chat_id]["night_actions"] = {}
    games[chat_id]["votes"] = {}

    await update.message.reply_text(
        "🌕 **MALAM KE-1 TIBA** 🌕\n\n"
        "Semua warga desa tertidur...\n"
        "Pemain dengan peran khusus, periksa PM dari bot untuk menjalankan aksi malam!"
    )

    await prompt_night_actions(context, chat_id)


async def prompt_night_actions(context: ContextTypes.DEFAULT_TYPE, chat_id: str):
    alive = get_alive_players(chat_id)

    for uid, p in alive.items():
        role = p["role"]
        buttons = []

        if role in ["Werewolf", "Doctor", "Seer"]:
            for target_id, target_p in alive.items():
                if role == "Werewolf" and target_p["role"] == "Werewolf":
                    continue
                buttons.append([InlineKeyboardButton(
                    target_p["name"],
                    callback_data=f"night_{role.lower()}_{chat_id}_{target_id}"
                )])

            text_action = {
                "Werewolf": "🍖 Pilih korban yang ingin kamu mangsa malam ini:",
                "Doctor": "🛡️ Pilih pemain yang ingin kamu lindungi malam ini:",
                "Seer": "🔮 Pilih pemain yang ingin kamu terawang identitasnya:"
            }

            await context.bot.send_message(
                chat_id=uid,
                text=text_action[role],
                reply_markup=InlineKeyboardMarkup(buttons)
            )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    action_type = data[0]

    if action_type == "night":
        role_act, chat_id, target_id = data[1], int(data[2]), int(data[3])

        if chat_id not in games or games[chat_id]["phase"] != "NIGHT":
            await query.edit_message_text("Fase malam sudah berakhir.")
            return

        game = games[chat_id]
        game["night_actions"][role_act] = target_id

        if role_act == "seer":
            target_p = game["players"][target_id]
            await query.edit_message_text(
                f"🔮 Hasil Penerawangan: **{target_p['name']}** adalah **{target_p['role']}**!")
        else:
            await query.edit_message_text("✅ Aksi malammu telah dicatat.")

        alive = get_alive_players(chat_id)
        active_roles = set(p["role"].lower() for p in alive.values() if p["role"] in ["Werewolf", "Doctor", "Seer"])

        if active_roles.issubset(set(game["night_actions"].keys())):
            await resolve_night(context, chat_id)

    elif action_type == "vote":
        chat_id, target_id = int(data[1]), int(data[2])
        voter_id = query.from_user.id

        if chat_id not in games or games[chat_id]["phase"] != "DAY":
            await query.answer("Fase voting sudah selesai!", show_alert=True)
            return

        game = games[chat_id]
        if voter_id not in get_alive_players(chat_id):
            await query.answer("Pemain mati tidak bisa voting!", show_alert=True)
            return

        game["votes"][voter_id] = target_id
        voter_name = query.from_user.first_name
        target_name = game["players"][target_id]["name"]

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🗳️ **{voter_name}** memberikan suara untuk **{target_name}**."
        )

        alive = get_alive_players(chat_id)
        if len(game["votes"]) >= len(alive):
            await resolve_day(context, chat_id)


async def resolve_night(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    game = games[chat_id]
    actions = game["night_actions"]

    target_kill = actions.get("werewolf")
    target_heal = actions.get("doctor")

    log = "☀️ **MATAHARI TERBIT** ☀️\n\n"
    if target_kill and target_kill != target_heal:
        dead_player = game["players"][target_kill]
        dead_player["is_alive"] = False
        log += f"💀 Kabar duka! **{dead_player['name']}** tewas diserang Werewolf tadi malam!"
    else:
        log += "🛡️ Hari yang tenang! Tidak ada korban jiwa tadi malam."

    winner = check_win(chat_id)
    if winner:
        game["phase"] = "ENDED"
        await context.bot.send_message(chat_id=chat_id,
                                       text=f"{log}\n\n🎉 **GAME SELESAI!** Kemenangan untuk: **{winner}**")
        return

    game["phase"] = "DAY"
    game["votes"] = {}

    alive = get_alive_players(chat_id)
    buttons = []
    for uid, p in alive.items():
        buttons.append([InlineKeyboardButton(f"Vote {p['name']}", callback_data=f"vote_{chat_id}_{uid}")])

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"{log}\n\nSilakan berdiskusi! Tekan tombol di bawah untuk memilih pemain yang dieksekusi:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def resolve_day(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    game = games[chat_id]
    votes = game["votes"]

    tally = {}
    for target in votes.values():
        tally[target] = tally.get(target, 0) + 1

    executed_id = max(tally, key=tally.get)
    executed_player = game["players"][executed_id]
    executed_player["is_alive"] = False

    log = f"🔥 Hasil voting terbanyak: **{executed_player['name']}** dieksekusi!\n" \
          f"Identitas aslinya adalah: **{executed_player['role']}**"

    winner = check_win(chat_id)
    if winner:
        game["phase"] = "ENDED"
        await context.bot.send_message(chat_id=chat_id,
                                       text=f"{log}\n\n🎉 **GAME SELESAI!** Kemenangan untuk: **{winner}**")
        return

    game["phase"] = "NIGHT"
    game["night_actions"] = {}
    game["day_count"] += 1

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"{log}\n\n🌙 **MALAM KE-{game['day_count']} TIBA** 🌙\nSemua warga desa kembali tidur..."
    )
    await prompt_night_actions(context, chat_id)


if __name__ == "__main__":
    # 1. Masukkan TOKEN di paling atas blok ini
    TOKEN = "8871369922:AAHKYx15iRTA7c1RznDc-WWwBHhymC3-_84"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("newgame", newgame_cmd))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CommandHandler("startgame", startgame_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("🤖 Bot Werewolf Telegram berjalan...")
    # 2. Pastikan ada tanda kurung () di ujung run_polling
    app.run_polling()
