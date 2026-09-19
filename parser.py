import json
import re
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. СПИСОК ПУБЛИЧНЫХ ТЕЛЕГРАМ-КАНАЛОВ
# Вставляй сюда юзернеймы БЕЗ символа '@'
# Например: если ссылка https://t.me/freelance_orders, пиши "freelance_orders"
# ==========================================
TG_CHANNELS = [
    "freelancetavern",
    "digitaltender",
    "freelance_zakazy"
]
]

# ==========================================
# 2. ФИЛЬТРЫ ЗАКАЗОВ
# ==========================================

# Белый список: ищем только твои направления
TARGET_KEYWORDS = [
    # Telegram боты и Mini Apps
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бот для тг",
    "mini app", "мини апп", "tma", "webapp", "web app", "бота",
    
    # Сайты и фронтенд
    "верстка", "сверстать", "html", "css", "landing", "лендинг", 
    "сайт визитка", "простой сайт", "статический сайт", "правки на сайте",
    "доработать сайт", "поправить верстку"
]

# Стоп-слова: отсекаем сложные/неподходящие технологии
STOP_WORDS = [
    "1с", "1c", "bitrix", "битрикс", "wordpress", "wp",
    "senior", "lead", "teamlead", "мидл", "middle",
    "flutter", "react native", "swift", "kotlin", "ios", "android",
    "c#", "c++", ".net", "java", "golang", "go", "rust", "php"
]

def clean_text(text: str) -> str:
    """Убирает лишние пробелы и переносы строк."""
    return re.sub(r"\s+", " ", text).strip()

def is_matching_order(text: str) -> bool:
    """Проверяет, подходит ли задача под твои критерии."""
    text_lower = text.lower()
    
    # 1. Если найдено хоть одно стоп-слово — отклоняем
    for stop in STOP_WORDS:
        # Граница слова, чтобы случайно не зацепить похожие фразы
        if re.search(r"\b" + re.escape(stop) + r"\b", text_lower):
            return False
            
    # 2. Если есть совпадение по целевым словам — пропускаем
    for target in TARGET_KEYWORDS:
        if target in text_lower:
            return True
            
    return False

# ==========================================
# 3. ФУНКЦИИ ПАРСИНГА
# ==========================================

def parse_habr():
    """Сбор задач с Habr Freelance."""
    url = "https://freelance.habr.com/tasks"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select(".task-card")
        
        for card in cards:
            title_elem = card.select_one(".task-card__title a")
            price_elem = card.select_one(".task-card__price")
            
            if not title_elem:
                continue
                
            title = clean_text(title_elem.text)
            link = "https://freelance.habr.com" + title_elem["href"]
            price = clean_text(price_elem.text) if price_elem else "Договорная"
            
            if is_matching_order(title):
                category = "Telegram" if any(k in title.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"
                tasks.append({
                    "title": title,
                    "price": price,
                    "url": link,
                    "category": category,
                    "source": "Habr"
                })
    except Exception as e:
        print(f"[!] Ошибка при парсинге Habr: {e}")
        
    return tasks

def parse_tg_channel(channel_username: str):
    """Сбор постов из открытых Telegram-каналов через веб-интерфейс."""
    username = channel_username.replace("@", "").strip()
    url = f"https://t.me/s/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        messages = soup.select(".tgme_widget_message")
        
        for msg in messages[-12:]:  # Проверяем последние 12 сообщений канала
            text_elem = msg.select_one(".tgme_widget_message_text")
            link_elem = msg.select_one(".tgme_widget_message_date")
            
            if not text_elem or not link_elem:
                continue
                
            full_text = text_elem.text.strip()
            link = link_elem.get("href")
            
            if is_matching_order(full_text):
                # Берем первую строчку сообщения в качестве заголовка
                first_line = clean_text(full_text.split("\n")[0])
                title = (first_line[:85] + "...") if len(first_line) > 85 else first_line
                
                tasks.append({
                    "title": title,
                    "price": "В описании",
                    "url": link,
                    "category": "Telegram",
                    "source": f"@{username}"
                })
    except Exception as e:
        print(f"[!] Ошибка парсинга канала @{username}: {e}")
        
    return tasks

# ==========================================
# 4. ЗАПУСК И СОХРАНЕНИЕ
# ==========================================

if __name__ == "__main__":
    all_orders = []
    
    # Собираем с биржи
    print("Собираю заказы с Хабра...")
    all_orders.extend(parse_habr())
    
    # Собираем с Telegram-каналов
    for ch in TG_CHANNELS:
        print(f"Проверяю канал @{ch}...")
        all_orders.extend(parse_tg_channel(ch))
        
    # Сохраняем в файл orders.json для сайта
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(all_orders, f, ensure_ascii=False, indent=2)
        
    print(f"\nГотово! Всего найдено подходящих заказов: {len(all_orders)}")
