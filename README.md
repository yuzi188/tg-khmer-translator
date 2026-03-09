# 🌐 Telegram 高棉語-中文翻譯 Bot

一個功能完整的 Telegram 翻譯機器人，支援高棉語（Khmer）與中文之間的即時翻譯，包含語音辨識翻譯功能。

## 功能特色

### 📝 文字翻譯
- 自動偵測語言（高棉語 / 中文 / 英文）
- 高棉語 🇰🇭 → 中文 🇨🇳
- 中文 🇨🇳 → 高棉語 🇰🇭
- 英文 🇬🇧 → 中文 + 高棉語
- 使用 reply message 方式回覆（不洗版）

### 🎤 語音翻譯
- 支援 Telegram 語音訊息
- 流程：語音 → Whisper 辨識 → GPT 翻譯 → 回覆

### 📖 廚房字典
- 內建常用廚房與日常詞彙
- 優先使用字典翻譯，速度更快
- 可擴充更多詞彙

### ⌨️ 指令
| 指令 | 說明 |
|------|------|
| `/start` | 顯示 Bot 說明 |
| `/help` | 顯示使用方式 |
| `/language` | 設定翻譯語言 |

## 技術架構

- **語言**: Python 3.11
- **框架**: python-telegram-bot 21.x (async)
- **翻譯**: OpenAI GPT-4.1-mini
- **語音辨識**: OpenAI Whisper
- **音頻處理**: pydub + ffmpeg

## 專案結構

```
tg-khmer-translator/
├── main.py           # Bot 主程式
├── translator.py     # 翻譯模組
├── speech.py         # 語音辨識模組
├── dictionary.py     # 廚房字典
├── requirements.txt  # Python 依賴
├── Procfile          # Railway 部署配置
├── railway.json      # Railway 設定
├── nixpacks.toml     # Nixpacks 設定（ffmpeg）
└── README.md         # 專案說明
```

## 環境變數

| 變數名稱 | 說明 |
|----------|------|
| `BOT_TOKEN` | Telegram Bot Token |
| `OPENAI_API_KEY` | OpenAI API Key |

## 部署

本專案使用 Railway 部署，透過 GitHub 倉庫自動部署。

## 授權

MIT License
