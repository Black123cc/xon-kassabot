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
def main_kb(is_admin=False):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("💰 Hisob to'ldirish"), KeyboardButton("💸 Pul yechish"))
    kb.row(KeyboardButton("📋 Tarix"), KeyboardButton("📞 Admin bilan bog'lanish"))
    if is_admin:
        kb.row(KeyboardButton("⚙️ Admin panel"))
    return kb

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📥 Kutayotgan to'lovlar"), KeyboardButton("📤 Kutayotgan yechimlar"))
    kb.row(KeyboardButton("💰 To'lov qo'shish"), KeyboardButton("📢 Habar tarqatish"))
    kb.row(KeyboardButton("🚫 Bloklash"), KeyboardButton("✅ Blokdan chiqarish"))
    kb.row(KeyboardButton("👥 Foydalanuvchilar"), KeyboardButton("📊 Statistika"))
    kb.row(KeyboardButton("🔍 To'lovni topish"), KeyboardButton("🔍 Yechimni topish"))
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
        f"Berish: {amount:,} 🇺🇿 UZS\n"
        f"Olish: {amount:,} 🇺🇿 1XBET | ⚡\n\n"
        f"Qabul: 9860256601576083 (OK)\n"
        f"O'tkazma: {bet_id} ID\n\n"
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
    card_fmt = f"{card[0:4]} {card[4:8]} {card[8:12]} {card[12:16]}" if len(card) == 16 else card
    wit_num = ''.join(filter(str.isdigit, wit_id))[-6:]
    return (
        f"✅ Amaliyot muvaffaqiyatli yakunlandi\n\n"
        f"ID: {wit_num}\n\n"
        f"Berish: 🇺🇿 1XBET | ⚡\n"
        f"Olish: 🇺🇿 UZS\n\n"
        f"Qabul: {card_fmt} (OK)\n"
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
            "👑 <b>Xush kelibsiz, Admin!</b>\n\n🤖 <b>Xon Kassa</b>",
            parse_mode="HTML", reply_markup=main_kb(is_admin=True))
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
            parse_mode="HTML", reply_markup=main_kb(is_admin=False))

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    uid = message.from_user.id
    if message.contact and message.contact.user_id == uid:
        user = get_user(uid)
        user["phone"] = message.contact.phone_number
        user["username"] = message.from_user.username or ""
        user["full_name"] = message.from_user.full_name or ""
        is_adm = uid == ADMIN_ID
        bot.send_message(message.chat.id,
            f"✅ <b>Ro'yxatdan o'tdingiz!</b>\n\n"
            f"📱 Raqam: <code>{message.contact.phone_number}</code>\n\n"
            f"Xush kelibsiz! 🎉",
            parse_mode="HTML", reply_markup=main_kb(is_admin=is_adm))
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

        if message.text == "🔍 To'lovni topish":
            set_state(uid, "admin_search_payment")
            bot.send_message(message.chat.id,
                "🔍 <b>To'lovni topish</b>\n\nID yoki foydalanuvchi ID sini kiriting:",
                parse_mode="HTML")
            return

        if message.text == "🔍 Yechimni topish":
            set_state(uid, "admin_search_withdraw")
            bot.send_message(message.chat.id,
                "🔍 <b>Yechimni topish</b>\n\nID yoki foydalanuvchi ID sini kiriting:",
                parse_mode="HTML")
            return

        if message.text == "🔙 Asosiy menu":
            clear_state(uid)
            bot.send_message(message.chat.id, "Asosiy menu:", reply_markup=main_kb(is_admin=True))
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

        if step == "admin_search_payment":
            query = message.text.strip()
            found = []
            for pid, p in payments.items():
                if query in str(p["user_id"]) or query in pid:
                    found.append((pid, p))
            if not found:
                bot.send_message(message.chat.id, "❌ To'lov topilmadi!")
            else:
                for pid, p in found[-5:]:
                    u = get_user(p["user_id"])
                    uname = f"@{u['username']}" if u['username'] else u['full_name']
                    kb2 = InlineKeyboardMarkup()
                    kb2.row(
                        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"dep_approve_{pid}"),
                        InlineKeyboardButton("❌ Rad etish", callback_data=f"dep_reject_{pid}")
                    )
                    status_emoji = {"approved":"✅","rejected":"❌","pending":"⏳","checking":"🔍","cancelled":"🚫","expired":"⏰"}
                    bot.send_message(message.chat.id,
                        f"💰 <b>To'lov:</b>\n\n"
                        f"👤 {uname} (ID: {p['user_id']})\n"
                        f"🎰 {p.get('platform','')}\n"
                        f"🆔 Bet ID: {p.get('bet_id','')}\n"
                        f"💵 Summa: {fmt(p['amount'])}\n"
                        f"🎯 Unique: {fmt(p['unique_amount'])}\n"
                        f"📊 Holat: {status_emoji.get(p['status'], p['status'])}",
                        parse_mode="HTML",
                        reply_markup=kb2 if p["status"] == "checking" else None)
            clear_state(uid)
            return

        if step == "admin_search_withdraw":
            query = message.text.strip()
            found = []
            for wid, w in withdrawals.items():
                if query in str(w["user_id"]) or query in wid:
                    found.append((wid, w))
            if not found:
                bot.send_message(message.chat.id, "❌ Yechim topilmadi!")
            else:
                for wid, w in found[-5:]:
                    u = get_user(w["user_id"])
                    uname = f"@{u['username']}" if u['username'] else u['full_name']
                    card = w.get("card","")
                    cf = f"{card[0:4]} {card[4:8]} {card[8:12]} {card[12:16]}" if len(card)==16 else card
                    kb2 = InlineKeyboardMarkup()
                    kb2.row(
                        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"wit_approve_{wid}"),
                        InlineKeyboardButton("❌ Rad etish", callback_data=f"wit_reject_{wid}")
                    )
                    status_emoji = {"approved":"✅","rejected":"❌","pending":"⏳"}
                    bot.send_message(message.chat.id,
                        f"💸 <b>Yechim:</b>\n\n"
                        f"👤 {uname} (ID: {w['user_id']})\n"
                        f"🎰 {w.get('platform','')}\n"
                        f"🆔 Bet ID: {w.get('bet_id','')}\n"
                        f"💳 Karta: {cf}\n"
                        f"🔑 Kod: {w.get('code','')}\n"
                        f"📊 Holat: {status_emoji.get(w['status'], w['status'])}",
                        parse_mode="HTML",
                        reply_markup=kb2 if w["status"] == "pending" else None)
            clear_state(uid)
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

    if message.text == "⚙️ Admin panel" and uid == ADMIN_ID:
        clear_state(uid)
        bot.send_message(message.chat.id, "👑 <b>Admin panel:</b>", parse_mode="HTML", reply_markup=admin_kb())
        return

    if message.text == "📞 Admin bilan bog'lanish":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("👨‍💼 Qo'llab-quvvatlash", url="https://t.me/Kassachi_Aka"))
        bot.send_message(message.chat.id,
            "📞 <b>Savol, shikoyat, takliflar bo'lsa bizga\n"
            "murojaat qilishingiz mumkin!</b>\n\n"
            "👇 Adminga yozish 👇",
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
                "✅ <b>Chek qabul qilindi!</b>\n\nAdmin tekshirmoqda...",
                parse_mode="HTML", reply_markup=main_kb())
            u = get_user(uid)
            uname = f"@{u['username']}" if u['username'] else u['full_name']
            kb = InlineKeyboardMarkup()
            kb.row(
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"dep_approve_{pid}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"dep_reject_{pid}")
            )
            bot.send_photo(ADMIN_ID, p["check_file"],
                caption=f"💰 <b>Yangi to'lov!</b>\n\n"
                        f"👤 {uname} (ID: {uid})\n"
                        f"🎰 {p['platform']}\n"
                        f"🆔 Bet ID: <code>{p['bet_id']}</code>\n"
                        f"💵 Kerakli: {fmt(p['amount'])}\n"
                        f"🎯 Unique: {fmt(p['unique_amount'])}",
                parse_mode="HTML", reply_markup=kb)
        else:
            bot.send_message(message.chat.id, "📸 Chek <b>rasmini</b> yuboring!", parse_mode="HTML")
        return

    # WITHDRAW: ID kiritish
    if step == "wit_id":
        bet_id = message.text.strip() if message.text else ""
        if not bet_id.isdigit() or not (9 <= len(bet_id) <= 12):
            bot.send_message(message.chat.id,
                "❌ <b>ID topilmadi!</b>\n\nID 9-12 raqamdan iborat bo'lishi kerak.\nQaytadan kiriting:",
                parse_mode="HTML")
            return
        data["bet_id"] = bet_id
        set_state(uid, "wit_id_confirm", data)
        bot.send_message(message.chat.id,
            f"📋 <b>Ma'lumotlar to'g'rimi?</b>\n\n"
            f"🎰 Platforma: <b>{data['platform']}</b>\n"
            f"🆔 ID: <b>{bet_id}</b>",
            parse_mode="HTML", reply_markup=yes_no_kb("wit_id"))
        return

    # WITHDRAW: Karta
    if step == "wit_card":
        card = message.text.replace(" ", "") if message.text else ""
        if not card.isdigit() or len(card) != 16:
            bot.send_message(message.chat.id, "❌ Karta raqami noto'g'ri! 16 ta raqam kiriting.")
            return
        data["card"] = card
        set_state(uid, "wit_card_confirm", data)
        cf = f"{card[0:4]} {card[4:8]} {card[8:12]} {card[12:16]}"
        bot.send_message(message.chat.id,
            f"📋 <b>Ma'lumotlar to'g'rimi?</b>\n\n"
            f"🎰 Platforma: <b>{data['platform']}</b>\n"
            f"🆔 ID: <b>{data['bet_id']}</b>\n"
            f"💳 Karta: <code>{cf}</code>",
            parse_mode="HTML", reply_markup=yes_no_kb("wit_card"))
        return

    # WITHDRAW: Maxsus kod
    if step == "wit_code":
        code = message.text.strip() if message.text else ""
        if not code:
            bot.send_message(message.chat.id, "❌ Kodni kiriting!")
            return
        data["code"] = code
        set_state(uid, "wit_code_confirm", data)
        bot.send_message(message.chat.id,
            f"📋 <b>Ma'lumotlar to'g'rimi?</b>\n\n"
            f"🎰 Platforma: <b>{data['platform']}</b>\n"
            f"🆔 ID: <b>{data['bet_id']}</b>\n"
            f"🔑 Kod: <b>{code}</b>",
            parse_mode="HTML", reply_markup=yes_no_kb("wit_code"))
        return

