"""
翻譯模組 - 使用 OpenAI GPT 進行高棉語 ↔ 中文翻譯
整合字典優先查詢與 GPT 翻譯
"""

import logging
import os
from typing import Optional, Tuple

from openai import AsyncOpenAI

from dictionary import lookup_dictionary

logger = logging.getLogger(__name__)

# 初始化 OpenAI 客戶端
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# GPT 模型設定
GPT_MODEL = "gpt-4.1-mini"


def detect_language(text: str) -> str:
    """
    偵測文字語言。

    使用 Unicode 範圍判斷：
    - 高棉語: U+1780–U+17FF
    - 中文: U+4E00–U+9FFF, U+3400–U+4DBF
    - 其他: 英文或未知

    Returns:
        'km' (高棉語), 'zh' (中文), 'en' (英文/其他)
    """
    khmer_count = 0
    chinese_count = 0
    latin_count = 0
    total = 0

    for char in text:
        if char.isspace() or not char.isprintable():
            continue
        total += 1
        code = ord(char)
        # 高棉語 Unicode 範圍
        if 0x1780 <= code <= 0x17FF or 0x19E0 <= code <= 0x19FF:
            khmer_count += 1
        # 中文 Unicode 範圍
        elif (0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF
              or 0xF900 <= code <= 0xFAFF):
            chinese_count += 1
        # 拉丁字母
        elif (0x0041 <= code <= 0x005A or 0x0061 <= code <= 0x007A):
            latin_count += 1

    if total == 0:
        return "en"

    khmer_ratio = khmer_count / total
    chinese_ratio = chinese_count / total

    if khmer_ratio > 0.3:
        return "km"
    elif chinese_ratio > 0.3:
        return "zh"
    else:
        return "en"


async def translate_with_gpt(text: str, source_lang: str, target_lang: str) -> str:
    """
    使用 GPT 進行翻譯。

    Args:
        text: 要翻譯的文字
        source_lang: 來源語言 ('km', 'zh', 'en')
        target_lang: 目標語言 ('km', 'zh', 'en')

    Returns:
        翻譯後的文字
    """
    lang_names = {
        "km": "Khmer (高棉語/柬埔寨語)",
        "zh": "Chinese (中文)",
        "en": "English (英文)",
    }

    source_name = lang_names.get(source_lang, source_lang)
    target_name = lang_names.get(target_lang, target_lang)

    system_prompt = (
        "You are a professional translator specializing in Khmer, Chinese, and English. "
        "Translate the given text accurately and naturally. "
        "Only output the translated text, no explanations or extra content. "
        "For Khmer text, use proper Khmer script. "
        "For Chinese text, use Simplified Chinese (简体中文). "
        "Maintain the original meaning and tone."
    )

    user_prompt = (
        f"Translate the following text from {source_name} to {target_name}:\n\n{text}"
    )

    try:
        response = await client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"GPT 翻譯完成: {source_lang}→{target_lang}")
        return result
    except Exception as e:
        logger.error(f"GPT 翻譯錯誤: {e}")
        raise


async def translate_message(text: str) -> Optional[Tuple[str, str, str]]:
    """
    翻譯訊息的主要入口。

    流程：
    1. 先查字典
    2. 字典未命中則偵測語言並使用 GPT 翻譯

    Args:
        text: 使用者傳送的文字

    Returns:
        (source_lang, original_text, translated_text) 或 None
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    # 1. 優先查字典
    dict_result = lookup_dictionary(text)
    if dict_result:
        source_lang, translated = dict_result
        return (source_lang, text, translated)

    # 2. 偵測語言
    source_lang = detect_language(text)
    logger.info(f"偵測語言: {source_lang}, 文字: {text[:50]}...")

    # 3. 根據語言決定翻譯方向
    if source_lang == "km":
        # 高棉語 → 中文
        translated = await translate_with_gpt(text, "km", "zh")
        return ("km", text, translated)
    elif source_lang == "zh":
        # 中文 → 高棉語
        translated = await translate_with_gpt(text, "zh", "km")
        return ("zh", text, translated)
    elif source_lang == "en":
        # 英文 → 同時翻譯成中文和高棉語
        zh_translated = await translate_with_gpt(text, "en", "zh")
        km_translated = await translate_with_gpt(text, "en", "km")
        return ("en", text, f"{km_translated}\n🇨🇳 中文: {zh_translated}")
    else:
        return None


def format_translation(source_lang: str, original: str, translated: str) -> str:
    """
    格式化翻譯輸出。

    Args:
        source_lang: 來源語言
        original: 原文
        translated: 翻譯結果

    Returns:
        格式化後的訊息字串
    """
    if source_lang == "km":
        return (
            f"🌐 翻譯\n"
            f"🇰🇭 Khmer: {original}\n"
            f"🇨🇳 中文: {translated}"
        )
    elif source_lang == "zh":
        return (
            f"🌐 翻譯\n"
            f"🇨🇳 中文: {original}\n"
            f"🇰🇭 Khmer: {translated}"
        )
    elif source_lang == "en":
        # 英文的情況，translated 已包含兩種翻譯
        return (
            f"🌐 翻譯\n"
            f"🇬🇧 English: {original}\n"
            f"🇰🇭 Khmer: {translated}"
        )
    else:
        return f"🌐 翻譯\n{translated}"
