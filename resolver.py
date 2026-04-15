import socket
import functools

@functools.lru_cache(maxsize=1024)
def resolve_ip(ip: str) -> str:
    """
    Выполняет reverse DNS для IP-адреса.
    Использует кэширование, чтобы не спамить DNS-сервер.
    """
    try:
        # Пытаемся получить имя хоста
        name, alias, addresslist = socket.gethostbyaddr(ip)
        return name
    except (socket.herror, socket.gaierror, Exception):
        # Если не удалось, возвращаем IP как есть
        return ip
