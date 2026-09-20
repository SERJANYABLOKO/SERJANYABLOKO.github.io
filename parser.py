import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. ТЕЛЕГРАМ-КАНАЛЫ С ПРЯМОЙ СВЯЗЬЮ
# ==========================================
TG_CHANNELS = [
    "job_python",
    "py_jobs",
    "aiogram_jobs",
    "python_rabota",
    "freelancetavern",
    "digitaltender",
    "forfreelance",
    "it_freelance_zakaz",
    "zakazy_it",
    "work_in_it",
    "freelance_rabota_rf",
    "it_podrabotka",
    "web_zakazy"
]

# ==========================================
# 2. ФИЛЬТРЫ ТЕХНОЛОГИЙ И СТОП-СЛОВА
# ==========================================
TARGET_KEYWORDS = [
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бота", "бота для",
    "написать бота", "дописать бота", "починить бота", "aiogram", "telethon",
    "mini app", "мини апп", "tma", "webapp", "web app",
    "верстка", "сверстать", "html", "css", "landing", "лендинг", 
    "сайт визитка", "простой сайт", "статический сайт", "поправить верстку",
    "написать скрипт", "сделать парсер", "парсер на python", "спарсить", "скрипт"
]

STOP_WORDS = [
    "kwork", "кворк", "fl.ru", "freelance.ru",
    "1с", "1c", "bitrix", "битрикс", "wordpress",
    "senior", "lead", "teamlead", "мидл", "middle",
    "flutter", "react native", "swift", "kotlin", "ios", "android",
    "c#", "c++", ".net", "java", "golang", "rust", "php"
]

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_matching_skills(text: str) -> bool:
    text_lower = text.lower()
    for stop in STOP_WORDS:
        if re.search(r"\b" + re.escape(stop) + r"\b", text_lower):
            return False
    return any(k in text_lower for k in TARGET_KEYWORDS)

