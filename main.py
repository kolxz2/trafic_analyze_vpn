import os
import asyncio
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, Response, FileResponse
from collections import defaultdict

from log_reader import read_new_logs

app = FastAPI(title="Xray Traffic Analyzer Pro", description="Анализ логов и управление списками (No-DB version)")

CSV_LOG_FILE = "logs.csv"

# Фоновая задача чтения логов
@app.on_event("startup")
async def startup_event():
    # Создаем файлы списков если их нет
    for f in ["direct.txt", "proxy.txt"]:
        if not os.path.exists(f):
            with open(f, "w") as file: pass
    
    asyncio.create_task(background_log_reader())

async def background_log_reader():
    while True:
        try:
            read_new_logs()
        except Exception as e:
            print(f"Error reading logs: {e}")
        await asyncio.sleep(60)

# --- Управление списками (Файловая реализация) ---

def load_list(list_type: str) -> Set[str]:
    filename = f"{list_type}.txt"
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_list(list_type: str, domains: Set[str]):
    with open(f"{list_type}.txt", "w", encoding="utf-8") as f:
        for d in sorted(list(domains)):
            f.write(f"{d}\n")

@app.get("/lists")
def get_lists():
    return {
        "direct": list(load_list("direct")),
        "proxy": list(load_list("proxy"))
    }

@app.post("/lists")
async def add_to_list(domain: str, list_type: str):
    if list_type not in ["direct", "proxy"]:
        raise HTTPException(status_code=400, detail="Invalid list type")
    
    direct = load_list("direct")
    proxy = load_list("proxy")

    # Удаляем из обоих на всякий случай
    if domain in direct: direct.remove(domain)
    if domain in proxy: proxy.remove(domain)

    # Добавляем в нужный
    if list_type == "direct":
        direct.add(domain)
    else:
        proxy.add(domain)

    save_list("direct", direct)
    save_list("proxy", proxy)
    return {"status": "success"}

@app.delete("/lists/{domain}")
async def remove_from_list(domain: str):
    direct = load_list("direct")
    proxy = load_list("proxy")

    if domain in direct: direct.remove(domain)
    if domain in proxy: proxy.remove(domain)

    save_list("direct", direct)
    save_list("proxy", proxy)
    return {"status": "success"}

# --- Статистика (Агрегация из CSV) ---

@app.get("/stats")
def get_stats(
    only_new: bool = False, 
    sort_by: str = "count", 
    limit: int = 100
):
    """
    Получение статистики по доменам из CSV.
    sort_by: 'count' (запросы) или 'users' (кол-во уникальных email)
    """
    direct = load_list("direct")
    proxy = load_list("proxy")
    distributed_domains = direct.union(proxy)

    if not os.path.exists(CSV_LOG_FILE):
        return []

    # domain -> {count, users: set, last_seen}
    stats = defaultdict(lambda: {"count": 0, "users": set(), "last_seen": datetime.min})

    with open(CSV_LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row["domain"]
            
            if only_new and domain in distributed_domains:
                continue

            try:
                ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            except:
                continue
            
            email = row.get("email", "system")
            
            stats[domain]["count"] += 1
            stats[domain]["users"].add(email)
            if ts > stats[domain]["last_seen"]:
                stats[domain]["last_seen"] = ts

    # Подготовка результатов
    results = []
    for domain, data in stats.items():
        status = "new"
        if domain in direct: status = "direct"
        elif domain in proxy: status = "proxy"

        results.append({
            "domain": domain,
            "count": data["count"],
            "user_count": len(data["users"]),
            "last_seen": data["last_seen"].strftime("%Y-%m-%d %H:%M:%S"),
            "status": status
        })

    # Сортировка
    if sort_by == "users":
        results.sort(key=lambda x: x["user_count"], reverse=True)
    else:
        results.sort(key=lambda x: x["count"], reverse=True)

    return results[:limit]

# --- Загрузки ---

@app.get("/download/{filename}")
async def download_file(filename: str):
    allowed = ["logs.csv", "direct.txt", "proxy.txt"]
    if filename not in allowed:
        raise HTTPException(status_code=404)
    
    if not os.path.exists(filename):
        with open(filename, "w") as f: pass
        
    return FileResponse(filename, filename=filename)

@app.get("/", response_class=HTMLResponse)
async def index():
    if not os.path.exists("index.html"):
        return HTMLResponse("<h1>Index file not found</h1>", status_code=404)
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
