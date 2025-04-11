#!/bin/bash

PROJECT_DIR="/root/motorentalbot/Motorentalbot"
VENV_PATH="$PROJECT_DIR/venv/bin/activate"

BOT_PATH="$PROJECT_DIR/bot/main.py"
API_PATH="$PROJECT_DIR/miniapp/app.py"

BOT_LOG="$PROJECT_DIR/logs/bot.log"
API_LOG="$PROJECT_DIR/logs/api.log"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR" || exit 1
source "$VENV_PATH"

echo "Запуск бота..."
nohup python3 "$BOT_PATH" > "$BOT_LOG" 2>&1 &
echo "Бот запущен. Лог: $BOT_LOG"

echo "Запуск FastAPI backend..."
nohup uvicorn miniapp.main:app --host 0.0.0.0 --port 8000 > "$API_LOG" 2>&1 &
echo "Backend запущен. Лог: $API_LOG"