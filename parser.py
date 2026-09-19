import json
import re
import requests
import feedparser
from bs4 import BeautifulSoup

# ==========================================
# 1. СПИСОК TELEGRAM-КАНАЛОВ
# ==========================================
TG_CHANNELS = [
    "freelancetavern",
    "digitaltender",
    "freelance_zakazy",
    "forfreelance",
    "zakazy_it",
    "freelance_rabota_rf"
]

# ==========================================
# 2. ФИЛЬТРЫ ЗАКАЗОВ
# ==========================================
TARGET_KEYWORDS = [
    # Telegram боты и Mini Apps
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бот для тг", "бота",
    "mini app", "мини апп", "tma", "webapp", "web app", "бота для",
    
    # Сайты и фронтенд
    "верстка", "сверстать", "html", "css", "landing", "лендинг", 
    "сайт визитка", "простой сайт", "статический сайт", "правки на сайте",
    "доработать сайт", "поправить верстку", "одностраничник", "сайт под ключ"
]

STOP_WORDS = [
    "1с", "1c", "bitrix", "битрикс", "wordpress", "wp",
    "senior", "lead", "teamlead", "мидл", "middle",
    "flutter", "react native", "swift", "kotlin", "ios", "android",
    "c#", "c++", ".net", "java", "golang", "go", "rust", "php"
]

def clean_text(text: str) -> str:
    """Убирает лишние пробелы, теги и символы."""
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_matching_order(text: str) -> bool:
    """Проверяет соответствие ключевым словам."""
    text_lower = text.lower()
    
    for stop in STOP_WORDS:
        if re.search(r"\b" + re.escape(stop) + r"\b", text_lower):
            return False
            
    for target in TARGET_KEYWORDS:
        if target in text_lower:
            return True
            
    return False

# ==========================================
# 3. ИСТОЧНИКИ ДАННЫХ
# ==========================================

def parse_rss_feed(url: str, source_name: str):
    """Универсальный сборщик через открытые RSS-ленты (FL.ru, Freelance.ru, Habr)."""
    tasks = []
    try:
        # User-Agent нужен, чтобы лента отдала данные
        feed = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        
        for entry in feed.entries[:25]:
            title = clean_text(entry.get("title", ""))
            summary = clean_text(entry.get("summary", ""))
            link = entry.get("link", "")
            
            # Проверяем и заголовок, и краткое описание
            full_check_text = f"{title} {summary}"
            
            if is_matching_order(full_check_text):
                cat = "Telegram" if any(k in full_check_text.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"
                tasks.append({
                    "title": title[:100],
                    "price": "Смотреть на бирже",
                    "url": link,
                    "category": cat,
                    "source": source_name
                })
    except Exception as e:
        print(f"[!] Ошибка RSS {source_name}: {e}")
        
    return tasks

def parse_tg_channel(channel_username: str):
    """Сбор постов из веб-версий Telegram-каналов."""
    username = channel_username.replace("@", "").strip()
    url = f"https://t.me/s/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        messages = soup.select(".tgme_widget_message")
        
        for msg in messages[-15:]:
            text_elem = msg.select_one(".tgme_widget_message_text")
            link_elem = msg.select_one(".tgme_widget_message_date")
            
            if not text_elem or not link_elem:
                continue
                
            full_text = text_elem.text.strip()
            link = link_elem.get("href")
            
            if is_matching_order(full_text):
                first_line = clean_text(full_text.split("\n")[0])
                title = (first_line[:90] + "...") if len(first_line) > 90 else first_line
                
                tasks.append({
                    "title": title,
                    "price": "В канале",
                    "url": link,
                    "category": "Telegram",
                    "source": f"@{username}"
                })
    except Exception as e:
        print(f"[!] Ошибка канала @{username}: {e}")
        
    return tasks

# ==========================================
# 4. ЗАПУСК
# ==========================================

if __name__ == "__main__":
    all_orders = []

    # 1. Биржи через стабильные RSS-ленты
    print("Собираем RSS FL.ru...")
    all_orders.extend(parse_rss_feed("https://www.fl.ru/rss/all.xml?category=5", "FL.ru"))

    print("Собираем RSS Freelance.ru...")
    all_orders.extend(parse_rss_feed("https://freelance.ru/rss/index", "Freelance.ru"))

    print("Собираем RSS Habr Freelance...")
    all_orders.extend(parse_rss_feed("https://freelance.habr.com/tasks.rss", "Habr"))

    # 2. Telegram-каналы
    for ch in TG_CHANNELS:
        print(f"Проверяем Telegram @{ch}...")
        all_orders.extend(parse_tg_channel(ch))

    # 3. Удаление дубликатов по URL
    unique_orders = []
    seen_urls = set()
    for o in all_orders:
        if o["url"] not in seen_urls:
            seen_urls.add(o["url"])
            unique_orders.append(o)

    # 4. Сохранение
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(unique_orders, f, ensure_ascii=False, indent=2)

    print(f"\nУспешно! Найдено уникальных заказов: {len(unique_orders)}")
