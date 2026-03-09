"""
翻譯模組
翻譯規則：
  高棉語 → 中文
  中文   → 高棉語
  英文   → 中文
"""

import logging
import os
from typing import Optional, Tuple

from openai import AsyncOpenAI

from dictionary import lookup_dictionary

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = "gpt-4.1-mini"


def detect_language(text: str) -> str:
    """
    偵測語言：優先用 Unicode 範圍判斷高棉語與中文，
    其餘交給 langdetect，無法判斷時預設 'en'。
    Returns: 'km' | 'zh' | 'en'
    """
    khmer_count = 0
    chinese_count = 0
    total = 0

    for ch in text:
        if ch.isspace() or not ch.isprintable():
            continue
        total += 1
        cp = ord(ch)
        if 0x1780 <= cp <= 0x17FF or 0x19E0 <= cp <= 0x19FF:
            khmer_count += 1
        elif (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF
              or 0xF900 <= cp <= 0xFAFF):
            chinese_count += 1

    if total == 0:
        return "en"

    if khmer_count / total > 0.25:
        return "km"
    if chinese_count / total > 0.25:
        return "zh"

    # 用 langdetect 輔助判斷
    try:
        from langdetect import detect
        lang = detect(text)
        if lang == "km":
            return "km"
        if lang in ("zh-cn", "zh-tw", "zh"):
            return "zh"
    except Exception:
        pass

    return "en"


async def _gpt_translate(text: str, src: str, tgt: str) -> str:
    """呼叫 GPT，只回傳譯文本身。"""
    lang_name = {
        "km": "Khmer (高棉語/柬埔寨語)",
        "zh": "Simplified Chinese (簡體中文)",
        "en": "English",
    }
    resp = await client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional translator specializing in Khmer, "
                    "Chinese, and English. Output only the translated text, "
                    "no explanations or extra content."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Translate from {lang_name[src]} to {lang_name[tgt]}:\n\n{text}"
                ),
            },
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    result = resp.choices[0].message.content.strip()
    logger.info("GPT 翻譯 %s→%s 完成", src, tgt)
    return result


async def translate_message(text: str) -> Optional[Tuple[str, str, str]]:
    """
    翻譯入口。
    Returns: (source_lang, original, translated) 或 None
    """
    text = text.strip()
    if not text:
        return None

    # 1. 優先查字典
    hit = lookup_dictionary(text)
    if hit:
        src, translated = hit
        return (src, text, translated)

    # 2. 偵測語言
    src = detect_language(text)
    logger.info("語言偵測: %s | %.50s", src, text)

    # 3. 依規則翻譯
    if src == "km":
        translated = await _gpt_translate(text, "km", "zh")
        return ("km", text, translated)
    elif src == "zh":
        translated = await _gpt_translate(text, "zh", "km")
        return ("zh", text, translated)
    else:
        # 英文或其他 → 中文
        translated = await _gpt_translate(text, "en", "zh")
        return ("en", text, translated)


def format_translation(source_lang: str, original: str, translated: str) -> str:
    """
    格式化翻譯輸出：
      km→zh : 🌐 翻譯 / 🇰🇭 Khmer: <原文> / 🇨🇳 中文: <譯文>
      zh→km : 🌐 翻譯 / 🇨🇳 中文: <原文> / 🇰🇭 Khmer: <譯文>
      en→zh : 🌐 翻譯 / 🇬🇧 English: <原文> / 🇨🇳 中文: <譯文>
    """
    if source_lang == "km":
        return f"🌐 翻譯\n🇰🇭 Khmer: {original}\n🇨🇳 中文: {translated}"
    elif source_lang == "zh":
        return f"🌐 翻譯\n🇨🇳 中文: {original}\n🇰🇭 Khmer: {translated}"
    else:
        return f"🌐 翻譯\n🇬🇧 English: {original}\n🇨🇳 中文: {translated}"
