import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. TELEGRAM-КАНАЛЫ (РАЗРАБОТКА + ДИЗАЙН)
# ==========================================
TG_CHANNELS = [
    # Разработка ботов, Python, TMA, скрипты
    "job_python", "py_jobs", "aiogram_jobs", "python_rabota",
    "it_podrabotka", "zakazy_it", "web_zakazy", "django_jobs",
    "telethon_jobs", "tg_apps_jobs", "python_freelance", "pydevjob",
    "tma_developers", "bot_creators_ru", "bots_orders", "bot_zakazy",
    
    # Веб-дизайн и UI/UX (новые каналы)
    "uiux_jobs", "design_zakaz", "webdesign_jobs", "figma_orders",
    "freelancedesign", "design_podrabotka", "uiux_designer_jobs",
    "webdesign_freelance", "designers_chat_ru",
    
    # Общие IT-заказы и открытые биржи
    "freelansim_ru", "freelancehunt_orders", "freelancetavern",
    "digitaltender", "forfreelance", "it_freelance_zakaz",
    "work_in_it", "freelance_rabota_rf", "freelance_orders_ru",
    "it_job_board", "pomogator_freelance", "ru_freelance",
    "frontend_jobs_ru", "front_jobs", "html_css_jobs", "verstka_jobs"
]

# ==========================================
# 2. КЛЮЧЕВЫЕ СЛОВА (РАЗРАБОТКА + ВЕБ-ДИЗАЙН)
# ==========================================
TARGET_KEYWORDS = [
    # Telegram боты и TMA
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бота для",
    "написать бота", "дописать бота", "починить бота", "разработка бота",
    "aiogram", "telethon", "pyrogram", "mini app", "мини апп", "tma", "webapp",
    
    # Сайты, верстка и веб-разработка
    "верстка", "сверстать", "html", "css", "landing", "лендинг", 
    "сайт визитка", "простой сайт", "статический сайт", "поправить верстку",
    "сделать сайт", "доработать сайт", "адаптивная верстка",
    
    # Веб-дизайн и UI/UX
    "веб дизайн", "веб-дизайн", "дизайн сайта", "дизайн лендинга",
    "ui/ux", "ui-ux", "макет сайта", "макет в figma", "сделать в figma",
    "редизайн сайта", "прототип сайта", "дизайн интерфейса", "фигма", "figma",
    
    # Парсеры и скрипты
    "написать скрипт", "сделать парсер", "парсер на python", "спарсить",
    "скрипт на python", "парсер данных", "автоматизация"
]

# ==========================================
# 3. СТОП-СЛОВА (SMM + МАРКЕТИНГ + СЛОЖНЫЙ СТЕК)
# ==========================================
STOP_WORDS = [
    "kwork", "кворк", "fl.ru", "freelance.ru",
    "smm", "смм", "smm-специалист", "смм-специалист", "ведение канала",
    "ведение telegram", "контент-мейкер", "копирайтер", "копирайтинг",
    "таргетолог", "таргет", "рилс", "reels", "shorts", "монтажер",
    "дизайн карточек", "оформление канала", "сторисмейкер", "менеджер блогера",
    "закупка рекламы", "трафик", "инвайтинг", "накрутка", "прогрев", "постинг",
    "1с", "1c", "bitrix", "битрикс", "wordpress", "senior", "lead", "teamlead",
    "flutter", "react native", "swift", "kotlin", "ios", "android", "c#", "c++", ".net", "java", "php"
]

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_matching_skills(text: str) -> bool:
    text_lower = text.lower()
    for stop in STOP_WORDS:
        if stop in text_lower:
            return False
    return any(k in text_lower for k in TARGET_KEYWORDS)

def is_fresh_date(dt: datetime) -> bool:
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() <= 48 * 3600

def get_category(text: str) -> str:
    text_lower = text.lower()
    if any(k in text_lower for k in ["дизайн", "figma", "фигма", "ui/ux", "ui-ux", "макет"]):
        return "Дизайн"
    elif any(k in text_lower for k in ["бот", "app", "tma"]):
        return "Telegram"
    elif any(k in text_lower for k in ["парсер", "спарсить", "скрипт"]):
        return "Парсеры"
    return "Веб-сайт"

