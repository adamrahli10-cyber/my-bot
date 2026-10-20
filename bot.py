import os
import re
import asyncio
import tempfile
import logging
from pathlib import Path

from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp
from pymongo import MongoClient

# ============================================================
# 1. الإعدادات الأساسية
# ============================================================

# ⚠️ سيتم قراءة التوكن ورابط قاعدة البيانات من إعدادات GitHub (Secrets)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGODB_URI = os.environ.get("MONGODB_URI")

# ⚠️ اسم قناة الاشتراك الإجباري
CHANNEL_USERNAME = "@botTelegram_0"

# أسماء المالكين
OWNER_1 = "@RAHLI_1"
OWNER_2 = "@TV_19_VPI"

# إعدادات النقاط
DOWNLOAD_COST = 2      # تكلفة تحميل الفيديو
REFERRAL_REWARD = 1    # مكافأة دعوة شخص جديد

# 🎁 الأكواد الخاصة (220 كوداً - تُستخدم مرة واحدة فقط في العالم)
PROMO_CODES = {
    # 100 كود بـ 2 نقاط
    "P2-8J4M": 2, "P2-3K9L": 2, "P2-7Q2W": 2, "P2-5N8B": 2, "P2-1C6V": 2,
    "P2-9X2Z": 2, "P2-4T7Y": 2, "P2-6H3P": 2, "P2-2R9K": 2, "P2-8D4F": 2,
    "P2-3M5N": 2, "P2-7V2C": 2, "P2-5B8X": 2, "P2-1Z6L": 2, "P2-9K2J": 2,
    "P2-4W7Q": 2, "P2-6Y3R": 2, "P2-2P9T": 2, "P2-8H4G": 2, "P2-3F5D": 2,
    "P2-7N2M": 2, "P2-5C8V": 2, "P2-1X6B": 2, "P2-9L2Z": 2, "P2-4J7K": 2,
    "P2-6Q3W": 2, "P2-2R9Y": 2, "P2-8T4H": 2, "P2-3G5F": 2, "P2-7D2S": 2,
    "P2-5A8P": 2, "P2-1M6N": 2, "P2-9V2C": 2, "P2-4B7X": 2, "P2-6Z3L": 2,
    "P2-2K9J": 2, "P2-8W4Q": 2, "P2-3Y5R": 2, "P2-7P2T": 2, "P2-5H8G": 2,
    "P2-1F6D": 2, "P2-9N2M": 2, "P2-4C7V": 2, "P2-6X3B": 2, "P2-2L9Z": 2,
    "P2-8J4K": 2, "P2-3Q5W": 2, "P2-7R2Y": 2, "P2-5T8H": 2, "P2-1G6F": 2,
    "P2-9D2S": 2, "P2-4A7P": 2, "P2-6M3N": 2, "P2-2V9C": 2, "P2-8B4X": 2,
    "P2-3Z5L": 2, "P2-7K2J": 2, "P2-5W8Q": 2, "P2-1Y6R": 2, "P2-9P2T": 2,
    "P2-4H7G": 2, "P2-6F3D": 2, "P2-2N9M": 2, "P2-8C4V": 2, "P2-3X5B": 2,
    "P2-7L2Z": 2, "P2-5J8K": 2, "P2-1Q6W": 2, "P2-9R2Y": 2, "P2-4T7H": 2,
    "P2-6G3F": 2, "P2-2D9S": 2, "P2-8A4P": 2, "P2-3M5N": 2, "P2-7V2C": 2,
    "P2-5B8X": 2, "P2-1Z6L": 2, "P2-9K2J": 2, "P2-4W7Q": 2, "P2-6Y3R": 2,
    "P2-2P9T": 2, "P2-8H4G": 2, "P2-3F5D": 2, "P2-7N2M": 2, "P2-5C8V": 2,
    "P2-1X6B": 2, "P2-9L2Z": 2, "P2-4J7K": 2, "P2-6Q3W": 2, "P2-2R9Y": 2,
    "P2-8T4H": 2, "P2-3G5F": 2, "P2-7D2S": 2, "P2-5A8P": 2, "P2-1M6N": 2,
    "P2-9V2C": 2, "P2-4B7X": 2, "P2-6Z3L": 2, "P2-2K9J": 2, "P2-8W4Q": 2,

    # 50 كود بـ 10 نقاط
    "P10-A1B2": 10, "P10-C3D4": 10, "P10-E5F6": 10, "P10-G7H8": 10, "P10-I9J1": 10,
    "P10-K2L3": 10, "P10-M4N5": 10, "P10-O6P7": 10, "P10-Q8R9": 10, "P10-S1T2": 10,
    "P10-U3V4": 10, "P10-W5X6": 10, "P10-Y7Z8": 10, "P10-A9B1": 10, "P10-C2D3": 10,
    "P10-E4F5": 10, "P10-G6H7": 10, "P10-I8J9": 10, "P10-K1L2": 10, "P10-M3N4": 10,
    "P10-O5P6": 10, "P10-Q7R8": 10, "P10-S9T1": 10, "P10-U2V3": 10, "P10-W4X5": 10,
    "P10-Y6Z7": 10, "P10-A8B9": 10, "P10-C1D2": 10, "P10-E3F4": 10, "P10-G5H6": 10,
    "P10-I7J8": 10, "P10-K9L1": 10, "P10-M2N3": 10, "P10-O4P5": 10, "P10-Q6R7": 10,
    "P10-S8T9": 10, "P10-U1V2": 10, "P10-W3X4": 10, "P10-Y5Z6": 10, "P10-A7B8": 10,
    "P10-C9D1": 10, "P10-E2F3": 10, "P10-G4H5": 10, "P10-I6J7": 10, "P10-K8L9": 10,
    "P10-M1N2": 10, "P10-O3P4": 10, "P10-Q5R6": 10, "P10-S7T8": 10, "P10-U9V1": 10,

    # 30 كود بـ 5 نقاط
    "P5-Z9Y8": 5, "P5-X7W6": 5, "P5-V5U4": 5, "P5-T3S2": 5, "P5-R1Q9": 5,
    "P5-P8O7": 5, "P5-N6M5": 5, "P5-L4K3": 5, "P5-J2I1": 5, "P5-H9G8": 5,
    "P5-F7E6": 5, "P5-D5C4": 5, "P5-B3A2": 5, "P5-Z1Y9": 5, "P5-X8W7": 5,
    "P5-V6U5": 5, "P5-T4S3": 5, "P5-R2Q1": 5, "P5-P9O8": 5, "P5-N7M6": 5,
    "P5-L5K4": 5, "P5-J3I2": 5, "P5-H1G9": 5, "P5-F8E7": 5, "P5-D6C5": 5,
    "P5-B4A3": 5, "P5-Z2Y1": 5, "P5-X9W8": 5, "P5-V7U6": 5, "P5-T5S4": 5,

    # 20 كود بـ 20 نقطة
    "P20-M1N2O3": 20, "P20-P4Q5R6": 20, "P20-S7T8U9": 20, "P20-V1W2X3": 20, "P20-Y4Z5A6": 20,
    "P20-B7C8D9": 20, "P20-E1F2G3": 20, "P20-H4I5J6": 20, "P20-K7L8M9": 20, "P20-N1O2P3": 20,
    "P20-Q4R5S6": 20, "P20-T7U8V9": 20, "P20-W1X2Y3": 20, "P20-Z4A5B6": 20, "P20-C7D8E9": 20,
    "P20-F1G2H3": 20, "P20-I4J5K6": 20, "P20-L7M8N9": 20, "P20-O1P2Q3": 20, "P20-R4S5T6": 20,

    # 10 أكواد بـ 30 نقطة
    "P30-U7V8W9": 30, "P30-X1Y2Z3": 30, "P30-A4B5C6": 30, "P30-D7E8F9": 30, "P30-G1H2I3": 30,
    "P30-J4K5L6": 30, "P30-M7N8O9": 30, "P30-P1Q2R3": 30, "P30-S4T5U6": 30, "P30-V7W8X9": 30,

    # 10 أكواد بـ 50 نقطة
    "P50-Y1Z2A3": 50, "P50-B4C5D6": 50, "P50-E7F8G9": 50, "P50-H1I2J3": 50, "P50-K4L5M6": 50,
    "P50-N7O8P9": 50, "P50-Q1R2S3": 50, "P50-T4U5V6": 50, "P50-W7X8Y9": 50, "P50-Z1A2B3": 50
}

