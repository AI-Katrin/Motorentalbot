#!/bin/bash

# Конфигурация путей
PROJECT_DIR="/root/Motorentalbot"
VENV_BIN="$PROJECT_DIR/venv/bin"

BOT_MODULE="bot.main"
API_MODULE="miniapp.app:app"

BOT_LOG="$PROJECT_DIR/logs/bot.log"
API_LOG="$PROJECT_DIR/logs/api.log"

# Создание папки logs, если не существует
mkdir -p "$PROJECT_DIR/logs"

# Переход в корень проекта
cd "$PROJECT_DIR" || exit 1

# Запуск Telegram-бота
echo "Запуск Telegram-бота..."
nohup "$VENV_BIN/python3" -m "$BOT_MODULE" > "$BOT_LOG" 2>&1 &

# Запуск FastAPI backend с указанием PYTHONPATH
echo "Запуск FastAPI backend..."
nohup env PYTHONPATH=. "$VENV_BIN/python3" -m uvicorn "$API_MODULE" --host 0.0.0.0 --port 8000 > "$API_LOG" 2>&1 &

echo "Скрипт выполнен. Логи:"
echo "Бот: $BOT_LOG"
echo "API: $API_LOG"
