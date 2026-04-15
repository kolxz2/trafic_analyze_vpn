import csv
import io
from sqlalchemy.orm import Session
from models import Traffic

def generate_csv_report(db: Session) -> str:
    """
    Генерирует CSV-строку из всех записей в таблице traffic.
    """
    traffic_data = db.query(Traffic).order_by(Traffic.count.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow(["domain", "count", "emails", "last_seen"])
    
    # Данные
    for entry in traffic_data:
        writer.writerow([
            entry.domain, 
            entry.count, 
            entry.emails or "", 
            entry.last_seen.strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    return output.getvalue()
