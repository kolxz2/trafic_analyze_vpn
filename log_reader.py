import os
import time
from parser import parse_log_line, prune_old_data

LOG_FILE_PATH = "/usr/local/x-ui/access.log"
STATE_FILE = "last_pos.txt"

def get_last_position():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0

def save_last_position(pos):
    with open(STATE_FILE, "w") as f:
        f.write(str(pos))

def read_new_logs():
    """
    Читает новые строки из лог-файла.
    """
    if not os.path.exists(LOG_FILE_PATH):
        # Если файла нет, возвращаем управление
        return

    last_pos = get_last_position()
    file_size = os.path.getsize(LOG_FILE_PATH)

    if file_size < last_pos:
        # Лог был ротирован или очищен
        last_pos = 0

    if file_size == last_pos:
        return

    try:
        # Удаляем старые логи из CSV
        prune_old_data()

        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(last_pos)
            for line in f:
                if line.strip():
                    parse_log_line(line)
            
            save_last_position(f.tell())
    except Exception as e:
        print(f"Error reading logs: {e}")
