"""
廚房字典模組 - 優先使用的翻譯查詢
支援高棉語 ↔ 中文的常用詞彙對照
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# 高棉語 → 中文 字典
KHMER_TO_CHINESE: dict[str, str] = {
    # 肉類
    "សាច់ជ្រូក": "豬肉",
    "សាច់មាន់": "雞肉",
    "សាច់គោ": "牛肉",
    "សាច់ត្រី": "魚肉",
    "សាច់បង្គា": "蝦",
    "សាច់ពពែ": "羊肉",
    "សាច់ទា": "鴨肉",
    # 主食
    "បាយ": "飯",
    "មី": "麵",
    "នំប៉័ង": "麵包",
    "បបរ": "粥",
    # 蔬菜
    "បន្លែ": "蔬菜",
    "ខ្ទឹមបារាំង": "洋蔥",
    "ខ្ទឹមស": "蒜",
    "ម្ទេស": "辣椒",
    "ត្រសក់": "黃瓜",
    "ប៉េងប៉ោះ": "番茄",
    "ស្ពៃ": "白菜",
    # 飲品 / 水
    "ទឹក": "水",
    "ទឹកកក": "冰水",
    "កាហ្វេ": "咖啡",
    "តែ": "茶",
    "ទឹកក្រូច": "橙汁",
    "ស្រាបៀរ": "啤酒",
    # 調味料
    "អំបិល": "鹽",
    "ស្ករ": "糖",
    "ទឹកត្រី": "魚露",
    "ប្រេង": "油",
    "ម្សៅ": "味精",
    # 廚房用語
    "ឆា": "炒",
    "ចម្អិន": "煮",
    "ចៀន": "炸",
    "អាំង": "烤",
    "ស្ងោរ": "燉湯",
    # 日常用語
    "ឈប់សម្រាក": "休息",
    "សួស្តី": "你好",
    "អរគុណ": "謝謝",
    "លាហើយ": "再見",
    "បាទ": "是（男性）",
    "ចាស": "是（女性）",
    "ទេ": "不是",
    "សូម": "請",
    "អត់ទោស": "對不起",
    # 數量 / 單位
    "កីឡូ": "公斤",
    "មួយ": "一",
    "ពីរ": "二",
    "បី": "三",
    "បួន": "四",
    "ប្រាំ": "五",
    # 工作相關
    "ធ្វើការ": "工作",
    "ផ្ទះបាយ": "廚房",
    "ម៉ាស៊ីន": "機器",
    "សម្អាត": "清潔",
}

# 自動生成反向字典：中文 → 高棉語
CHINESE_TO_KHMER: dict[str, str] = {v: k for k, v in KHMER_TO_CHINESE.items()}


def lookup_dictionary(text: str) -> Optional[Tuple[str, str]]:
    """
    在字典中查詢翻譯。

    Args:
        text: 要查詢的文字

    Returns:
        (原文語言標記, 翻譯結果) 或 None（未找到）
        語言標記: 'km' 表示高棉語, 'zh' 表示中文
    """
    text_stripped = text.strip()

    # 先查高棉語 → 中文
    if text_stripped in KHMER_TO_CHINESE:
        logger.info(f"字典命中 (km→zh): {text_stripped}")
        return ("km", KHMER_TO_CHINESE[text_stripped])

    # 再查中文 → 高棉語
    if text_stripped in CHINESE_TO_KHMER:
        logger.info(f"字典命中 (zh→km): {text_stripped}")
        return ("zh", CHINESE_TO_KHMER[text_stripped])

    return None


def get_dictionary_stats() -> dict:
    """取得字典統計資訊"""
    return {
        "khmer_to_chinese": len(KHMER_TO_CHINESE),
        "chinese_to_khmer": len(CHINESE_TO_KHMER),
        "total_pairs": len(KHMER_TO_CHINESE),
    }
