import os
import re
import asyncio
import sqlite3
import tempfile
import logging
from pathlib import Path

from telegram import Update, BotCommand
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# ============================================================
# 1. الإعدادات الأساسية
# ============================================================

# ⚠️ ضع التوكن الخاص بك هنا (أو اتركه يقرأ من البيئة)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8824872624:AAH5F6c9A0XIrCGzyLMT6wbfwOTDkM7arGc")

# أسماء المالكين (يجب أن تكون مطابقة لأسمائهم في تيليجرام بالضبط)
OWNER_1 = "@RAHLI_1"
OWNER_2 = "@TV_19_VPI"

# إعدادات النقاط
DOWNLOAD_COST = 2      # تكلفة تحميل الفيديو
REFERRAL_REWARD = 1    # مكافأة دعوة شخص جديد

# 🎁 الأكواد الخاصة (صعبة التخمين وتُستخدم مرة واحدة فقط)
PROMO_CODES = {
    "N4X8-V2K9-P3": 5,
    "R7Q1-M5T3-Z9": 10,
    "H2C6-B8W4-L1": 20,
    "K9J3-D7F5-Y2": 50,
}

# ------------------------------------------------------------
# رسالة التنبيه وإخلاء المسؤولية
# ------------------------------------------------------------
WARNING_MESSAGE = """⚠️ <b>تنبيه وإخلاء مسؤولية:</b>

أهلاً بك! صُمم هذا البوت لتسهيل حفظ وتحميل المحتوى المباح والنافع.

نرجو تذكر قول الله تعالى:
﴿ مَا يَلْفِظُ مِنْ قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ ﴾

نبرأ إلى الله من استخدام هذا البوت في تحميل ما حرّم الله (كالمقاطع المحرمة والمنكرات)، أو انتهاك حقوق الملكية الفكرية للآخرين بغير حق.

<b>المستخدم وحده يتحمل المسؤولية كاملة أمام الله عن طبيعة استخدامه.</b>

---
👤 <b>المالكين:</b> {owner1} و {owner2}
"""

# المنصات المدعومة فقط
SUPPORTED_DOMAINS = {
    "youtube.com": "يوتيوب",
    "youtu.be": "يوتيوب",
    "tiktok.com": "تيك توك",
    "vm.tiktok.com": "تيك توك",
    "facebook.com": "فيسبوك",
    "fb.watch": "فيسبوك",
    "instagram.com": "إنستغرام",
}

