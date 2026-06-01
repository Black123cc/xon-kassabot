import telebot
import random
import threading
import time
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ===================== SOZLAMALAR =====================
TOKEN = "8667542060:AAGaZZ6XgpU32dNhISEEKENUwxMg30c6ihk"
ADMIN_ID = 8941268998
KARTA_RAQAM = "9860256601576083"
MIN_SUMMA = 5000
TOLOV_VAQTI = 15

bot = telebot.TeleBot(TOKEN)

# ===================== DATABASE =====================
users = {}
payments = {}
withdrawals = {}
user_state = {}
blocked_users = set()

# ===================== YORDAMCHI =====================
def get_user(user_id):
    if user_id not in users:
        users[user_id] = {"balance": 0, "username": "", "full_name": ""}
    return users[user_id]

def unique_amount(base):
    return base + random.randint(1, 99)

def fmt(amount):
    return f"{amount:,} so'm".replace(",", " ")

def set_state(uid, step, data=None):
    user_state[uid] = {"step": step, "data": data or {}}

def get_state(uid):
    return user_state.get(uid, {"step": None, "data": {}})

def clear_state(uid):
    user_state.pop(uid, None)

def is_blocked(uid):
    return uid in blocked_users

def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")

# ===================== KLAVIATURALAR =====================
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("💰 Hisob to'ldirish"), KeyboardButton("💸 Pul yechish"))
    kb.row(KeyboardButton("📋 Tarix"), KeyboardButton("📞 Admin bilan bog'lanish"))
    return kb

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📥 Kutayotgan to'lovlar"), KeyboardButton("📤 Kutayotgan yechimlar"))
    kb.row(KeyboardButton("💰 To'lov qo'shish"), KeyboardButton("📢 Habar tarqatish"))
    kb.row(KeyboardButton("🚫 Bloklash"), KeyboardButton("✅ Blokdan chiqarish"))
    kb.row(KeyboardButton("👥 Foydalanuvchilar"), KeyboardButton("📊 Statistika"))
    kb.row(KeyboardButton("🔙 Asosiy menu"))
    return kb

def yes_no_kb(prefix):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Ha", callback_data=f"{prefix}_yes"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"{prefix}_no")
    )
    return kb

def platform_kb(prefix):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎰 1XBet", callback_data=f"{prefix}_1xbet"))
    return kb

