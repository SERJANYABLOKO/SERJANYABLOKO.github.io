import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

TG_CHANNELS = [
    "freelancetavern",
    "digitaltender",
    "freelance_zakazy",
    "forfreelance",
    "it_freelance_zakaz",
    "zakazy_it",
    "py_jobs"
]

TARGET_KEYWORDS = [
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бота",
    "mini app", "мини апп", "tma", "webapp", "web app",
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

def parse_habr():
    """Собирает заказы с Хабра вместе со временем и числом откликов."""
    url = "https://freelance.habr.com/tasks"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select(".task-card")
        
        for card in cards:
            title_el = card.select_one(".task-card__title a")
            if not title_el:
                continue
                
            title = clean_text(title_el.text)
            if not is_matching(title):
                continue
                
            link = "https://freelance.habr.com" + title_el.get("href", "")
            
            # Бюджет
            price_el = card.select_one(".task-card__price")
            price = clean_text(price_el.text) if price_el else "Договорная"
            
            # Количество откликов (на Хабре лежит в блоке параметров задания)
            responses_el = card.select_one(".task-params__item_responses")
            if responses_el:
                responses_count = clean_text(responses_el.text)
            else:
                responses_count = "0 откликов"
                
            # Время публикации
            date_el = card.select_one(".task-params__item_published")
            published_at = clean_text(date_el.text) if date_el else "Сегодня"

            cat = "Telegram" if any(k in title.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"

            tasks.append({
                "title": title,
                "price": price,
                "url": link,
                "category": cat,
                "source": "Хабр Фриланс",
                "published_at": published_at,
                "responses": responses_count,
                "direct_contact": None
            })
    except Exception as e:
        print(f"[!] Ошибка парсинга Хабра: {e}")
        
    return tasks

def parse_tg(channel: str):
    """Собирает посты из публичной веб-ленты Telegram-канала."""
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        messages = soup.select(".tgme_widget_message")
        
        for msg in messages[-15:]:
            text_el = msg.select_one(".tgme_widget_message_text")
            date_el = msg.select_one(".tgme_widget_message_date time")
            link_el = msg.select_one(".tgme_widget_message_date")
            
            if not text_el or not link_el:
                continue
                
            text = text_el.text.strip()
            if not is_matching(text):
                continue
                
            first_line = clean_text(text.split("\n")[0])
            title = (first_line[:90] + "...") if len(first_line) > 90 else first_line
            link = link_el.get("href")
            
            # Время поста из атрибута datetime: "2026-09-20T08:45:00+00:00"
            published_at = "Недавно"
            if date_el and date_el.get("datetime"):
                raw_time = date_el.get("datetime")
                try:
                    dt = datetime.fromisoformat(raw_time)
                    published_at = dt.strftime("%d.%m %H:%M")
                except Exception:
                    published_at = raw_time[:10]

            # Ищем @username в тексте поста
            direct_contact = None
            found_usernames = re.findall(r"@[a-zA-Z0-9_]{5,}", text)
            if found_usernames:
                direct_contact = found_usernames[0]

            cat = "Telegram" if any(k in text.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"

            tasks.append({
                "title": title,
                "price": "В описании",
                "url": link,
                "category": cat,
                "source": f"@{channel}",
                "published_at": published_at,
                "responses": "В личке", # В ТГ нет счетчика откликов
                "direct_contact": direct_contact
            })
    except Exception as e:
        print(f"[!] Ошибка канала @{channel}: {e}")
        
    return tasks

if __name__ == "__main__":
    all_orders = []
    
    # 1. Telegram
    for ch in TG_CHANNELS:
        all_orders.extend(parse_tg(ch))
        
    # 2. Хабр
    all_orders.extend(parse_habr())
    
    # 3. Дедупликация
    seen_urls = set()
    unique_orders = []
    for o in all_orders:
        if o["url"] not in seen_urls:
            seen_urls.add(o["url"])
            unique_orders.append(o)
            
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(unique_orders, f, ensure_ascii=False, indent=2)
        
    print(f"Готово! Сохранено заказов: {len(unique_orders)}")
