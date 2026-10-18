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

# ========== الإعدادات الأساسية لبوتك ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_FILE = "users.json"
DEVELOPER = "@RAHLI_1"
BOT_NAME = "صانع البوتات"

# قنواتك التي ستفرض على الزبائن
CHANNELS = [
    {"id": "@eco_store_2", "name": "قناتي الرسمية", "url": "https://t.me/eco_store_2"},
    {"id": "@RAHLI_120", "name": "مجموعتي الرسمية", "url": "https://t.me/RAHLI_120"},
]

# ========== شرح التشغيل للمبتدئين ==========
INSTRUCTIONS_TEXT = """
📚 *دليل المبتدئين: كيف تجعل بوتك يعمل؟*

أهلاً بك! لقد حصلت على كود بوتك (تطوير المالك: @RAHLI_1). اتبع هذه الخطوات بالضبط:

*الخطوة 1: تحميل تطبيق Pydroid 3*
1. اذهب إلى متجر Google Play.
2. ابحث عن تطبيق *Pydroid 3* وقم بتثبيته.

*الخطوة 2: الحصول على التوكن*
1. اذهب إلى بوت @BotFather في تلغرام.
2. أرسل له الأمر /newbot.
3. اختر اسماً ومعرفاً لبوتك.
4. سيعطيك BotFather رسالة فيها *Token* (كود طويل). انسخه.

*الخطوة 3: تشغيل البوت*
1. افتح تطبيق Pydroid 3.
2. افتح الملف الذي أرسلته لك (بوت_أزرار.py).
3. ابحث عن السطر: `TOKEN = "ضع_توكن_بوتك_هنا"`.
4. ضع التوكن الذي نسخته مكان الكلمة العربية (بين علامات التنصيص).
5. اضغط على زر التشغيل (الزر الأصفر ▶️).
6. مبروك! اذهب إلى بوتك في تلغرام واضغط /start.

⚠️ *ملاحظة هامة:* هذا البوت مبرمج ليطلب من المستخدمين الاشتراك في قنوات المالك @RAHLI_1 أولاً.
"""

# ========== قاعدة بيانات ==========
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# ========== التحقق من الاشتراك (للبوت الرئيسي) ==========
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

# ========== القوالب (البوتات التي تُرسل للزبائن) ==========
TEMPLATES = {}

# هنا السر: هذا الكود هو ما سيحصل عليه الزبون. لقد وضعنا فيه اسمك وقنواتك.
TEMPLATES["buttons"] = {
    "name": "🔘 بوت أزرار",
    "desc": "بوت بقوائم أزرار تفاعلية.",
    "code": '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
# الزبون سيضع توكنه هنا
TOKEN = "ضع_توكن_بوتك_هنا"

# معلومات المالك الأساسي (أنت)
ORIGINAL_OWNER = "@RAHLI_1"
FORCED_CHANNELS = ["@eco_store_2", "@RAHLI_120"]

# دالة إجبار المستخدمين على الاشتراك في قنواتك
async def check_forced_sub(update, ctx):
    user_id = update.effective_user.id
    not_sub = []
    for ch in FORCED_CHANNELS:
        try:
            m = await ctx.bot.get_chat_member(ch, user_id)
            if m.status in ["left", "kicked"]:
                not_sub.append(ch)
        except Exception:
            not_sub.append(ch)
            
    if not_sub:
        kb = [[InlineKeyboardButton(f"📢 اشترك هنا", url=f"https://t.me/{ch.replace('@','')}")] for ch in not_sub]
        kb.append([InlineKeyboardButton("✅ تحققت", callback_data="check_sub")])
        text = f"⚠️ *يجب عليك الاشتراك في قنوات المالك {ORIGINAL_OWNER} أولاً:*"
        if update.callback_query:
            await update.callback_query.answer("اشترك أولاً!", show_alert=True)
        else:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return False
    return True

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await check_forced_sub(update, ctx): return
    kb = [
        [InlineKeyboardButton("زر 1", callback_data="b1")],
        [InlineKeyboardButton("زر 2", callback_data="b2")],
        [InlineKeyboardButton(f"👑 المالك الأساسي: {ORIGINAL_OWNER}", callback_data="none")]
    ]
    await update.message.reply_text("أهلاً بك في بوت الأزرار:", reply_markup=InlineKeyboardMarkup(kb))

async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "check_sub":
        if await check_forced_sub(update, ctx):
            await start(update, ctx)
        return
    if q.data == "none": return
    await q.edit_message_text(f"ضغطت على: {q.data}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
if __name__ == "__main__": main()
'''
}

# باقي القوالب (يمكنك إضافة نفس الحماية لها لاحقاً بنفس الطريقة)
TEMPLATES["translate"] = {
    "name": "🌐 بوت ترجمة",
    "desc": "يترجم النصوص.",
    "code": '''#!/usr/bin/env python3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل أي نص وسأترجمه. (تطوير @RAHLI_1)")
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

TEMPLATES["calc"] = {
    "name": "🧮 بوت حاسبة",
    "desc": "حاسبة بسيطة.",
    "code": '''#!/usr/bin/env python3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN = "ضع_توكن_بوتك_هنا"
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل عملية مثل: 5+3*2 (تطوير @RAHLI_1)")
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

# ========== القوائم ==========
def main_menu():
    kb = [
        [InlineKeyboardButton("🤖 أنواع البوتات", callback_data="types")],
        [InlineKeyboardButton("🔗 شارك البوت", callback_data="share")],
        [InlineKeyboardButton(f"{DEVELOPER} 👑 المالك", callback_data="owner")],
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
            f"*{tpl['name']}*\n\n{tpl['desc']}\n\n📥 جاري إرسال الملف...",
            parse_mode="Markdown"
        )
        
        f = InputFile(io.BytesIO(tpl["code"].encode("utf-8")), filename=f"{key}_bot.py")
        await ctx.bot.send_document(
            chat_id=q.from_user.id,
            document=f,
            caption=f"✅ هذا هو كود بوت {tpl['name']} الخاص بك. (تطوير: {DEVELOPER})"
        )
        
        await ctx.bot.send_message(
            chat_id=q.from_user.id,
            text=INSTRUCTIONS_TEXT,
            parse_mode="Markdown"
        )
        
        await ctx.bot.send_message(
            chat_id=q.from_user.id,
            text="اختر نوعاً آخر أو اضغط رجوع:",
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

async def msg_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    not_sub = await check_subscription(update.effective_user.id, ctx.bot)
    if not_sub:
        await update.message.reply_text(
            "⚠️ اشترك أولاً:",
            reply_markup=subscribe_keyboard(not_sub)
        )
        return
    await update.message.reply_text("استخدم /start للبدء.")

def main():
    print("=" * 50)
    print(f"🤖 {BOT_NAME}")
    print(f"👑 المالك: {DEVELOPER}")
    print("=" * 50)
    
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
