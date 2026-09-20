import json
import re
import requests
import feedparser
from bs4 import BeautifulSoup

# ==========================================
# 1. СПИСОК БЕСПЛАТНЫХ TELEGRAM-КАНАЛОВ
# Сюда стекаются прямые заказы от клиентов
# ==========================================
TG_CHANNELS = [
    "freelancetavern",     # Таверна фриланса (много ботов и сайтов)
    "digitaltender",       # Тендеры и задачи
    "freelance_zakazy",    # Заказы фриланса
    "forfreelance",        # Биржа задач
    "it_freelance_zakaz",  # IT заказы
    "zakazy_it",           # Проекты и подработка
    "py_jobs"              # Заказы по Python и ботам
]

# ==========================================
# 2. ФИЛЬТРЫ (ТОЛЬКО ТВОЙ СТЕК)
# ==========================================
TARGET_KEYWORDS = [
    # Telegram
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бота",
    "mini app", "мини апп", "tma", "webapp", "web app",
    # Веб и верстка
    "верстка", "сверстать", "html", "css", "landing", "лендинг", 
    "сайт визитка", "простой сайт", "статический сайт", "поправить верстку"
]

STOP_WORDS = [
    "1с", "1c", "bitrix", "битрикс", "wordpress",
    "senior", "lead", "teamlead", "мидл", "middle",
    "flutter", "react native", "swift", "kotlin", "ios", "android",
    "c#", "c++", ".net", "java", "golang", "rust", "php"
]

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_matching(text: str) -> bool:
    text_lower = text.lower()
    for stop in STOP_WORDS:
        if re.search(r"\b" + re.escape(stop) + r"\b", text_lower):
            return False
    return any(k in text_lower for k in TARGET_KEYWORDS)

# ==========================================
# 3. СБОР ИЗ TELEGRAM (БЕСПЛАТНО, БЕЗ ПАСПОРТА)
# ==========================================
def parse_tg(channel: str):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        messages = soup.select(".tgme_widget_message")
        
        for msg in messages[-15:]:
            text_el = msg.select_one(".tgme_widget_message_text")
            date_el = msg.select_one(".tgme_widget_message_date")
            if not text_el or not date_el:
                continue
                
            text = text_el.text.strip()
            link = date_el.get("href")
            
            if is_matching(text):
                first_line = clean_text(text.split("\n")[0])
                title = (first_line[:90] + "...") if len(first_line) > 90 else first_line
                
                # Ищем контакт (@username) прямо в тексте
                usernames = re.findall(r"@[a-zA-Z0-9_]{5,}", text)
                direct_contact = usernames[0] if usernames else f"@{channel}"
                
                tasks.append({
                    "title": title,
                    "price": "В описании",
                    "url": link,
                    "category": "Telegram" if any(k in text.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт",
                    "source": f"TG ({direct_contact})"
                })
    except Exception as e:
        print(f"Ошибка @{channel}: {e}")
    return tasks

# ==========================================
# 4. СБОР С ХАБРА (5 БЕСПЛАТНЫХ ОТКЛИКОВ В ДЕНЬ)
# ==========================================
def parse_habr():
    tasks = []
    try:
        feed = feedparser.parse("https://freelance.habr.com/tasks.rss", agent="Mozilla/5.0")
        for entry in feed.entries[:25]:
            title = clean_text(entry.get("title", ""))
            summary = clean_text(entry.get("summary", ""))
            link = entry.get("link", "")
            full = f"{title} {summary}"
            
            if is_matching(full):
                cat = "Telegram" if any(k in full.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"
                tasks.append({
                    "title": title[:95],
                    "price": "Бесплатный отклик",
                    "url": link,
                    "category": cat,
                    "source": "Хабр Фриланс"
                })
    except Exception as e:
        print(f"Ошибка Хабра: {e}")
    return tasks

if __name__ == "__main__":
    orders = []
    
    # 1. Собираем Telegram-каналы (основной поток прямых заказов)
    for ch in TG_CHANNELS:
        orders.extend(parse_tg(ch))
        
    # 2. Собираем Хабр Фриланс
    orders.extend(parse_habr())
    
    # 3. Убираем дубликаты
    unique = []
    seen = set()
    for o in orders:
        if o["url"] not in seen:
            seen.add(o["url"])
            unique.append(o)
            
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
        
    print(f"Готово! Найдено {len(unique)} бесплатных заказов.")
