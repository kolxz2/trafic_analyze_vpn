import socket
import functools
import dns.resolver
import dns.reversename

# Настройка резолвера с DNS Яндекса
yandex_resolver = dns.resolver.Resolver()
yandex_resolver.nameservers = ['77.88.8.8', '77.88.8.1']
yandex_resolver.timeout = 2.0
yandex_resolver.lifetime = 2.0

@functools.lru_cache(maxsize=1024)
def resolve_ip(ip: str) -> str:
    """
    Выполняет reverse DNS для IP-адреса через Яндекс DNS.
    Использует кэширование, чтобы не спамить DNS-сервер.
    """
    try:
        # Пытаемся получить имя через PTR запись
        addr = dns.reversename.from_address(ip)
        answer = yandex_resolver.resolve(addr, "PTR")
        if answer:
            return str(answer[0]).rstrip('.')
        return ip
    except Exception:
        # Если не удалось через dnspython, пробуем системный
        try:
            name, alias, addresslist = socket.gethostbyaddr(ip)
            return name
        except:
            return ip
