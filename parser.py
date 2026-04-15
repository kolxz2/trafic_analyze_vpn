import re
import csv
import os
from datetime import datetime, timedelta
from resolver import resolve_ip

# Регулярные выражения
PATTERN_TCP = re.compile(r"tcp:([a-zA-Z0-9\-\.\:]+):(\d+)")
PATTERN_IP = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
PATTERN_EMAIL = re.compile(r"email: (\S+)")

CSV_LOG_FILE = "logs.csv"

def parse_log_line(line: str, save_to_csv=True):
    """
    Парсит одну строку лога и сохраняет в CSV.
    """
    match_tcp = PATTERN_TCP.search(line)
    if not match_tcp:
        return

    address = match_tcp.group(1)
    
    # Извлечем email
    match_email = PATTERN_EMAIL.search(line)
    email = match_email.group(1) if match_email else "system"

    # Резолвим IP если нужно
    orig_ip = ""
    if PATTERN_IP.match(address):
        orig_ip = address
        domain = resolve_ip(address)
    else:
        domain = address

    now = datetime.now()
    
    # Сохраняем в CSV
    if save_to_csv:
        write_to_csv(now, domain, email, orig_ip)

def write_to_csv(timestamp, domain, email, ip):
    file_exists = os.path.isfile(CSV_LOG_FILE)
    with open(CSV_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "domain", "email", "ip"])
        writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), domain, email, ip])

def prune_old_data():
    """
    Удаляет данные старше 3 месяцев из CSV.
    """
    three_months_ago = datetime.now() - timedelta(days=90)
    
    # Очистка CSV
    if os.path.exists(CSV_LOG_FILE):
        temp_file = CSV_LOG_FILE + ".tmp"
        try:
            with open(CSV_LOG_FILE, "r", encoding="utf-8") as f, open(temp_file, "w", newline="", encoding="utf-8") as out:
                reader = csv.reader(f)
                writer = csv.writer(out)
                headers = next(reader, None)
                if headers:
                    writer.writerow(headers)
                for row in reader:
                    try:
                        row_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                        if row_time >= three_months_ago:
                            writer.writerow(row)
                    except:
                        continue
            os.replace(temp_file, CSV_LOG_FILE)
        except Exception as e:
            print(f"Error pruning CSV: {e}")

def process_log_file(content: str):
    lines = content.splitlines()
    for line in lines:
        if line.strip():
            parse_log_line(line)
