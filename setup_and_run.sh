#!/bin/bash
# chmod +x setup_and_run.sh
# ./setup_and_run.sh
# Путь к папке проекта
PROJECT_DIR="/home/trafic_analyze_vpn"
cd $PROJECT_DIR

# 1. Создание venv если его нет
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# 2. Активация и установка зависимостей
echo "Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Убиваем старый процесс если он запущен
echo "Перезапуск сервера..."
pkill -f "main.py" || true

# 4. Запуск через nohup
nohup venv/bin/python main.py > output.log 2>&1 &

echo "------------------------------------------"
echo "Сервер запущен в фоне!"
echo "Логи можно смотреть командой: tail -f output.log"
echo "------------------------------------------"
