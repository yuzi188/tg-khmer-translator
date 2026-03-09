"""
Telegram 高棉語-中文翻譯 Bot 主程式
支援文字翻譯、語音翻譯、廚房字典
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

# ──────────────────────────────────────────────
# Logging 設定
# ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# 降低 httpx 的日誌等級
logging.getLogger("httpx").setLevel(logging.WARNING)

# ──────────────────────────────────────────────
# 環境變數
# ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN 環境變數未設定")


# ──────────────────────────────────────────────
# 指令處理器
# ──────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /start 指令"""
    stats = get_dictionary_stats()
    welcome_message = (
        "🌐 <b>高棉語-中文翻譯 Bot</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 歡迎使用翻譯 Bot！\n\n"
        "📝 <b>功能說明：</b>\n"
        "• 自動偵測語言並翻譯\n"
        "• 高棉語 🇰🇭 ↔ 中文 🇨🇳 互譯\n"
        "• 英文 🇬🇧 → 中文 + 高棉語\n"
        "• 語音訊息自動辨識翻譯 🎤\n"
        f"• 內建廚房字典（{stats['total_pairs']} 組詞彙）📖\n\n"
        "📌 <b>使用方式：</b>\n"
        "直接傳送文字或語音訊息即可自動翻譯\n\n"
        "⌨️ <b>指令列表：</b>\n"
        "/start - 顯示 Bot 說明\n"
        "/help - 顯示使用方式\n"
        "/language - 設定翻譯語言\n"
    )
    await update.message.reply_text(welcome_message, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /help 指令"""
    help_message = (
        "📖 <b>使用說明</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ <b>文字翻譯</b>\n"
        "直接傳送文字訊息，Bot 會自動偵測語言並翻譯：\n"
        "• 高棉語 → 中文\n"
        "• 中文 → 高棉語\n"
        "• 英文 → 中文 + 高棉語\n\n"
        "2️⃣ <b>語音翻譯</b>\n"
        "傳送語音訊息，Bot 會：\n"
        "• 自動辨識語音內容\n"
        "• 翻譯成對應語言\n\n"
        "3️⃣ <b>廚房字典</b>\n"
        "常用廚房詞彙會優先使用內建字典翻譯，\n"
        "速度更快、更準確。\n\n"
        "💡 <b>提示：</b>\n"
        "• 在群組中使用時，Bot 會以 reply 方式回覆\n"
        "• 支援私聊和群組使用\n"
    )
    await update.message.reply_text(help_message, parse_mode="HTML")


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /language 指令"""
    language_message = (
        "🌍 <b>翻譯語言設定</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "目前支援的翻譯方向：\n\n"
        "🇰🇭 高棉語 (Khmer) → 🇨🇳 中文\n"
        "🇨🇳 中文 → 🇰🇭 高棉語 (Khmer)\n"
        "🇬🇧 英文 (English) → 🇨🇳 中文 + 🇰🇭 高棉語\n\n"
        "💡 Bot 會自動偵測您的訊息語言，\n"
        "無需手動設定！直接傳送訊息即可。"
    )
    await update.message.reply_text(language_message, parse_mode="HTML")


# ──────────────────────────────────────────────
# 訊息處理器
# ──────────────────────────────────────────────
async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """處理文字訊息 - 自動翻譯"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # 忽略指令
    if text.startswith("/"):
        return

    # 忽略太短的訊息
    if len(text) < 1:
        return

    try:
        result = await translate_message(text)
        if result:
            source_lang, original, translated = result
            response = format_translation(source_lang, original, translated)
            # 使用 reply 方式回覆，避免洗版
            await update.message.reply_text(response)
        else:
            logger.warning(f"無法翻譯訊息: {text[:50]}")
    except Exception as e:
        logger.error(f"翻譯處理錯誤: {e}")
        await update.message.reply_text("⚠️ 翻譯失敗，請稍後再試。")


async def handle_voice_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """處理語音訊息 - 語音辨識 + 翻譯"""
    if not update.message or not update.message.voice:
        return

    # 傳送處理中提示
    processing_msg = await update.message.reply_text("🔄 正在處理語音訊息...")

    ogg_path = None
    try:
        # 1. 下載語音檔案
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        # 建立暫存檔案
        ogg_path = os.path.join(tempfile.gettempdir(), f"{voice.file_id}.ogg")
        await voice_file.download_to_drive(ogg_path)
        logger.info(f"語音檔案已下載: {ogg_path}")

        # 2. 處理語音（辨識 + 翻譯）
        result = await process_voice_message(ogg_path)

        if result:
            source_lang, recognized, translated = result
            response = format_voice_translation(source_lang, recognized, translated)
        else:
            response = "⚠️ 無法辨識語音內容，請重新錄製。"

        # 3. 更新回覆訊息
        await processing_msg.edit_text(response)

    except Exception as e:
        logger.error(f"語音處理錯誤: {e}")
        await processing_msg.edit_text("⚠️ 語音處理失敗，請稍後再試。")


# ──────────────────────────────────────────────
# 錯誤處理
# ──────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """全域錯誤處理器"""
    logger.error(f"Update {update} caused error: {context.error}")


# ──────────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────────
def main() -> None:
    """啟動 Bot"""
    logger.info("正在啟動翻譯 Bot...")

    # 建立 Application
    application = Application.builder().token(BOT_TOKEN).build()

    # 註冊指令處理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("language", language_command))

    # 註冊訊息處理器
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )
    application.add_handler(
        MessageHandler(filters.VOICE, handle_voice_message)
    )

    # 註冊錯誤處理器
    application.add_error_handler(error_handler)

    # 啟動 Bot（使用 polling 模式）
    logger.info("Bot 已啟動，開始接收訊息...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