WARNING_MESSAGE = """⚠️ <b>تنبيه وإخلاء مسؤولية:</b>

أهلاً بك! صُمم هذا البوت لتسهيل حفظ وتحميل المحتوى المباح والنافع.

نرجو تذكر قول الله تعالى:
﴿ مَا يَلْفِظُ مِنْ قَوْلٍ إِلَّا لَدَيْهِ رَقِيبٌ عَتِيدٌ ﴾

نبرأ إلى الله من استخدام هذا البوت في تحميل ما حرّم الله (كالمقاطع المحرمة والمنكرات)، أو انتهاك حقوق الملكية الفكرية للآخرين بغير حق.

<b>المستخدم وحده يتحمل المسؤولية كاملة أمام الله عن طبيعة استخدامه.</b>

---
👤 <b>المالكين:</b> {owner1} و {owner2}
"""

SUPPORTED_DOMAINS = {
    "youtube.com": "يوتيوب", "youtu.be": "يوتيوب",
    "tiktok.com": "تيك توك", "vm.tiktok.com": "تيك توك",
    "facebook.com": "فيسبوك", "fb.watch": "فيسبوك",
    "instagram.com": "إنستغرام",
}

MAX_FILE_SIZE_MB = 50
TEMP_DIR = Path(tempfile.gettempdir()) / "tg_downloader_bot"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# 2. إعداد قاعدة البيانات السحابية (MongoDB)
# ============================================================
try:
    client = MongoClient(MONGODB_URI)
    db = client['telegram_bot_db']
    users_collection = db['users']
    used_codes_collection = db['used_codes']
    logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح.")
