#!/bin/bash

PROJECT_DIR="/root/Motorentalbot"
VENV_BIN="$PROJECT_DIR/venv/bin"

BOT_MODULE="bot.main"
API_MODULE="miniapp.app:app"

BOT_LOG="$PROJECT_DIR/logs/bot.log"
API_LOG="$PROJECT_DIR/logs/api.log"

mkdir -p "$PROJECT_DIR/logs"

cd "$PROJECT_DIR" || exit 1

echo "Запуск Telegram-бота..."
nohup "$VENV_BIN/python3" -m "$BOT_MODULE" > "$BOT_LOG" 2>&1 &

echo "Запуск FastAPI backend..."
nohup env PYTHONPATH="$PROJECT_DIR" "$VENV_BIN/python3" -m uvicorn "$API_MODULE" --host 0.0.0.0 --port 8000 > "$API_LOG" 2>&1 &

echo "Скрипт выполнен. Логи:"
echo "Бот: $BOT_LOG"
echo "API: $API_LOG"