# ===================== CHEK GENERATSIYA =====================
def deposit_check(user_id, amount, payment_id, unique_amount, bet_id):
    return (
        f"✅ Amaliyot muvaffaqiyatli yakunlandi\n\n"
        f"ID: {payment_id[-6:]}\n\n"
        f"Berish: {fmt(amount)} 🇺🇿 UZS\n"
        f"Olish: {fmt(amount)} 🇺🇿 1XBET | ⚡\n\n"
        f"Qabul: 9860256601576083 (OK)\n"
        f"O'tkazma: {unique_amount} ID\n\n"
        f"Sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

def withdraw_pending_check(user_id, amount, wit_id, platform, bet_id):
    return (
        f"🆔: {wit_id[-6:]}\n"
        f"🗓 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"🔄 Arizangiz qayta ishlashga yuborildi.\n"
        f"Iltimos, tasdiqlashni kuting."
    )

def withdraw_approved_check(user_id, amount, wit_id, platform, bet_id, card):
    return (
        f"✅ Amaliyot muvaffaqiyatli yakunlandi\n\n"
        f"ID: {wit_id[-6:]}\n\n"
        f"Berish: 🇺🇿 1XBET | ⚡\n"
        f"Olish: 🇺🇿 UZS\n\n"
        f"Qabul: {card} (OK)\n"
        f"O'tkazma: {bet_id} ID\n\n"
        f"Sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

# ===================== START =====================
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    clear_state(uid)
    if is_blocked(uid):
        bot.send_message(message.chat.id, "🚫 Siz bloklangansiz. Admin bilan bog'laning.")
        return
    if uid == ADMIN_ID:
        user = get_user(uid)
        user["username"] = message.from_user.username or ""
        user["full_name"] = message.from_user.full_name or ""
        bot.send_message(message.chat.id,
            "👑 <b>Xush kelibsiz, Admin!</b>\n\n🤖 <b>Xon Kassa</b> boshqaruv paneli",
            parse_mode="HTML", reply_markup=admin_kb())
        return
    # Agar foydalanuvchi ro'yxatdan o'tmagan bo'lsa
    user = get_user(uid)
    if not user.get("phone"):
        phone_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        phone_kb.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
        bot.send_message(message.chat.id,
            f"👋 <b>Xush kelibsiz, {message.from_user.first_name}!</b>\n\n"
            f"🏦 <b>Xon Kassa</b> — bukmekerlik hisobi boshqaruvi\n\n"
            f"🔐 Davom etish uchun telefon raqamingizni yuboring:",
            parse_mode="HTML", reply_markup=phone_kb)
    else:
        user["username"] = message.from_user.username or ""
        user["full_name"] = message.from_user.full_name or ""
        bot.send_message(message.chat.id,
            f"👋 <b>Xush kelibsiz, {message.from_user.first_name}!</b>\n\n"
            f"🏦 <b>Xon Kassa</b>",
            parse_mode="HTML", reply_markup=main_kb())

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    uid = message.from_user.id
    if message.contact and message.contact.user_id == uid:
        user = get_user(uid)
        user["phone"] = message.contact.phone_number
        user["username"] = message.from_user.username or ""
        user["full_name"] = message.from_user.full_name or ""
        bot.send_message(message.chat.id,
            f"✅ <b>Ro'yxatdan o'tdingiz!</b>\n\n"
            f"📱 Raqam: <code>{message.contact.phone_number}</code>\n\n"
            f"Xush kelibsiz! 🎉",
            parse_mode="HTML", reply_markup=main_kb())
    else:
        bot.send_message(message.chat.id, "❌ Iltimos, o'z raqamingizni yuboring!")

# ===================== ASOSIY HANDLER =====================
@bot.message_handler(func=lambda m: True, content_types=["text", "photo"])
def handle_all(message):
    uid = message.from_user.id

    if is_blocked(uid) and uid != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 Siz bloklangansiz.")
        return

    state = get_state(uid)
    step = state["step"]
    data = state["data"]

    # ========== ADMIN ==========
    if uid == ADMIN_ID:

        if message.text == "📥 Kutayotgan to'lovlar":
            pending = [(pid, p) for pid, p in payments.items() if p["status"] == "checking"]
            if not pending:
                bot.send_message(message.chat.id, "✅ Kutayotgan to'lovlar yo'q.")
                return
            for pid, p in pending:
                u = get_user(p["user_id"])
                uname = f"@{u['username']}" if u['username'] else u['full_name']
                kb = InlineKeyboardMarkup()
                kb.row(
                    InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"dep_approve_{pid}"),
                    InlineKeyboardButton("❌ Rad etish", callback_data=f"dep_reject_{pid}")
                )
                caption = (
                    f"💰 <b>To'lov so'rovi</b>\n\n"
                    f"👤 {uname} (ID: {p['user_id']})\n"
                    f"🎰 {p.get('platform','')}\n"
                    f"🆔 Bet ID: <code>{p.get('bet_id','')}</code>\n"
                    f"💵 Kerakli: {fmt(p['amount'])}\n"
                    f"🎯 Unique: {fmt(p['unique_amount'])}\n"
                    f"📅 {now_str()}"
                )
                if p.get("check_file"):
                    bot.send_photo(ADMIN_ID, p["check_file"], caption=caption, parse_mode="HTML", reply_markup=kb)
                else:
                    bot.send_message(ADMIN_ID, caption, parse_mode="HTML", reply_markup=kb)
            return

        if message.text == "📤 Kutayotgan yechimlar":
            pending = [(wid, w) for wid, w in withdrawals.items() if w["status"] == "pending"]
            if not pending:
                bot.send_message(message.chat.id, "✅ Kutayotgan yechimlar yo'q.")
                return
            for wid, w in pending:
                u = get_user(w["user_id"])
                uname = f"@{u['username']}" if u['username'] else u['full_name']
                card = w["card"]
                card_fmt = f"{card[0:4]} {card[4:8]} {card[8:12]} {card[12:16]}"
                kb = InlineKeyboardMarkup()
                kb.row(
                    InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"wit_approve_{wid}"),
                    InlineKeyboardButton("❌ Rad etish", callback_data=f"wit_reject_{wid}")
                )
                bot.send_message(ADMIN_ID,
                    f"💸 <b>Yechish so'rovi</b>\n\n"
                    f"👤 {uname} (ID: {w['user_id']})\n"
                    f"🎰 {w.get('platform','')}\n"
                    f"🆔 Bet ID: <code>{w.get('bet_id','')}</code>\n"
                    f"💳 Karta: <code>{card_fmt}</code>\n"
                    f"🔑 Kod: <code>{w.get('code','')}</code>\n"
                    f"📅 {now_str()}",
                    parse_mode="HTML", reply_markup=kb)
            return

        if message.text == "💰 To'lov qo'shish":
            set_state(uid, "admin_add_payment")
            bot.send_message(message.chat.id,
                "💰 <b>Foydalanuvchiga to'lov qo'shish</b>\n\n"
                "Foydalanuvchi Telegram ID sini kiriting:",
                parse_mode="HTML")
            return

        if message.text == "📢 Habar tarqatish":
            set_state(uid, "admin_broadcast")
            bot.send_message(message.chat.id,
                "📢 <b>Habar tarqatish</b>\n\nBarcha foydalanuvchilarga yuboriladigan habarni kiriting:",
                parse_mode="HTML")
            return

        if message.text == "🚫 Bloklash":
            set_state(uid, "admin_block")
            bot.send_message(message.chat.id,
                "🚫 <b>Foydalanuvchi bloklash</b>\n\nTelegram ID kiriting:",
                parse_mode="HTML")
            return

        if message.text == "✅ Blokdan chiqarish":
            set_state(uid, "admin_unblock")
            bot.send_message(message.chat.id,
                "✅ <b>Blokdan chiqarish</b>\n\nTelegram ID kiriting:",
                parse_mode="HTML")
            return

        if message.text == "👥 Foydalanuvchilar":
            if not users:
                bot.send_message(message.chat.id, "👥 Hech kim yo'q.")
                return
            text = f"👥 <b>Foydalanuvchilar ({len(users)} ta):</b>\n\n"
            for uid2, u in list(users.items())[:30]:
                uname = f"@{u['username']}" if u['username'] else u['full_name']
                blok = " 🚫" if uid2 in blocked_users else ""
                text += f"• {uname} ({uid2}){blok}\n"
            bot.send_message(message.chat.id, text, parse_mode="HTML")
            return

        if message.text == "📊 Statistika":
            dep_ok = len([p for p in payments.values() if p["status"] == "approved"])
            dep_sum = sum(p["amount"] for p in payments.values() if p["status"] == "approved")
            wit_ok = len([w for w in withdrawals.values() if w["status"] == "approved"])
            bot.send_message(message.chat.id,
                f"📊 <b>Statistika:</b>\n\n"
                f"👥 Foydalanuvchilar: {len(users)}\n"
                f"🚫 Bloklangan: {len(blocked_users)}\n"
                f"📥 Tasdiqlangan to'lovlar: {dep_ok} ta\n"
                f"💰 Jami to'ldirilgan: {fmt(dep_sum)}\n"
                f"📤 Tasdiqlangan yechimlar: {wit_ok} ta\n"
                f"📋 Jami to'lovlar: {len(payments)}\n"
                f"📋 Jami yechimlar: {len(withdrawals)}",
                parse_mode="HTML")
            return

        if message.text == "🔙 Asosiy menu":
            clear_state(uid)
            bot.send_message(message.chat.id, "Admin panel:", reply_markup=admin_kb())
            return

        # Admin holatlari
        if step == "admin_add_payment":
            try:
                target_id = int(message.text.strip())
            except:
                bot.send_message(message.chat.id, "❌ Noto'g'ri ID!")
                return
            if target_id not in users:
                bot.send_message(message.chat.id, "❌ Bu foydalanuvchi topilmadi!")
                return
            set_state(uid, "admin_add_amount", {"target_id": target_id})
            u = get_user(target_id)
            uname = f"@{u['username']}" if u['username'] else u['full_name']
            bot.send_message(message.chat.id,
                f"👤 Foydalanuvchi: {uname}\n\nQancha summa qo'shilsin?",
                parse_mode="HTML")
            return

        if step == "admin_add_amount":
            try:
                amount = int(message.text.replace(" ", "").replace(",", ""))
            except:
                bot.send_message(message.chat.id, "❌ Faqat raqam!")
                return
            target_id = data["target_id"]
            u = get_user(target_id)
            u["balance"] += amount
            uname = f"@{u['username']}" if u['username'] else u['full_name']
            clear_state(uid)
            bot.send_message(message.chat.id,
                f"✅ {uname} ga {fmt(amount)} qo'shildi!\n"
                f"Yangi balans: {fmt(u['balance'])}",
                parse_mode="HTML")
            bot.send_message(target_id,
                f"💰 <b>Hisobingizga {fmt(amount)} qo'shildi!</b>\n"
                f"Admin tomonidan.",
                parse_mode="HTML")
            return

        if step == "admin_broadcast":
            count = 0
            for user_id in users:
                if user_id != ADMIN_ID and user_id not in blocked_users:
                    try:
                        if message.photo:
                            bot.send_photo(user_id, message.photo[-1].file_id,
                                caption=message.caption or "", parse_mode="HTML")
                        else:
                            bot.send_message(user_id, message.text, parse_mode="HTML")
                        count += 1
                    except:
                        pass
            clear_state(uid)
            bot.send_message(message.chat.id,
                f"✅ Habar {count} ta foydalanuvchiga yuborildi!",
                reply_markup=admin_kb())
            return

        if step == "admin_block":
            try:
                target_id = int(message.text.strip())
            except:
                bot.send_message(message.chat.id, "❌ Noto'g'ri ID!")
                return
            blocked_users.add(target_id)
            clear_state(uid)
            bot.send_message(message.chat.id, f"✅ {target_id} bloklandi!")
            return

        if step == "admin_unblock":
            try:
                target_id = int(message.text.strip())
            except:
                bot.send_message(message.chat.id, "❌ Noto'g'ri ID!")
                return
            blocked_users.discard(target_id)
            clear_state(uid)
            bot.send_message(message.chat.id, f"✅ {target_id} blokdan chiqarildi!")
            return

    # ========== FOYDALANUVCHI ==========

    if message.text == "💰 Hisob to'ldirish":
        clear_state(uid)
        bot.send_message(message.chat.id,
            "💰 <b>Hisob to'ldirish</b>\n\nQaysi platforma?",
            parse_mode="HTML", reply_markup=platform_kb("dep"))
        return

    if message.text == "💸 Pul yechish":
        clear_state(uid)
        bot.send_message(message.chat.id,
            "💸 <b>Pul yechish</b>\n\nQaysi platforma?",
            parse_mode="HTML", reply_markup=platform_kb("wit"))
        return

    if message.text == "📋 Tarix":
        user_pays = [(pid, p) for pid, p in payments.items() if p["user_id"] == uid]
        user_wits = [(wid, w) for wid, w in withdrawals.items() if w["user_id"] == uid]
        if not user_pays and not user_wits:
            bot.send_message(message.chat.id, "📋 Tarix bo'sh.")
            return
        text = "📋 <b>Oxirgi amallar:</b>\n\n"
        emoji_map = {"approved": "✅", "rejected": "❌", "pending": "⏳",
                     "checking": "🔍", "cancelled": "🚫", "expired": "⏰"}
        for pid, p in user_pays[-5:]:
            e = emoji_map.get(p["status"], "❓")
            text += f"{e} To'ldirish: {fmt(p['amount'])} — {p['status']}\n"
        for wid, w in user_wits[-5:]:
            e = emoji_map.get(w["status"], "❓")
            text += f"{e} Yechish — {w['status']}\n"
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        return

    if message.text == "📞 Admin bilan bog'lanish":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("👨‍💼 @Kassachi_Aka", url="https://t.me/Kassachi_Aka"))
        bot.send_message(message.chat.id,
            "📞 <b>Admin bilan bog'lanish:</b>",
            parse_mode="HTML", reply_markup=kb)
        return

    # ========== HOLATLAR ==========

    # DEPOSIT: ID kiritish
    if step == "dep_id":
        bet_id = message.text.strip() if message.text else ""
        if not bet_id.isdigit() or not (9 <= len(bet_id) <= 12):
            bot.send_message(message.chat.id,
                "❌ <b>ID topilmadi!</b>\n\nID 9-12 raqamdan iborat bo'lishi kerak.\nQaytadan kiriting:",
                parse_mode="HTML")
            return
        data["bet_id"] = bet_id
        set_state(uid, "dep_id_confirm", data)
        bot.send_message(message.chat.id,
            f"📋 <b>Ma'lumotlar to'g'rimi?</b>\n\n"
            f"🎰 Platforma: <b>{data['platform']}</b>\n"
            f"🆔 ID: <b>{bet_id}</b>",
            parse_mode="HTML", reply_markup=yes_no_kb("dep_id"))
        return

    # DEPOSIT: Summa
    if step == "dep_amount":
        try:
            amount = int(message.text.replace(" ", "").replace(",", ""))
        except:
            bot.send_message(message.chat.id, "❌ Faqat raqam kiriting!")
            return
        if amount < MIN_SUMMA:
            bot.send_message(message.chat.id,
                f"❌ Minimum: <b>{fmt(MIN_SUMMA)}</b>", parse_mode="HTML")
            return
        u_amount = unique_amount(amount)
        pid = f"DEP{uid}{int(datetime.now().timestamp())}"
        payments[pid] = {
            "user_id": uid, "platform": data.get("platform", ""),
            "bet_id": data.get("bet_id", ""), "amount": amount,
            "unique_amount": u_amount, "status": "pending",
            "time": datetime.now(), "check_file": None
        }
        data["payment_id"] = pid
        set_state(uid, "dep_check", data)
        karta = KARTA_RAQAM
        kf = f"{karta[0:4]} {karta[4:8]} {karta[8:12]} {karta[12:16]}"
        cancel_kb = InlineKeyboardMarkup()
        cancel_kb.add(InlineKeyboardButton("❌ Bekor qilish", callback_data=f"dep_cancel_{pid}"))
        bot.send_message(message.chat.id,
            f"💳 <b>To'lov ma'lumotlari:</b>\n\n"
            f"🏦 Karta: <code>{kf}</code>\n"
            f"💰 Aynan shu summani o'tkazing: <b>{fmt(u_amount)}</b>\n\n"
            f"⚠️ Boshqa summa o'tkazilsa tasdiqlanmaydi!\n\n"
            f"⏱ Vaqt: <b>{TOLOV_VAQTI} daqiqa</b>\n\n"
            f"To'lovdan keyin <b>chek rasmini</b> yuboring:",
            parse_mode="HTML", reply_markup=cancel_kb)
        threading.Thread(target=auto_cancel, args=(pid, uid, TOLOV_VAQTI * 60), daemon=True).start()
        return

    # DEPOSIT: Chek rasm
    if step == "dep_check":
        pid = data.get("payment_id")
        if not pid or pid not in payments:
            bot.send_message(message.chat.id, "❌ To'lov topilmadi.")
            clear_state(uid)
            return
        p = payments[pid]
        if p["status"] != "pending":
            bot.send_message(message.chat.id, "❌ To'lov bekor qilingan.")
            clear_state(uid)
            return
        if message.photo:
            p["check_file"] = message.photo[-1].file_id
            p["status"] = "checking"
            clear_state(uid)
            bot.send_message(message.chat.id,
                "✅ <b>Chek qabul 