def is_fresh_date(dt: datetime) -> bool:
    """Проверка даты: не старше 48 часов (172 800 секунд)."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() <= 48 * 3600

# ==========================================
# 3. СБОР С ХАБРА (СТРОГО <= 5 ОТКЛИКОВ)
# ==========================================
def parse_habr():
    url = "https://freelance.habr.com/tasks"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code != 200:
            return tasks
            
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select(".task-card")
        
        for card in cards:
            title_el = card.select_one(".task-card__title a")
            if not title_el:
                continue
                
            title = clean_text(title_el.text)
            if not is_matching_skills(title):
                continue
            
            # Не больше 5 откликов
            responses_el = card.select_one(".task-params__item_responses")
            responses_count = 0
            if responses_el:
                digits = re.findall(r"\d+", clean_text(responses_el.text))
                if digits:
                    responses_count = int(digits[0])
            
            if responses_count > 5:
                continue

            # Только свежие (сегодня/вчера)
            date_el = card.select_one(".task-params__item_published")
            published_text = clean_text(date_el.text).lower() if date_el else ""
            if not any(w in published_text for w in ["сегодня", "вчера", "назад", "минут", "час"]):
                continue

            price_el = card.select_one(".task-card__price")
            price = clean_text(price_el.text) if price_el else "Договорная"
            link = "https://freelance.habr.com" + title_el.get("href", "")
            cat = "Telegram" if any(k in title.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"

            tasks.append({
                "title": title,
                "price": price,
                "url": link,
                "category": cat,
                "source": "Хабр (< 5 откликов)",
                "published_at": published_text.capitalize(),
                "responses": f"{responses_count} откл.",
                "direct_contact": None,
                "discovered_at": datetime.now(timezone.utc).isoformat()
            })
    except Exception as e:
        print(f"[!] Хабр ошибка: {e}")
        
    return tasks

# ==========================================
# 4. СБОР ИЗ TELEGRAM (ПРЯМОЙ КОНТАКТ)
# ==========================================
def parse_tg(channel: str):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return tasks
            
        soup = BeautifulSoup(res.text, "html.parser")
        messages = soup.select(".tgme_widget_message")
        
        for msg in messages[-25:]:
            text_el = msg.select_one(".tgme_widget_message_text")
            date_el = msg.select_one(".tgme_widget_message_date time")
            link_el = msg.select_one(".tgme_widget_message_date")
            
            if not text_el or not link_el:
                continue
                
            text = text_el.text.strip()
            if not is_matching_skills(text):
                continue

            msg_dt = None
            published_str = "Сегодня"
            if date_el and date_el.get("datetime"):
                try:
                    msg_dt = datetime.fromisoformat(date_el.get("datetime"))
                    if not is_fresh_date(msg_dt):
                        continue
                    published_str = msg_dt.strftime("%d.%m %H:%M")
                except Exception:
                    pass

            first_line = clean_text(text.split("\n")[0])
            title = (first_line[:90] + "...") if len(first_line) > 90 else first_line
            link = link_el.get("href")

            # Извлечение контакта
            direct_contact = None
            found_usernames = re.findall(r"@[a-zA-Z0-9_]{5,}", text)
            if found_usernames:
                valid_usernames = [u for u in found_usernames if channel.lower() not in u.lower()]
                if valid_usernames:
                    direct_contact = valid_usernames[0]

            cat = "Telegram" if any(k in text.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"

            discovered_time = msg_dt.isoformat() if msg_dt else datetime.now(timezone.utc).isoformat()

            tasks.append({
                "title": title,
                "price": "В описании",
                "url": link,
                "category": cat,
                "source": f"TG (@{channel})",
                "published_at": published_str,
                "responses": "0–1 чел. (в ЛС)",
                "direct_contact": direct_contact,
                "discovered_at": discovered_time
            })
    except Exception as e:
        print(f"[!] TG @{channel} ошибка: {e}")
        
    return tasks

# ==========================================
# 5. ХРАНИЛИЩЕ И ОЧИСТКА СТАРШЕ 2 ДНЕЙ
# ==========================================
def load_existing_orders() -> list:
    """Загружает уже сохраненные заказы из orders.json."""
    if not os.path.exists("orders.json"):
        return []
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def filter_orders_under_48h(orders: list) -> list:
    """Оставляет только те заказы, с момента появления которых прошло меньше 48 часов."""
    now = datetime.now(timezone.utc)
    fresh_orders = []

    for order in orders:
        disc_str = order.get("discovered_at")
        if not disc_str:
            # Если метки времени нет, сохраняем заказ
            fresh_orders.append(order)
            continue
        try:
            order_time = datetime.fromisoformat(disc_str)
            if order_time.tzinfo is None:
                order_time = order_time.replace(tzinfo=timezone.utc)
            
            # Прошло меньше 2 дней (48 часов)
            if (now - order_time).total_seconds() <= 48 * 3600:
                fresh_orders.append(order)
        except Exception:
            fresh_orders.append(order)

    return fresh_orders

if __name__ == "__main__":
    # 1. Загружаем историю прошлых заказов
    old_orders = load_existing_orders()
    
    # 2. Собираем свежие задачи
    new_scraped = []
    for ch in TG_CHANNELS:
        new_scraped.extend(parse_tg(ch))
    new_scraped.extend(parse_habr())
    
    # 3. Объединяем старые и новые без дубликатов по ссылке
    # Новые задачи идут в начало списка
    combined_orders = []
    seen_urls = set()
    
    for order in new_scraped + old_orders:
        url = order.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            combined_orders.append(order)
            
    # 4. Удаляем то, что старше 48 часов
    final_orders = filter_orders_under_48h(combined_orders)
    
    # 5. Сохраняем обратно в orders.json
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(final_orders, f, ensure_ascii=False, indent=2)
        
    print(f"Готово! В базе {len(final_orders)} актуальных заказов за последние 2 дня.")
