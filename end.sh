#!/bin/bash

pkill -f "uvicorn miniapp.app:app"
pkill -f "bot/main.py"

echo "Все процессы остановлены."
