"""
語音翻譯模組 - 使用 OpenAI Whisper 辨識語音並翻譯
支援 Telegram voice message (OGG/OGA) 格式
"""

import logging
import os
import tempfile
from typing import Optional, Tuple

from openai import AsyncOpenAI
from pydub import AudioSegment

from translator import detect_language, translate_with_gpt

logger = logging.getLogger(__name__)

# 初始化 OpenAI 客戶端
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def convert_ogg_to_mp3(ogg_path: str) -> str:
    """
    將 OGG 格式轉換為 MP3 格式。

    Telegram 語音訊息使用 OGG Opus 編碼，
    需要轉換為 Whisper 支援的格式。

    Args:
        ogg_path: OGG 檔案路徑

    Returns:
        MP3 檔案路徑
    """
    try:
        mp3_path = ogg_path.replace(".ogg", ".mp3").replace(".oga", ".mp3")
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(mp3_path, format="mp3")
        logger.info(f"音頻轉換完成: {ogg_path} → {mp3_path}")
        return mp3_path
    except Exception as e:
        logger.error(f"音頻轉換失敗: {e}")
        raise


async def transcribe_audio(audio_path: str) -> str:
    """
    使用 OpenAI Whisper 辨識語音。

    Args:
        audio_path: 音頻檔案路徑（MP3 格式）

    Returns:
        辨識出的文字
    """
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )
        logger.info(f"語音辨識完成: {transcript[:50]}...")
        return transcript.strip()
    except Exception as e:
        logger.error(f"語音辨識失敗: {e}")
        raise


async def process_voice_message(ogg_path: str) -> Optional[Tuple[str, str, str]]:
    """
    處理語音訊息的完整流程。

    流程：OGG → MP3 → Whisper 辨識 → 語言偵測 → GPT 翻譯

    Args:
        ogg_path: Telegram 下載的 OGG 語音檔案路徑

    Returns:
        (source_lang, recognized_text, translated_text) 或 None
    """
    mp3_path = None
    try:
        # 1. 轉換音頻格式
        mp3_path = await convert_ogg_to_mp3(ogg_path)

        # 2. Whisper 語音辨識
        recognized_text = await transcribe_audio(mp3_path)

        if not recognized_text:
            logger.warning("語音辨識結果為空")
            return None

        # 3. 偵測語言
        source_lang = detect_language(recognized_text)
        logger.info(f"語音語言偵測: {source_lang}")

        # 4. 翻譯
        if source_lang == "km":
            translated = await translate_with_gpt(recognized_text, "km", "zh")
            return ("km", recognized_text, translated)
        elif source_lang == "zh":
            translated = await translate_with_gpt(recognized_text, "zh", "km")
            return ("zh", recognized_text, translated)
        elif source_lang == "en":
            zh_translated = await translate_with_gpt(recognized_text, "en", "zh")
            return ("en", recognized_text, zh_translated)
        else:
            # 預設翻譯為中文
            translated = await translate_with_gpt(recognized_text, "en", "zh")
            return ("unknown", recognized_text, translated)

    except Exception as e:
        logger.error(f"語音處理失敗: {e}")
        raise
    finally:
        # 清理暫存檔案
        for path in [ogg_path, mp3_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.debug(f"已清理暫存檔案: {path}")
                except OSError:
                    pass


def format_voice_translation(
    source_lang: str, recognized: str, translated: str
) -> str:
    """
    格式化語音翻譯輸出。

    Args:
        source_lang: 來源語言
        recognized: 辨識出的文字
        translated: 翻譯結果

    Returns:
        格式化後的訊息字串
    """
    if source_lang == "km":
        return (
            f"🎤 語音翻譯\n"
            f"🇰🇭 Khmer: {recognized}\n"
            f"🇨🇳 中文: {translated}"
        )
    elif source_lang == "zh":
        return (
            f"🎤 語音翻譯\n"
            f"🇨🇳 中文: {recognized}\n"
            f"🇰🇭 Khmer: {translated}"
        )
    elif source_lang == "en":
        return (
            f"🎤 語音翻譯\n"
            f"🇬🇧 English: {recognized}\n"
            f"🇨🇳 中文: {translated}"
        )
    else:
        return (
            f"🎤 語音翻譯\n"
            f"🗣️ 辨識: {recognized}\n"
            f"🇨🇳 中文: {translated}"
        )