# ===================== CALLBACK =====================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    uid = call.from_user.id
    cb = call.data

    # DEPOSIT platform
    if cb == "dep_1xbet":
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        set_state(uid, "dep_id", {"platform": "1XBet"})
        bot.send_message(call.message.chat.id,
            "🎰 <b>1XBet</b>\n\n🆔 Hisobingiz ID sini kiriting (9-12 raqam):",
            parse_mode="HTML")

    # DEPOSIT ID confirm
    elif cb == "dep_id_yes":
        state = get_state(uid)
        d = state["data"]
        set_state(uid, "dep_amount", d)
        bot.answer_callback_query(call.id, "✅")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id,
            f"💰 Qancha summa kiritmoqchisiz?\nMinimum: <b>{fmt(MIN_SUMMA)}</b>",
            parse_mode="HTML")

    elif cb == "dep_id_no":
        state = get_state(uid)
        d = state["data"]
        set_state(uid, "dep_id", d)
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, "🆔 ID ni qaytadan kiriting:")

    # DEPOSIT bekor
    elif cb.startswith("dep_cancel_"):
        pid = cb.replace("dep_cancel_", "")
        if pid in payments:
            payments[pid]["status"] = "cancelled"
        clear_state(uid)
        bot.answer_callback_query(call.id, "Bekor qilindi")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, "❌ To'lov bekor qilindi.", reply_markup=main_kb())

    # DEPOSIT tasdiqlash (admin)
    elif cb.startswith("dep_approve_"):
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Ruxsat yo'q!")
            return
        pid = cb.replace("dep_approve_", "")
        p = payments.get(pid)
        if not p or p["status"] != "checking":
            bot.answer_callback_query(call.id, "❌ Allaqachon ko'rib chiqilgan!")
            return
        p["status"] = "approved"
        user = get_user(p["user_id"])
        user["balance"] += p["amount"]
        bot.answer_callback_query(call.id, "✅ Tasdiqlandi!")
        try:
            bot.edit_message_caption(
                call.message.caption + "\n\n✅ <b>TASDIQLANDI</b>",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        except:
            pass
        bot.send_message(p["user_id"],
            deposit_check(p["user_id"], p["amount"], pid, p["unique_amount"], p["bet_id"]),
            parse_mode="HTML")

    # DEPOSIT rad (admin)
    elif cb.startswith("dep_reject_"):
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Ruxsat yo'q!")
            return
        pid = cb.replace("dep_reject_", "")
        p = payments.get(pid)
        if not p:
            bot.answer_callback_query(call.id, "❌ Topilmadi!")
            return
        p["status"] = "rejected"
        bot.answer_callback_query(call.id, "❌ Rad etildi!")
        try:
            bot.edit_message_caption(
                call.message.caption + "\n\n❌ <b>RAD ETILDI</b>",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        except:
            pass
        bot.send_message(p["user_id"],
            "❌ <b>To'lovingiz rad etildi!</b>\n\nMuammo bo'lsa admin bilan bog'laning.",
            parse_mode="HTML")

    # WITHDRAW platform
    elif cb == "wit_1xbet":
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        set_state(uid, "wit_id", {"platform": "1XBet"})
        bot.send_message(call.message.chat.id,
            "🎰 <b>1XBet</b>\n\n🆔 Hisobingiz ID sini kiriting (9-12 raqam):",
            parse_mode="HTML")

    # WITHDRAW ID confirm
    elif cb == "wit_id_yes":
        state = get_state(uid)
        d = state["data"]
        set_state(uid, "wit_card", d)
        bot.answer_callback_query(call.id, "✅")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id,
            "💳 Karta raqamingizni kiriting (16 raqam):")

    elif cb == "wit_id_no":
        state = get_state(uid)
        d = state["data"]
        set_state(uid, "wit_id", d)
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, "🆔 ID ni qaytadan kiriting:")

    # WITHDRAW karta confirm
    elif cb == "wit_card_yes":
        state = get_state(uid)
        d = state["data"]
        set_state(uid, "wit_code", d)
        bot.answer_callback_query(call.id, "✅")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id,
            "🔑 <b>Maxsus kodni kiriting</b>\n\n"
            "(1XBet Cash out da berilgan kod):",
            parse_mode="HTML")

    elif cb == "wit_card_no":
        state = get_state(uid)
        d = state["data"]
        set_state(uid, "wit_card", d)
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, "💳 Karta raqamini qaytadan kiriting (16 raqam):")

    # WITHDRAW kod confirm
    elif cb == "wit_code_yes":
        state = get_state(uid)
        d = state["data"]
        wid = f"WIT{uid}{int(datetime.now().timestamp())}"
        withdrawals[wid] = {
            "user_id": uid,
            "platform": d.get("platform", ""),
            "bet_id": d.get("bet_id", ""),
            "card": d.get("card", ""),
            "code": d.get("code", ""),
            "status": "pending",
            "time": datetime.now()
        }
        clear_state(uid)
        bot.answer_callback_query(call.id, "✅")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id,
            withdraw_pending_check(uid, 0, wid, d['platform'], d['bet_id']),
            parse_mode="HTML", reply_markup=main_kb())
        u = get_user(uid)
        uname = f"@{u['username']}" if u['username'] else u['full_name']
        card = d.get("card", "")
        cf = f"{card[0:4]} {card[4:8]} {card[8:12]} {card[12:16]}" if card else ""
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"wit_approve_{wid}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"wit_reject_{wid}")
        )
        bot.send_message(ADMIN_ID,
            f"💸 <b>Yangi yechish so'rovi!</b>\n\n"
            f"👤 {uname} (ID: {uid})\n"
            f"🎰 {d['platform']}\n"
            f"🆔 Bet ID: <code>{d['bet_id']}</code>\n"
            f"💳 Karta: <code>{cf}</code>\n"
            f"🔑 Kod: <code>{d['code']}</code>\n"
            f"📅 {now_str()}",
            parse_mode="HTML", reply_markup=kb)

    elif cb == "wit_code_no":
        state = get_state(uid)
        d = state["data"]
        set_state(uid, "wit_code", d)
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, "🔑 Kodni qaytadan kiriting:")

    # WITHDRAW tasdiqlash (admin)
    elif cb.startswith("wit_approve_"):
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Ruxsat yo'q!")
            return
        wid = cb.replace("wit_approve_", "")
        w = withdrawals.get(wid)
        if not w or w["status"] != "pending":
            bot.answer_callback_query(call.id, "❌ Allaqachon ko'rib chiqilgan!")
            return
        w["status"] = "approved"
        bot.answer_callback_query(call.id, "✅ Tasdiqlandi!")
        try:
            bot.edit_message_text(
                call.message.text + "\n\n✅ <b>TASDIQLANDI</b>",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        except:
            pass
        bot.send_message(w["user_id"],
            withdraw_approved_check(w["user_id"], 0, wid, w["platform"], w["bet_id"], w["card"]),
            parse_mode="HTML")

    # WITHDRAW rad (admin)
    elif cb.startswith("wit_reject_"):
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Ruxsat yo'q!")
            return
        wid = cb.replace("wit_reject_", "")
        w = withdrawals.get(wid)
        if not w:
            bot.answer_callback_query(call.id, "❌ Topilmadi!")
            return
        w["status"] = "rejected"
        bot.answer_callback_query(call.id, "❌ Rad etildi!")
        try:
            bot.edit_message_text(
                call.message.text + "\n\n❌ <b>RAD ETILDI</b>",
                call.message.chat.id, call.message.message_id, parse_mode="HTML")
        except:
            pass
        bot.send_message(w["user_id"],
            "❌ <b>Yechish so'rovingiz rad etildi!</b>\n\nMuammo bo'lsa admin bilan bog'laning.",
            parse_mode="HTML")

# ===================== AUTO BEKOR =====================
def auto_cancel(pid, user_id, delay):
    time.sleep(delay)
    if pid in payments and payments[pid]["status"] == "pending":
        payments[pid]["status"] = "expired"
        try:
            bot.send_message(user_id,
                "⏰ <b>To'lov vaqti tugadi!</b>\n\nYangi to'lov yarating.",
                parse_mode="HTML")
        except:
            pass

# ===================== MAIN =====================
print("🚀 Xon Kassa bot ishga tushdi!")
while True:
    try:
        bot.polling(none_stop=True, interval=1, timeout=1800)
    except Exception as e:
        print(f"Xato: {e}")
        time.sleep(5)