MAX_FILE_SIZE_MB = 50
TEMP_DIR = Path(tempfile.gettempdir()) / "tg_downloader_bot"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# 2. إعداد قاعدة البيانات (النقاط والإحالات)
# ============================================================
DB_PATH = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS used_codes (
            code TEXT PRIMARY KEY,
            user_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT points, referred_by FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(user_id, referred_by=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
    conn.commit()
    conn.close()

def update_points(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# 🔥 دالة جديدة لجلب الإحصائيات
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(points) FROM users")
    total_points = cursor.fetchone()[0] or 0
    conn.close()
    return total_users, total_points

# ============================================================
# 3. دوال مساعدة للتحميل والتحقق
# ============================================================
def extract_domain(url: str):
    url = url.strip()
    match = re.match(r"^(?:https?://)?(?:www\.)?([^/]+)", url, re.IGNORECASE)
    return match.group(1).lower().split(":")[0] if match else None

def is_supported_url(url: str):
    domain = extract_domain(url)
    if not domain: return False, None
    if domain in SUPPORTED_DOMAINS: return True, SUPPORTED_DOMAINS[domain]
    for supported, name in SUPPORTED_DOMAINS.items():
        if domain.endswith("." + supported): return True, name
    return False, None

def download_video(url: str, output_dir: Path):
    ydl_opts = {
        "outtmpl": str(output_dir / "%(title).100s_%(id)s.%(ext)s"),
        "format": "best[ext=mp4]/best", 
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "max_filesize": MAX_FILE_SIZE_MB * 1024 * 1024,
        "extractor_args": {"youtube": {"player_client": ["tv", "mweb", "android"]}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = Path(ydl.prepare_filename(info))
        if not file_path.exists():
            files = sorted(output_dir.glob("*"), key=os.path.getmtime, reverse=True)
            if files: file_path = files[0]
            else: raise FileNotFoundError("لم يتم العثور على الملف.")
        return file_path, info

async def cleanup_file(path: Path):
    try:
        if path.exists(): await asyncio.to_thread(path.unlink)
    except Exception: pass

# ============================================================
# 4. معالجات البوت (الأوامر)
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = context.bot.username
    
    referred_by = None
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id:
                referred_by = referrer_id
        except ValueError:
            pass

    user = get_user(user_id)
    if not user:
        add_user(user_id, referred_by)
        if referred_by:
            update_points(referred_by, REFERRAL_REWARD)
            try:
                await context.bot.send_message(
                    chat_id=referred_by, 
                    text=f"🎉 مبروك! انضم شخص جديد عبر رابطك، وحصلت على {REFERRAL_REWARD} نقطة."
                )
            except Exception: pass
        user = get_user(user_id)

    points = user[0]
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    welcome_text = (
        f"🤖 <b>أهلاً بك في بوت التحميل!</b>\n\n"
        f"💰 <b>رصيدك الحالي:</b> {points} نقطة\n"
        f"(تكلفة تحميل الفيديو الواحد: {DOWNLOAD_COST} نقاط)\n\n"
        f"🔗 <b>رابط الإحالة الخاص بك:</b>\n"
        f"<code>{ref_link}</code>\n"
        f"(شارك الرابط، واحصل على {REFERRAL_REWARD} نقطة لكل شخص جديد!)\n\n"
        f"📥 <b>كيفية الاستخدام:</b>\n"
        f"فقط قم بإرسال رابط الفيديو هنا وسأقوم بتحميله.\n\n"
        f"🔹 <b>المنصات المدعومة:</b>\n"
        f"يوتيوب، تيك توك، فيسبوك، إنستغرام.\n\n"
        f"👇 <i>يرجى قراءة التنبيه التالي:</i>\n\n"
    )
    
    warning_text = WARNING_MESSAGE.format(owner1=OWNER_1, owner2=OWNER_2)
    await update.message.reply_text(welcome_text + warning_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🔒 التحقق من أن المستخدم هو أحد المالكين
    username = update.effective_user.username
    current_user = f"@{username}" if username else ""
    
    if current_user not in [OWNER_1, OWNER_2]:
        await update.message.reply_text("❌ عذراً، هذا الأمر مخصص للمالكين فقط.")
        return

    total_users, total_points = get_stats()
    
    stats_text = (
        "📊 <b>إحصائيات البوت:</b>\n\n"
        f"👥 <b>إجمالي عدد المستخدمين:</b> {total_users} مستخدم\n"
        f"💰 <b>إجمالي النقاط في النظام:</b> {total_points} نقطة"
    )
    await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)

async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = context.bot.username
    user = get_user(user_id)
    
    if not user:
        add_user(user_id)
        user = get_user(user_id)
        
    points = user[0]
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    text = (
        f"💰 <b>رصيدك الحالي:</b> {points} نقطة\n\n"
        f"🔗 <b>رابط الإحالة الخاص بك:</b>\n"
        f"<code>{ref_link}</code>\n"
        f"شارك هذا الرابط واحصل على {REFERRAL_REWARD} نقطة لكل شخص يدخل منه.\n\n"
        f"🎁 <b>لشحن النقاط:</b> استخدم الأمر <code>/redeem الكود</code>\n"
        f"🛒 <b>للشراء:</b> أرسل الأمر /buy"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ يرجى كتابة الكود بعد الأمر. مثال:\n<code>/redeem الكود_هنا</code>", parse_mode=ParseMode.HTML)
        return
        
    code = context.args[0].strip().upper()
    
    if code not in PROMO_CODES:
        await update.message.reply_text("❌ هذا الكود غير صحيح أو غير موجود.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM used_codes WHERE code = ?", (code,))
    if cursor.fetchone():
        conn.close()
        await update.message.reply_text("❌ عذراً، هذا الكود تم استخدامه مسبقاً وهو غير صالح الآن.")
        return
        
    points_to_add = PROMO_CODES[code]
    
    cursor.execute("INSERT INTO used_codes (code, user_id) VALUES (?, ?)", (code, user_id))
    conn.commit()
    conn.close()
    
    update_points(user_id, points_to_add)
    await update.message.reply_text(f"✅ تم شحن حسابك بنجاح!\n💰 حصلت على <b>{points_to_add}</b> نقطة.", parse_mode=ParseMode.HTML)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛒 <b>لشراء النقاط:</b>\n\n"
        "إذا كنت تريد شراء نقاط لتحميل المزيد من الفيديوهات، يرجى التواصل مع أحد المالكين:\n"
        f"👤 {OWNER_1}\n"
        f"👤 {OWNER_2}\n\n"
        "سيقومون بإعطائك كود شحن، قم بإرساله للبوت بهذه الطريقة:\n"
        "<code>/redeem الكود_الذي_أعطوك_إياه</code>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id
    url = message.text.strip()

    if not re.search(r"https?://", url, re.IGNORECASE):
        await message.reply_text("❌ الرجاء إرسال رابط فيديو صالح.")
        return

    supported, platform_name = is_supported_url(url)
    if not supported:
        await message.reply_text("❌ عذراً، المنصة غير مدعومة.\nالمنصات المدعومة فقط: يوتيوب، تيك توك، فيسبوك، إنستغرام.")
        return

    user = get_user(user_id)
    if not user:
        add_user(user_id)
        user = get_user(user_id)
        
    points = user[0]
    if points < DOWNLOAD_COST:
        await message.reply_text(
            f"❌ <b>رصيدك غير كافٍ!</b>\n"
            f"تحتاج إلى {DOWNLOAD_COST} نقاط لتحميل الفيديو.\n"
            f"رصيدك الحالي: {points} نقطة.\n\n"
            f"🔗 اجمع النقاط عبر مشاركة رابط الإحالة الخاص بك (أرسل /points).\n"
            f"🛒 أو قم بشرائها من المالكين (أرسل /buy).",
            parse_mode=ParseMode.HTML
        )
        return

    update_points(user_id, -DOWNLOAD_COST)
    
    processing_msg = await message.reply_text(f"⏳ جاري معالجة رابط {platform_name}...\n(تم خصم {DOWNLOAD_COST} نقاط)\nيرجى الانتظار.")
    await message.chat.send_action(ChatAction.UPLOAD_VIDEO)

    task_dir = TEMP_DIR / f"task_{message.message_id}_{user_id}"
    task_dir.mkdir(exist_ok=True, parents=True)

    file_path = None
    try:
        file_path, info = await asyncio.to_thread(download_video, url, task_dir)

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"حجم الفيديو ({file_size_mb:.1f} ميجا) يتجاوز الحد المسموح (50 ميجا).")

        warning_caption = WARNING_MESSAGE.format(owner1=OWNER_1, owner2=OWNER_2)
        if len(warning_caption) > 1000:
            warning_caption = warning_caption[:1000] + "..."

        with open(file_path, "rb") as video_file:
            await message.reply_video(
                video=video_file, caption=warning_caption, parse_mode=ParseMode.HTML,
                supports_streaming=True, filename=file_path.name,
                read_timeout=300, write_timeout=300, connect_timeout=300
            )
        await processing_msg.delete()

    except Exception as e:
        logger.exception(f"خطأ: {e}")
        update_points(user_id, DOWNLOAD_COST)
        await processing_msg.edit_text("❌ حدث خطأ أثناء التحميل (قد يكون الرابط معطلاً أو بطء في الشبكة).\n✅ تم إرجاع النقاط المخصومة إلى رصيدك.")
        
    finally:
        if file_path: await cleanup_file(file_path)
        try:
            if task_dir.exists() and not any(task_dir.iterdir()): await asyncio.to_thread(task_dir.rmdir)
        except Exception: pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="حدث استثناء:", exc_info=context.error)

# ============================================================
# 5. تشغيل البوت
# ============================================================

def main():
    if not BOT_TOKEN or BOT_TOKEN == "ضع_التوكن_الخاص_بك_هنا":
        raise ValueError("الرجاء تعيين BOT_TOKEN أولاً.")

    init_db() 

    # 🔥 إضافة قائمة الأوامر تلقائياً (أمر stats مخفي عن العامة لكي لا يراه أحد)
    async def post_init(application: Application) -> None:
        await application.bot.set_my_commands([
            BotCommand("start", "بدء استخدام البوت وعرض الرصيد"),
            BotCommand("points", "عرض رصيدك الحالي ورابط الإحالة"),
            BotCommand("redeem", "شحن النقاط باستخدام كود"),
            BotCommand("buy", "شراء النقاط من المالكين"),
        ])

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(300)
        .write_timeout(300)
        .connect_timeout(300)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command)) # 🔥 إضافة أمر الإحصائيات
    application.add_handler(CommandHandler("points", points_command))
    application.add_handler(CommandHandler("redeem", redeem_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_error_handler(error_handler)

    logger.info("✅ البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
