#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import json
import logging
import os
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ========== الإعدادات ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_FILE = "users.json"
DEVELOPER = "@RAHLI_1"
BOT_NAME = "صانع البوتات"

CHANNELS = [
    {"id": "@eco_store_2", "name": "قناتي الرسمية", "url": "https://t.me/eco_store_2"},
    {"id": "@RAHLI_120", "name": "مجموعتي الرسمية", "url": "https://t.me/RAHLI_120"},
]

# ========== قاعدة بيانات ==========
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# ========== التحقق من الاشتراك ==========
async def check_subscription(user_id, bot):
    not_subscribed = []
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                not_subscribed.append(ch)
        except Exception as e:
            logger.warning(f"خطأ في التحقق من {ch['id']}: {e}")
            not_subscribed.append(ch)
    return not_subscribed

def subscribe_keyboard(not_subscribed):
    kb = []
    for ch in not_subscribed:
        kb.append([InlineKeyboardButton(f"📢 {ch['name']}", url=ch["url"])])
    kb.append([InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_sub")])
    return InlineKeyboardMarkup(kb)

# ========== القوالب ==========
TEMPLATES = {}

TEMPLATES["buttons"] = {
    "name": "🔘 بوت أزرار",
    "desc": "بوت بقوائم أزرار تفاعلية.",
    "code": '''#!/usr/bin/env python3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
logging.basicConfig(level=logging.INFO)
TOKEN = "ضع_توكن_بوتك_هنا"
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("زر 1", callback_data="b1")],[InlineKeyboardButton("زر 2", callback_data="b2")]]
    await update.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(kb))
async def btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); await q.edit_message_text(f"ضغطت: {q.data}")
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

TEMPLATES["translate"] = {
    "name": "🌐 بوت ترجمة",
    "desc": "يترجم النصوص.",
    "code": '''#!/usr/bin/env python3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل أي نص وسأترجمه.")
async def tr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    await update.message.reply_text(f"🌐 https://translate.google.com/?text={t}")
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tr))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

TEMPLATES["quiz"] = {
    "name": "🎯 بوت مسابقات",
    "desc": "أسئلة وأجوبة.",
    "code": '''#!/usr/bin/env python3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
Q = [{"q":"عاصمة المغرب؟","o":["الرباط","فاس"],"a":"الرباط"}]
scores = {}
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    scores[update.effective_user.id] = 0
    await ask(update, 0)
async def ask(update, i):
    if i >= len(Q):
        await update.effective_message.reply_text(f"النقاط: {scores[update.effective_user.id]}")
        return
    kb = [[InlineKeyboardButton(o, callback_data=f"{i}_{o}")] for o in Q[i]["o"]]
    await update.effective_message.reply_text(Q[i]["q"], reply_markup=InlineKeyboardMarkup(kb))
async def btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    i = int(q.data.split("_")[0]); a = q.data.split("_",1)[1]
    if a == Q[i]["a"]:
        scores[q.from_user.id] += 1; await q.edit_message_text("✅ صحيح")
    else: await q.edit_message_text(f"❌ الجواب: {Q[i]['a']}")
    await ask(update, i+1)
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

TEMPLATES["calc"] = {
    "name": "🧮 بوت حاسبة",
    "desc": "حاسبة بسيطة.",
    "code": '''#!/usr/bin/env python3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل عملية مثل: 5+3*2")
async def c(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    try:
        if not set(t) <= set("0123456789+-*/(). "): raise ValueError
        await update.message.reply_text(f"= {eval(t, {'__builtins__':{}}, {})}")
    except: await update.message.reply_text("خطأ")
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, c))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

TEMPLATES["age"] = {
    "name": "🎂 حساب العمر",
    "desc": "يحسب عمرك.",
    "code": '''#!/usr/bin/env python3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل تاريخ ميلادك YYYY-MM-DD")
async def a(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        b = datetime.strptime(update.message.text.strip(), "%Y-%m-%d"); t = datetime.now()
        y = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
        await update.message.reply_text(f"عمرك: {y} سنة")
    except: await update.message.reply_text("صيغة خاطئة")
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, a))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

TEMPLATES["welcome"] = {
    "name": "👋 بوت ترحيب",
    "desc": "يرحب بالأعضاء.",
    "code": '''#!/usr/bin/env python3
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
async def w(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    for m in update.message.new_chat_members:
        await update.message.reply_text(f"أهلاً {m.full_name} 🎉")
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, w))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

TEMPLATES["broadcast"] = {
    "name": "📢 بوت إعلانات",
    "desc": "إرسال جماعي للمشتركين.",
    "code": '''#!/usr/bin/env python3
import json, os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
ADMIN_ID = 0
DB = "subs.json"
def l(): return json.load(open(DB)) if os.path.exists(DB) else []
def s(d): json.dump(d, open(DB,"w"))
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    subs = l()
    if update.effective_user.id not in subs: subs.append(update.effective_user.id); s(subs)
    await update.message.reply_text("تم الاشتراك.")
async def b(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(ctx.args)
    for u in l():
        try: await ctx.bot.send_message(u, msg)
        except: pass
    await update.message.reply_text("تم.")
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", b))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

TEMPLATES["zakhrafa"] = {
    "name": "بوت زخرفة",
    "desc": "يزخرف الأسماء.",
    "code": '''#!/usr/bin/env python3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
D = {"a":"α","b":"в","c":"¢","d":"∂","e":"є","f":"ƒ","g":"g","h":"н","i":"ι","j":"נ","k":"к","l":"ℓ","m":"м","n":"η","o":"σ","p":"ρ","q":"q","r":"я","s":"ѕ","t":"т","u":"υ","v":"ν","w":"ω","x":"χ","y":"у","z":"z"}
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل اسمك.")
async def z(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.lower(); await update.message.reply_text("".join(D.get(c,c) for c in t))
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, z))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

TEMPLATES["pdf"] = {
    "name": "📄 صور → PDF",
    "desc": "يحوّل الصور إلى PDF.",
    "code": '''#!/usr/bin/env python3
import io
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
TOKEN = "ضع_توكن_بوتك_هنا"
imgs = {}
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل الصور ثم /done")
async def c(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user.id; imgs.setdefault(u, [])
    p = update.message.photo[-1]; f = await p.get_file(); b = await f.download_as_bytearray()
    imgs[u].append(Image.open(io.BytesIO(b)).convert("RGB"))
    await update.message.reply_text(f"عدد الصور: {len(imgs[u])}")
async def d(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user.id
    if not imgs.get(u): await update.message.reply_text("لا صور."); return
    buf = io.BytesIO(); imgs[u][0].save(buf, "PDF", save_all=True, append_images=imgs[u][1:]); buf.seek(0)
    await update.message.reply_document(buf, filename="out.pdf"); imgs[u] = []
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", d))
    app.add_handler(MessageHandler(filters.PHOTO, c))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

TEMPLATES["music"] = {
    "name": "🎵 بوت موسيقى",
    "desc": "يبحث عن أغاني يوتيوب.",
    "code": '''#!/usr/bin/env python3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل اسم الأغنية.")
async def s(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.message.text.replace(" ","+")
    await update.message.reply_text(f"🎵 https://www.youtube.com/results?search_query={q}")
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, s))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

# ========== القوائم ==========
def main_menu():
    kb = [
        [InlineKeyboardButton("🤖 أنواع البوتات", callback_data="types")],
        [InlineKeyboardButton("🔗 شارك البوت", callback_data="share")],
        [InlineKeyboardButton("@RAHLI_1 👑 المالك", callback_data="owner")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")],
    ]
    return InlineKeyboardMarkup(kb)

def types_menu():
    keys = list(TEMPLATES.keys())
    kb = []
    for i in range(0, len(keys), 2):
        row = []
        for k in keys[i:i+2]:
            row.append(InlineKeyboardButton(TEMPLATES[k]["name"], callback_data=f"tpl_{k}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("⬅ رجوع", callback_data="back")])
    return InlineKeyboardMarkup(kb)

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅ رجوع", callback_data="back")]])

# ========== الأوامر ==========
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    not_sub = await check_subscription(user.id, ctx.bot)
    if not_sub:
        await update.message.reply_text(
            f"👋 أهلاً {user.full_name}\n\n"
            "⚠️ *قبل استخدام البوت، يجب أن تشترك في:*",
            parse_mode="Markdown",
            reply_markup=subscribe_keyboard(not_sub)
        )
        return

    db = load_db()
    uid = str(user.id)
    referrer = ctx.args[0] if ctx.args else None
    if uid not in db:
        db[uid] = {"name": user.full_name, "joined": datetime.now().isoformat(), "referrals": 0}
        if referrer and referrer in db and referrer != uid:
            db[referrer]["referrals"] = db[referrer].get("referrals", 0) + 1
        save_db(db)

    await update.message.reply_text(
        f"👋 أهلاً {user.full_name}\n\n"
        f"مرحباً بك في *{BOT_NAME}*.\n\n"
        "اختر من الأزرار أدناه:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ========== معالج الأزرار ==========
async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "check_sub":
        not_sub = await check_subscription(q.from_user.id, ctx.bot)
        if not_sub:
            await q.answer("❌ لم تشترك بعد.", show_alert=True)
        else:
            await q.answer("✅ تم التحقق!", show_alert=True)
            await q.edit_message_text(
                f"✅ شكراً لاشتراكك!\n\nمرحباً في *{BOT_NAME}*:",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        return

    not_sub = await check_subscription(q.from_user.id, ctx.bot)
    if not_sub:
        await q.edit_message_text(
            "⚠️ يجب أن تشترك أولاً:",
            reply_markup=subscribe_keyboard(not_sub)
        )
        return

    if data == "types":
        await q.edit_message_text("🤖 اختر نوع البوت:", reply_markup=types_menu())

    elif data.startswith("tpl_"):
        key = data[4:]
        tpl = TEMPLATES.get(key)
        if not tpl:
            return
        await q.edit_message_text(
            f"*{tpl['name']}*\n\n{tpl['desc']}\n\n📥 جاري الإرسال...",
            parse_mode="Markdown"
        )
        f = InputFile(io.BytesIO(tpl["code"].encode("utf-8")), filename=f"{key}_bot.py")
        await ctx.bot.send_document(
            chat_id=q.from_user.id,
            document=f,
            caption=f"✅ {tpl['name']}\n\n"
                    "📌 *خطوات التشغيل:*\n"
                    "1. افتح @BotFather وأنشئ بوتاً جديداً\n"
                    "2. انسخ التوكن\n"
                    "3. افتح الملف وضع التوكن مكان `ضع_توكن_بوتك_هنا`\n"
                    "4. شغّله بـ: `python3 {key}_bot.py`",
            parse_mode="Markdown"
        )
        await ctx.bot.send_message(
            chat_id=q.from_user.id,
            text="اختر نوعاً آخر:",
            reply_markup=types_menu()
        )

    elif data == "share":
        me = await ctx.bot.get_me()
        link = f"https://t.me/{me.username}?start={q.from_user.id}"
        await q.edit_message_text(
            f"🔗 *رابطك الخاص:*\n\n`{link}`\n\n"
            "شاركه وكل من يدخل منه يُحسب في إحصائياتك.",
            parse_mode="Markdown",
            reply_markup=back_menu()
        )

    elif data == "owner":
        await q.edit_message_text(
            f"👑 *مالك البوت:*\n\n"
            f"{DEVELOPER}\n\n"
            "هذا البوت من تطوير وإدارة المالك الرسمي.",
            parse_mode="Markdown",
            reply_markup=back_menu()
        )

    elif data == "stats":
        db = load_db()
        uid = str(q.from_user.id)
        d = db.get(uid, {})
        await q.edit_message_text(
            f"📊 إحصائياتك:\n\n"
            f"👤 {q.from_user.full_name}\n"
            f"👥 الإحالات: {d.get('referrals', 0)}\n"
            f"📅 الانضمام: {d.get('joined', '')[:10]}",
            reply_markup=back_menu()
        )

    elif data == "back":
        await q.edit_message_text("القائمة الرئيسية:", reply_markup=main_menu())

# ========== معالج الرسائل ==========
async def msg_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    not_sub = await check_subscription(update.effective_user.id, ctx.bot)
    if not_sub:
        await update.message.reply_text(
            "⚠️ اشترك أولاً:",
            reply_markup=subscribe_keyboard(not_sub)
        )
        return
    await update.message.reply_text("استخدم /start للبدء.")

# ========== التشغيل ==========
def main():
    print("=" * 50)
    print(f"🤖 {BOT_NAME}")
    print(f"👑 المالك: {DEVELOPER}")
    print("=" * 50)
    import os
token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        print("❌ لا يوجد توكن.")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))

    print("✅ البوت يعمل... Ctrl+C للإيقاف.")
    app.run_polling()

if __name__ == "__main__":
    main()
