"""
Telegram 高棉語-中文翻譯 Bot
- 群組所有訊息自動偵測語言並翻譯（不需指令觸發）
- 高棉語 → 中文
- 中文   → 高棉語
- 英文   → 中文
- 一律用 reply message 方式回覆，不洗版
"""

import logging
import os
import tempfile

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from translator import translate_message, format_translation
from speech import process_voice_message, format_voice_translation
from dictionary import get_dictionary_stats

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ── 環境變數 ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN 環境變數未設定")


# ── 指令處理器 ────────────────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stats = get_dictionary_stats()
    await update.message.reply_text(
        "🌐 <b>高棉語-中文翻譯 Bot</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 <b>自動翻譯規則：</b>\n"
        "🇰🇭 高棉語 → 🇨🇳 中文\n"
        "🇨🇳 中文   → 🇰🇭 高棉語\n"
        "🇬🇧 英文   → 🇨🇳 中文\n\n"
        "🎤 語音訊息自動辨識並翻譯\n"
        f"📖 內建廚房字典（{stats['total_pairs']} 組詞彙）\n\n"
        "直接傳送訊息即可，Bot 會自動以 reply 方式回覆翻譯結果。\n\n"
        "⌨️ /help - 使用說明　/language - 語言資訊",
        parse_mode="HTML",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 <b>使用說明</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ <b>文字翻譯</b>\n"
        "直接傳送任何文字，Bot 自動偵測語言並翻譯：\n"
        "• 高棉語 🇰🇭 → 中文 🇨🇳\n"
        "• 中文 🇨🇳 → 高棉語 🇰🇭\n"
        "• 英文 🇬🇧 → 中文 🇨🇳\n\n"
        "2️⃣ <b>語音翻譯</b>\n"
        "傳送語音訊息，Bot 自動辨識並翻譯。\n\n"
        "3️⃣ <b>廚房字典</b>\n"
        "常用詞彙優先查字典，速度更快更準確。\n\n"
        "💡 所有回覆均以 reply 方式，不會洗版。",
        parse_mode="HTML",
    )


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🌍 <b>翻譯語言資訊</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🇰🇭 高棉語 → 🇨🇳 中文\n"
        "🇨🇳 中文   → 🇰🇭 高棉語\n"
        "🇬🇧 英文   → 🇨🇳 中文\n\n"
        "Bot 自動偵測語言，無需手動設定。",
        parse_mode="HTML",
    )


# ── 訊息處理器 ────────────────────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    群組 / 私聊所有文字訊息自動翻譯。
    一律用 reply_text 回覆原訊息，不洗版。
    """
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()
    if not text:
        return

    logger.info("收到訊息 [chat_id=%s]: %.60s", msg.chat_id, text)

    try:
        result = await translate_message(text)
        if result:
            src, original, translated = result
            reply = format_translation(src, original, translated)
            await msg.reply_text(reply)
        else:
            logger.info("無法判斷語言，略過: %.50s", text)
    except Exception as e:
        logger.error("翻譯失敗: %s", e)
        await msg.reply_text("⚠️ 翻譯失敗，請稍後再試。")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    語音訊息：下載 .ogg → Whisper 辨識 → 翻譯 → reply 回覆。
    """
    msg = update.message
    if not msg or not msg.voice:
        return

    processing = await msg.reply_text("🔄 正在處理語音...")
    ogg_path = None

    try:
        # 下載語音檔（.ogg）
        voice_file = await context.bot.get_file(msg.voice.file_id)
        ogg_path = os.path.join(tempfile.gettempdir(), f"{msg.voice.file_id}.ogg")
        await voice_file.download_to_drive(ogg_path)
        logger.info("語音下載完成: %s", ogg_path)

        # 辨識 + 翻譯
        result = await process_voice_message(ogg_path)
        if result:
            src, recognized, translated = result
            reply = format_voice_translation(src, recognized, translated)
        else:
            reply = "⚠️ 無法辨識語音內容，請重新錄製。"

        await processing.edit_text(reply)

    except Exception as e:
        logger.error("語音處理錯誤: %s", e)
        await processing.edit_text("⚠️ 語音處理失敗，請稍後再試。")


# ── 錯誤處理 ──────────────────────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Update %s 發生錯誤: %s", update, context.error)


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("啟動翻譯 Bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    # 指令
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("language", language_command))

    # 文字訊息（群組 + 私聊，排除指令）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # 語音訊息
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # 錯誤處理
    app.add_error_handler(error_handler)

    logger.info("Bot 開始 polling...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
