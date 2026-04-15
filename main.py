"""
API Endpoints:
- GET /              : Главная страница (интерфейс)
- GET /stats         : Получение статистики по доменам (с фильтрацией и сортировкой)
- GET /lists         : Получение списков direct и proxy
- POST /lists        : Добавление домена в список (direct или proxy)
- DELETE /lists/{d}  : Удаление домена из списков
- GET /download/{f}  : Скачивание файлов (logs.csv, direct.txt, proxy.txt)
"""
import os
import asyncio
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, Response, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

import db
import models
import parser
import report
from log_reader import read_new_logs

app = FastAPI(title="Xray Traffic Analyzer Pro", description="Анализ логов и управление списками")

# Инициализация БД при запуске
@app.on_event("startup")
async def startup_event():
    db.init_db()
    # Фоновая задача чтения логов
    asyncio.create_task(background_log_reader())

async def background_log_reader():
    while True:
        try:
            read_new_logs()
        except Exception as e:
            print(f"Error reading logs: {e}")
        await asyncio.sleep(60)

# --- Управление списками ---

def sync_lists_to_files(database: Session):
    """Синхронизирует БД с текстовыми файлами."""
    for list_type in ["direct", "proxy"]:
        domains = database.query(models.DomainList).filter(models.DomainList.list_type == list_type).all()
        with open(f"{list_type}.txt", "w", encoding="utf-8") as f:
            for d in domains:
                f.write(f"{d.domain}\n")

@app.get("/lists")
def get_lists(database: Session = Depends(db.get_db)):
    direct = database.query(models.DomainList).filter(models.DomainList.list_type == "direct").all()
    proxy = database.query(models.DomainList).filter(models.DomainList.list_type == "proxy").all()
    return {
        "direct": [d.domain for d in direct],
        "proxy": [d.domain for d in proxy]
    }

@app.post("/lists")
async def add_to_list(domain: str, list_type: str, database: Session = Depends(db.get_db)):
    if list_type not in ["direct", "proxy"]:
        raise HTTPException(status_code=400, detail="Invalid list type")
    
    # Удаляем из другого списка если есть
    database.query(models.DomainList).filter(models.DomainList.domain == domain).delete()
    
    new_item = models.DomainList(domain=domain, list_type=list_type)
    database.add(new_item)
    database.commit()
    sync_lists_to_files(database)
    return {"status": "success"}

@app.delete("/lists/{domain}")
async def remove_from_list(domain: str, database: Session = Depends(db.get_db)):
    database.query(models.DomainList).filter(models.DomainList.domain == domain).delete()
    database.commit()
    sync_lists_to_files(database)
    return {"status": "success"}

# --- Статистика ---

@app.get("/stats")
def get_stats(
    only_new: bool = False, 
    sort_by: str = "count", 
    limit: int = 100, 
    database: Session = Depends(db.get_db)
):
    """
    Получение статистики по доменам.
    sort_by: 'count' (запросы) или 'users' (кол-во уникальных email)
    """
    # Список уже распределенных доменов
    distributed = database.query(models.DomainList.domain).all()
    distributed_domains = [d[0] for d in distributed]

    query = database.query(
        models.LogEntry.domain,
        func.count(models.LogEntry.id).label("total_count"),
        func.count(distinct(models.LogEntry.email)).label("user_count"),
        func.max(models.LogEntry.timestamp).label("last_seen")
    ).group_by(models.LogEntry.domain)

    if only_new:
        query = query.filter(models.LogEntry.domain.notin_(distributed_domains))

    if sort_by == "users":
        query = query.order_by(func.count(distinct(models.LogEntry.email)).desc())
    else:
        query = query.order_by(func.count(models.LogEntry.id).desc())

    results = query.limit(limit).all()

    return [
        {
            "domain": r[0],
            "count": r[1],
            "user_count": r[2],
            "last_seen": r[3],
            "status": "new" if r[0] not in distributed_domains else ("direct" if r[0] in [d.domain for d in database.query(models.DomainList).filter(models.DomainList.list_type=="direct").all()] else "proxy")
        } for r in results
    ]

# --- Загрузки ---

@app.get("/download/{filename}")
async def download_file(filename: str):
    allowed = ["logs.csv", "direct.txt", "proxy.txt"]
    if filename not in allowed:
        raise HTTPException(status_code=404)
    
    if not os.path.exists(filename):
        # Создаем пустой файл если его нет
        with open(filename, "w") as f: pass
        
    return FileResponse(filename, filename=filename)

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
