import re
import csv
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import LogEntry
from resolver import resolve_ip

# Регулярные выражения
PATTERN_TCP = re.compile(r"tcp:([a-zA-Z0-9\-\.\:]+):(\d+)")
PATTERN_IP = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
PATTERN_EMAIL = re.compile(r"email: (\S+)")

CSV_LOG_FILE = "logs.csv"

def parse_log_line(line: str, db: Session, save_to_csv=True):
    """
    Парсит одну строку лога и сохраняет в БД и CSV.
    """
    match_tcp = PATTERN_TCP.search(line)
    if not match_tcp:
        return

    address = match_tcp.group(1)
    
    # Извлечем email
    match_email = PATTERN_EMAIL.search(line)
    email = match_email.group(1) if match_email else "system"

    # Резолвим IP если нужно
    if PATTERN_IP.match(address):
        domain = resolve_ip(address)
    else:
        domain = address

    now = datetime.now()
    
    # 1. Сохраняем в БД
    new_entry = LogEntry(timestamp=now, domain=domain, email=email)
    db.add(new_entry)
    db.commit()

    # 2. Сохраняем в CSV
    if save_to_csv:
        write_to_csv(now, domain, email)

def write_to_csv(timestamp, domain, email):
    file_exists = os.path.isfile(CSV_LOG_FILE)
    with open(CSV_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "domain", "email"])
        writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), domain, email])

def prune_old_data(db: Session):
    """
    Удаляет данные старше 3 месяцев из БД и CSV.
    """
    three_months_ago = datetime.now() - timedelta(days=90)
    
    # Удаляем из БД
    db.query(LogEntry).filter(LogEntry.timestamp < three_months_ago).delete()
    db.commit()
    
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

def process_log_file(content: str, db: Session):
    lines = content.splitlines()
    for line in lines:
        if line.strip():
            parse_log_line(line, db)
