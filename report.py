import csv
import io
import os
from datetime import datetime
from collections import defaultdict

CSV_LOG_FILE = "logs.csv"

def generate_csv_report() -> str:
    """
    Генерирует CSV-строку из всех записей (группировка по доменам) на основе logs.csv.
    """
    if not os.path.exists(CSV_LOG_FILE):
        return "domain,count,last_seen\n"

    stats = defaultdict(lambda: {"count": 0, "last_seen": datetime.min})

    with open(CSV_LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row["domain"]
            try:
                ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            except:
                continue
            
            stats[domain]["count"] += 1
            if ts > stats[domain]["last_seen"]:
                stats[domain]["last_seen"] = ts
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow(["domain", "count", "last_seen"])
    
    # Сортировка по количеству
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True)

    # Данные
    for domain, data in sorted_stats:
        writer.writerow([
            domain, 
            data["count"], 
            data["last_seen"].strftime("%Y-%m-%d %H:%M:%S") if data["last_seen"] != datetime.min else "N/A"
        ])
    
    return output.getvalue()