# ==========================================
# 4. СБОР С ХАБРА (<= 10 ОТКЛИКОВ)
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
            
            responses_el = card.select_one(".task-params__item_responses")
            responses_count = 0
            if responses_el:
                digits = re.findall(r"\d+", clean_text(responses_el.text))
                if digits:
                    responses_count = int(digits[0])
            
            if responses_count > 10:
                continue

            date_el = card.select_one(".task-params__item_published")
            published_text = clean_text(date_el.text).lower() if date_el else ""
            if not any(w in published_text for w in ["сегодня", "вчера", "назад", "минут", "час"]):
                continue

            price_el = card.select_one(".task-card__price")
            price = clean_text(price_el.text) if price_el else "Договорная"
            link = "https://freelance.habr.com" + title_el.get("href", "")

            tasks.append({
                "title": title,
                "price": price,
                "url": link,
                "category": get_category(title),
                "source": "Хабр (< 10 откл.)",
                "published_at": published_text.capitalize(),
                "responses": f"{responses_count} откл.",
                "direct_contact": None,
                "discovered_at": datetime.now(timezone.utc).isoformat()
            })
    except Exception as e:
        print(f"[!] Хабр ошибка: {e}")
        
    return tasks

# ==========================================
# 5. СБОР ИЗ TELEGRAM
# ==========================================
def parse_tg(channel: str):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=8)
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

            direct_contact = None
            found_usernames = re.findall(r"@[a-zA-Z0-9_]{5,}", text)
            if found_usernames:
                valid_usernames = [u for u in found_usernames if channel.lower() not in u.lower()]
                if valid_usernames:
                    direct_contact = valid_usernames[0]

            discovered_time = msg_dt.isoformat() if msg_dt else datetime.now(timezone.utc).isoformat()

            tasks.append({
                "title": title,
                "price": "В описании",
                "url": link,
                "category": get_category(text),
                "source": f"TG (@{channel})",
                "published_at": published_str,
                "responses": "0–1 чел. (в ЛС)",
                "direct_contact": direct_contact,
                "discovered_at": discovered_time
            })
    except Exception:
        pass
        
    return tasks

# ==========================================
# 6. ХРАНЕНИЕ И АВТООЧИСТКА ЗА 48 ЧАСОВ
# ==========================================
def load_existing_orders() -> list:
    if not os.path.exists("orders.json"):
        return []
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def filter_orders_under_48h(orders: list) -> list:
    now = datetime.now(timezone.utc)
    fresh_orders = []

    for order in orders:
        if not is_matching_skills(order.get("title", "")):
            continue
            
        disc_str = order.get("discovered_at")
        if not disc_str:
            fresh_orders.append(order)
            continue
        try:
            order_time = datetime.fromisoformat(disc_str)
            if order_time.tzinfo is None:
                order_time = order_time.replace(tzinfo=timezone.utc)
            if (now - order_time).total_seconds() <= 48 * 3600:
                fresh_orders.append(order)
        except Exception:
            fresh_orders.append(order)

    return fresh_orders

if __name__ == "__main__":
    old_orders = load_existing_orders()
    
    new_scraped = []
    print(f"[*] Сканирование {len(TG_CHANNELS)} каналов...")
    for ch in TG_CHANNELS:
        new_scraped.extend(parse_tg(ch))
        
    print("[*] Сканирование Хабр Фриланс...")
    new_scraped.extend(parse_habr())
    
    combined_orders = []
    seen_urls = set()
    
    for order in new_scraped + old_orders:
        url = order.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            combined_orders.append(order)
            
    final_orders = filter_orders_under_48h(combined_orders)
    
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(final_orders, f, ensure_ascii=False, indent=2)
        
    print(f"[+] Готово! В базе {len(final_orders)} актуальных заказов (IT + Web-Design).")
