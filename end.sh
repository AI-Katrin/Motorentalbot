#!/bin/bash

pkill -f "uvicorn miniapp.main:app"
pkill -f "bot/main.py"

echo "Все процессы остановлены."
