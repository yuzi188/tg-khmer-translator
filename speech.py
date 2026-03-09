"""
語音翻譯模組
流程：下載 .ogg → 直接送 OpenAI Whisper → 偵測語言 → GPT 翻譯
Whisper 原生支援 .ogg 格式，不需要 pydub 或 ffmpeg。
"""

import logging
import os
import tempfile
from typing import Optional, Tuple

from openai import AsyncOpenAI

from translator import detect_language, _gpt_translate

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def transcribe_ogg(ogg_path: str) -> str:
    """
    直接將 .ogg 檔送給 Whisper 辨識，回傳文字。
    Whisper 原生支援 OGG Opus 格式。
    """
    with open(ogg_path, "rb") as f:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text",
        )
    text = transcript.strip() if isinstance(transcript, str) else str(transcript).strip()
    logger.info("Whisper 辨識完成: %.60s", text)
    return text


async def process_voice_message(ogg_path: str) -> Optional[Tuple[str, str, str]]:
    """
    處理語音訊息完整流程。
    Returns: (source_lang, recognized_text, translated_text) 或 None
    """
    try:
        # 1. Whisper 辨識
        recognized = await transcribe_ogg(ogg_path)
        if not recognized:
            logger.warning("Whisper 辨識結果為空")
            return None

        # 2. 偵測語言
        src = detect_language(recognized)
        logger.info("語音語言偵測: %s", src)

        # 3. 依規則翻譯（同文字翻譯規則）
        if src == "km":
            translated = await _gpt_translate(recognized, "km", "zh")
        elif src == "zh":
            translated = await _gpt_translate(recognized, "zh", "km")
        else:
            translated = await _gpt_translate(recognized, "en", "zh")

        return (src, recognized, translated)

    except Exception as e:
        logger.error("語音處理失敗: %s", e)
        raise
    finally:
        # 清理暫存檔
        if ogg_path and os.path.exists(ogg_path):
            try:
                os.remove(ogg_path)
            except OSError:
                pass


def format_voice_translation(src: str, recognized: str, translated: str) -> str:
    """
    格式化語音翻譯輸出。
    """
    if src == "km":
        return f"🎤 語音翻譯\n🇰🇭 Khmer: {recognized}\n🇨🇳 中文: {translated}"
    elif src == "zh":
        return f"🎤 語音翻譯\n🇨🇳 中文: {recognized}\n🇰🇭 Khmer: {translated}"
    else:
        return f"🎤 語音翻譯\n🇬🇧 English: {recognized}\n🇨🇳 中文: {translated}"