except Exception as e:
    logger.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")

def get_user(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        return user.get("points", 0), user.get("referred_by", None)
    return None

def add_user(user_id, referred_by=None):
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "points": 0, "referred_by": referred_by})

def update_points(user_id, amount):
    users_collection.update_one({"user_id": user_id}, {"$inc": {"points": amount}}, upsert=True)

def get_stats():
    total_users = users_collection.count_documents({})
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$points"}}}]
    result = list(users_collection.aggregate(pipeline))
    total_points = result[0]["total"] if result else 0
    return total_users, total_points

# ============================================================
# 3. دوال مساعدة للتحميل والاشتراك
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

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']: return True
    except Exception as e:
        logger.error(f"خطأ في التحقق من الاشتراك: {e}")
        return True 

    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "⚠️ <b>عذراً عزيزي،</b>\n\nلاستخدام البوت، يجب عليك الاشتراك في قناتنا أولاً.\nاضغط على الزر أدناه للاشتراك، ثم اضغط على زر 'تحقق من الاشتراك'."
    
    if update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return False

# ============================================================
# 4. معالجات البوت
# ============================================================
async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_subscription(update, context):
        await query.message.edit_text("✅ شكراً لاشتراكك! يمكنك الآن استخدام البوت بإرسال /start")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): return
    user_id = update.effective_user.id
    bot_username = context.bot.username
    
    referred_by = None
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id: referred_by = referrer_id
        except ValueError: pass

    user = get_user(user_id)
    if not user:
        add_user(user_id, referred_by)
        if referred_by:
            update_points(referred_by, REFERRAL_REWARD)
            try: await context.bot.send_message(referred_by, f"🎉 مبروك! انضم شخص جديد عبر رابطك، وحصلت على {REFERRAL_REWARD} نقطة.")
            except Exception: pass
        user = get_user(user_id)

    points = user[0]
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    welcome_text = (
        f"🤖 <b>أهلاً بك في بوت التحميل!</b>\n\n"
        f"💰 <b>رصيدك الحالي:</b> {points} نقطة\n"
        f"(تكلفة تحميل الفيديو الواحد: {DOWNLOAD_COST} نقاط)\n\n"
        f"🔗 <b>رابط الإحالة الخاص بك:</b>\n<code>{ref_link}</code>\n"
        f"(شارك الرابط، واحصل على {REFERRAL_REWARD} نقطة لكل شخص جديد!)\n\n"
        f"📥 <b>كيفية الاستخدام:</b> فقط قم بإرسال رابط الفيديو هنا.\n\n"
        f"👇 <i>يرجى قراءة التنبيه التالي:</i>\n\n"
    )
    warning_text = WARNING_MESSAGE.format(owner1=OWNER_1, owner2=OWNER_2)
    await update.message.reply_text(welcome_text + warning_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): return
    user_id = update.effective_user.id
    bot_username = context.bot.username
    user = get_user(user_id) or (0, None)
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    text = (
        f"💰 <b>رصيدك الحالي:</b> {user[0]} نقطة\n\n"
        f"🔗 <b>رابط الإحالة الخاص بك:</b>\n<code>{ref_link}</code>\n"
        f"🎁 <b>لشحن النقاط:</b> <code>/redeem الكود</code>\n🛒 <b>للشراء:</b> /buy"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): return
    user_id = update.effective_user.id
    
    # استخراج النص بعد كلمة redeem مباشرة وتجاهل أي مسافات زائدة
    message_text = update.message.text
    parts = message_text.split(maxsplit=1) 
    
    if len(parts) < 2:
        return await update.message.reply_text("❌ يرجى كتابة الكود بعد الأمر. مثال:\n<code>/redeem الكود_هنا</code>", parse_mode=ParseMode.HTML)
        
    code = parts[1].strip().upper() # أخذ الكود وتحويله لحروف كبيرة
    
    if code not in PROMO_CODES:
        return await update.message.reply_text("❌ هذا الكود غير صحيح.")
        
    if used_codes_collection.find_one({"code": code}):
        return await update.message.reply_text("❌ عذراً، هذا الكود تم استخدامه مسبقاً.")
        
    points_to_add = PROMO_CODES[code]
    used_codes_collection.insert_one({"code": code, "user_id": user_id})
    update_points(user_id, points_to_add)
    await update.message.reply_text(f"✅ تم شحن حسابك!\n💰 حصلت على <b>{points_to_add}</b> نقطة.", parse_mode=ParseMode.HTML)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): return
    text = f"🛒 <b>لشراء النقاط:</b>\nتواصل مع المالكين:\n👤 {OWNER_1}\n👤 {OWNER_2}\n\nأرسل الكود الذي يعطوك إياه هكذا:\n<code>/redeem الكود</code>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): return
    username = update.effective_user.username
    if f"@{username}" not in [OWNER_1, OWNER_2]:
        return await update.message.reply_text("❌ هذا الأمر للمالكين فقط.")
    total_users, total_points = get_stats()
    await update.message.reply_text(f"📊 <b>الإحصائيات:</b>\n👥 المستخدمين: {total_users}\n💰 النقاط: {total_points}", parse_mode=ParseMode.HTML)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): return
    message = update.message
    user_id = message.from_user.id
    url = message.text.strip()

    if not re.search(r"https?://", url, re.IGNORECASE):
        return await message.reply_text("❌ الرجاء إرسال رابط صالح.")

    supported, platform_name = is_supported_url(url)
    if not supported:
        return await message.reply_text("❌ المنصة غير مدعومة.")

    user = get_user(user_id) or (0, None)
    if user[0] < DOWNLOAD_COST:
        return await message.reply_text(f"❌ رصيدك غير كافٍ! تحتاج {DOWNLOAD_COST} نقاط.\nرصيدك: {user[0]}\n\n🔗 اجمع النقاط: /points\n🛒 اشتري: /buy", parse_mode=ParseMode.HTML)

    update_points(user_id, -DOWNLOAD_COST)
    processing_msg = await message.reply_text(f"⏳ جاري معالجة {platform_name}...\n(تم خصم {DOWNLOAD_COST} نقاط)")
    await message.chat.send_action(ChatAction.UPLOAD_VIDEO)

    task_dir = TEMP_DIR / f"task_{message.message_id}_{user_id}"
    task_dir.mkdir(exist_ok=True, parents=True)
    file_path = None
    
    try:
        file_path, info = await asyncio.to_thread(download_video, url, task_dir)
        if file_path.stat().st_size / (1024 * 1024) > MAX_FILE_SIZE_MB:
            raise ValueError(f"حجم الفيديو أكبر من {MAX_FILE_SIZE_MB} ميجا.")

        warning_caption = WARNING_MESSAGE.format(owner1=OWNER_1, owner2=OWNER_2)
        with open(file_path, "rb") as video_file:
            await message.reply_video(
                video=video_file, caption=warning_caption[:1024], parse_mode=ParseMode.HTML,
                supports_streaming=True, filename=file_path.name,
                read_timeout=300, write_timeout=300, connect_timeout=300
            )
        await processing_msg.delete()
    except Exception as e:
        logger.exception(f"خطأ: {e}")
        update_points(user_id, DOWNLOAD_COST)
        await processing_msg.edit_text("❌ حدث خطأ أثناء التحميل.\n✅ تم إرجاع النقاط إلى رصيدك.")
    finally:
        if file_path: await cleanup_file(file_path)
        try:
            if task_dir.exists() and not any(task_dir.iterdir()): await asyncio.to_thread(task_dir.rmdir)
        except Exception: pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="حدث استثناء:", exc_info=context.error)

# ============================================================
# 5. التشغيل
# ============================================================
def main():
    if not BOT_TOKEN or not MONGODB_URI:
        raise ValueError("الرجاء تعيين BOT_TOKEN و MONGODB_URI أولاً.")

    async def post_init(application: Application) -> None:
        await application.bot.set_my_commands([
            BotCommand("start", "بدء استخدام البوت"),
            BotCommand("points", "عرض رصيدك"),
            BotCommand("redeem", "شحن النقاط بكود"),
            BotCommand("buy", "شراء النقاط"),
        ])

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(300).write_timeout(300).connect_timeout(300)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("points", points_command))
    application.add_handler(CommandHandler("redeem", redeem_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_error_handler(error_handler)

    logger.info("✅ البوت يعمل الآن وقاعدة البيانات متصلة...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
