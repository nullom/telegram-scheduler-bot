# Telegram Scheduler Bot

A production-ready Python Telegram bot that collects messages from authorized users and automatically posts them to a private channel at scheduled intervals throughout the day.

## ✨ Features

- **Owner-only access** - Bot accepts messages exclusively from the configured owner
- **Multi-format support** - Handles text, photos, voice messages, audio files, and documents
- **Smart URL detection** - Automatically identifies and logs URLs in text messages
- **Scheduled delivery** - Posts stored messages to your private channel at predefined times
- **Robust storage** - SQLite database with automatic cleanup and monitoring
- **Production logging** - Comprehensive logging system with rotation and error tracking
- **Easy configuration** - Simple `.env` file setup with sensible defaults

## 🚀 Quick Start

1. **Clone and setup:**
```bash
git clone https://github.com/nullom/telegram-scheduler-bot.git
cd telegram-scheduler-bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure:**
```bash
cp .env.example .env
# Edit .env with your bot token and settings
```

3. **Run:**
```bash
python main.py
```

## ⚙️ Configuration

Create `.env` file from the example and configure:

```env
# Bot credentials
BOT_TOKEN=your_bot_token_from_botfather
OWNER_ID=your_telegram_user_id
CHANNEL_ID=your_private_channel_id

# Schedule (7 posts per day, evenly distributed)
SCHEDULED_TIMES=04:07,06:15,10:13,12:15,14:17,16:19,18:21

# Database settings
DB_CLEANUP_DAYS=30
DB_PATH=bot_storage.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=bot.log
```

## 🎯 Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and current status |
| `/status` | Bot health and message statistics |
| `/help` | Command reference and supported formats |
| `/stats` | Detailed analytics and database info |

## 📁 Architecture

```
telegram-scheduler-bot/
├── main.py           # Application entry point
├── config.py         # Environment and settings management
├── handlers.py       # Telegram message processing
├── scheduler.py      # Automatic posting logic
├── database.py       # SQLite operations and queries
├── requirements.txt  # Dependencies
├── .env.example     # Configuration template
└── README.md        # Documentation
```

## 🔒 Security

- **Access control** - Only configured owner can interact with bot
- **Input validation** - Comprehensive message type checking and error handling
- **Secure storage** - Environment-based configuration, no hardcoded credentials
- **Error boundaries** - Graceful handling of malformed or unsupported content

## 📊 Message Flow

1. **Collection** - Owner sends messages to bot (text, media, files)
2. **Storage** - Messages stored in SQLite with metadata and timestamps
3. **Scheduling** - APScheduler runs at configured intervals
4. **Delivery** - Stored messages posted to private channel
5. **Cleanup** - Sent messages archived, old data purged automatically

## 🚢 Deployment

**Development:**
```bash
python main.py
```

**Production (Linux):**
```bash
nohup python main.py > bot.log 2>&1 &
```

**Systemd service:**
```ini
[Unit]
Description=Telegram Scheduler Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/path/to/bot
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📈 Monitoring

- **Real-time logs** - Structured logging with timestamps and levels
- **Database metrics** - Storage size, message counts, cleanup status
- **Health checks** - Built-in status commands and error reporting
- **Performance tracking** - Message processing times and scheduler reliability

## �️ Requirements

- Python 3.8+
- SQLite3
- Internet connection for Telegram API

## � License

MIT License - see LICENSE file for details.
