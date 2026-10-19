import os
import re
import asyncio
import tempfile
import logging
from pathlib import Path

from telegram import Update
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

# ⚠️ ضع التوكن الخاص بك هنا
BOT_TOKEN = "8914214210:AAFn_9caVKbHiQb9-AajsRf8NBVJADpLnHU"

# أسماء المالكين
OWNER_1 = "@RAHLI_1"
OWNER_2 = "@TV_19_VPI"

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

# الحد الأقصى لحجم الملف
MAX_FILE_SIZE_MB = 50

# مجلد مؤقت للتحميلات
TEMP_DIR = Path(tempfile.gettempdir()) / "tg_downloader_bot"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================================
# 2. دوال مساعدة
# ============================================================

def extract_domain(url: str):
    url = url.strip()
    match = re.match(r"^(?:https?://)?(?:www\.)?([^/]+)", url, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower().split(":")[0]

def is_supported_url(url: str):
    domain = extract_domain(url)
    if not domain:
        return False, None
    if domain in SUPPORTED_DOMAINS:
        return True, SUPPORTED_DOMAINS[domain]
    for supported_domain, platform_name in SUPPORTED_DOMAINS.items():
        if domain.endswith("." + supported_domain):
            return True, platform_name
    return False, None

def download_video(url: str, output_dir: Path):
    ydl_opts = {
        "outtmpl": str(output_dir / "%(title).100s_%(id)s.%(ext)s"),
        "format": "best[ext=mp4]/best", 
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "max_filesize": MAX_FILE_SIZE_MB * 1024 * 1024,
        "extractor_args": {"youtube": {"player_client": ["tv", "mweb", "android"]}},
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = Path(ydl.prepare_filename(info))
        
        if not file_path.exists():
            files = sorted(output_dir.glob("*"), key=os.path.getmtime, reverse=True)
            if files:
                file_path = files[0]
            else:
                raise FileNotFoundError("لم يتم العثور على الملف بعد التحميل.")
        return file_path, info

async def cleanup_file(path: Path):
    try:
        if path.exists():
            await asyncio.to_thread(path.unlink)
    except Exception as e:
        logger.warning(f"فشل حذف الملف المؤقت {path}: {e}")

# ============================================================
# 3. معالجات البوت
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 <b>أهلاً بك في بوت التحميل!</b>\n\n"
        "📥 <b>كيفية الاستخدام:</b>\n"
        "فقط قم بإرسال رابط الفيديو هنا وسأقوم بتحميله وإرساله لك فوراً.\n"
        "⚠️ <i>ملاحظة: الحد الأقصى لحجم الفيديو هو 50 ميجابايت.</i>\n\n"
        "🔹 <b>المنصات المدعومة:</b>\n"
        "1. يوتيوب (YouTube)\n"
        "2. تيك توك (TikTok)\n"
        "3. فيسبوك (Facebook)\n"
        "4. إنستغرام (Instagram)\n\n"
        "👇 <i>يرجى قراءة التنبيه التالي:</i>\n\n"
    )
    warning_text = WARNING_MESSAGE.format(owner1=OWNER_1, owner2=OWNER_2)
    
    await update.message.reply_text(
        welcome_text + warning_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    url = message.text.strip()

    if not re.search(r"https?://", url, re.IGNORECASE):
        await message.reply_text("❌ الرجاء إرسال رابط فيديو صالح.")
        return

    supported, platform_name = is_supported_url(url)
    if not supported:
        await message.reply_text("❌ عذراً، المنصة غير مدعومة.\nالمنصات المدعومة فقط: يوتيوب، تيك توك، فيسبوك، إنستغرام.")
        return

    processing_msg = await message.reply_text(f"⏳ جاري معالجة رابط {platform_name}...\nيرجى الانتظار.")
    await message.chat.send_action(ChatAction.UPLOAD_VIDEO)

    task_dir = TEMP_DIR / f"task_{message.message_id}_{message.from_user.id}"
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
            # زيادة وقت الانتظار إلى 300 ثانية (5 دقائق)
            await message.reply_video(
                video=video_file,
                caption=warning_caption,
                parse_mode=ParseMode.HTML,
                supports_streaming=True,
                filename=file_path.name,
                read_timeout=300,  
                write_timeout=300, 
                connect_timeout=300 
            )
        await processing_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        error_text = str(e).lower()
        if "sign in" in error_text or "confirm you're not a bot" in error_text:
            user_msg = "❌ يوتيوب يطلب تسجيل الدخول (حماية من البوتات).\nجرب إرسال الرابط مرة أخرى."
        elif "private" in error_text:
            user_msg = "❌ الفيديو خاص أو غير متاح للعامة."
        else:
            user_msg = "❌ تعذر تحميل الفيديو. قد يكون الرابط معطلاً أو المحتوى محمياً."
        await processing_msg.edit_text(user_msg)
        
    except ValueError as e:
        await processing_msg.edit_text(f"❌ {e}")
        
    except Exception as e:
        logger.exception(f"خطأ غير متوقع: {e}")
        await processing_msg.edit_text("❌ حدث خطأ غير متوقع (بطء في الإنترنت أثناء الرفع).")
        
    finally:
        if file_path:
            await cleanup_file(file_path)
        try:
            if task_dir.exists() and not any(task_dir.iterdir()):
                await asyncio.to_thread(task_dir.rmdir)
        except Exception:
            pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="حدث استثناء:", exc_info=context.error)

# ============================================================
# 4. تشغيل البوت
# ============================================================

def main():
    if not BOT_TOKEN or BOT_TOKEN == "ضع_التوكن_الخاص_بك_هنا":
        raise ValueError("الرجاء تعيين BOT_TOKEN أولاً.")

    # 🔥 زيادة أوقات الانتظار إلى 5 دقائق
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(300)
        .write_timeout(300)
        .connect_timeout(300)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_error_handler(error_handler)

    logger.info("✅ البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
