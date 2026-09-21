import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. ОТКРЫТЫЕ ИСТОЧНИКИ (КАНАЛЫ + БИРЖИ)
# ==========================================
TG_CHANNELS = [
    # Боты, Python, Скрипты, TMA
    "job_python", "py_jobs", "aiogram_jobs", "python_rabota",
    "it_podrabotka", "zakazy_it", "web_zakazy", "telethon_jobs",
    "tg_apps_jobs", "python_freelance", "tma_developers",
    "bot_creators_ru", "bots_orders", "bot_zakazy", "zakaz_na_bota",
    
    # Веб-дизайн, Figma, UI/UX
    "uiux_jobs", "design_zakaz", "webdesign_jobs", "figma_orders",
    "freelancedesign", "design_podrabotka", "uiux_designer_jobs",
    "webdesign_freelance", "designers_chat_ru", "freelance_design_ru",
    
    # Сайты, Верстка, Фриланс
    "freelansim_ru", "freelancehunt_orders", "freelancetavern",
    "digitaltender", "forfreelance", "it_freelance_zakaz",
    "work_in_it", "freelance_rabota_rf", "freelance_orders_ru",
    "it_job_board", "pomogator_freelance", "ru_freelance",
    "frontend_jobs_ru", "front_jobs", "html_css_jobs", "verstka_jobs"
]

# ==========================================
# 2. РАСШИРЕННЫЕ КЛЮЧЕВЫЕ СЛОВА
# ==========================================
TARGET_KEYWORDS = [
    # Telegram боты и TMA
    "бот", "боты", "бота", "боту", "ботом", "тг бот", "тг-бот", "telegram bot",
    "aiogram", "telethon", "pyrogram", "mini app", "мини апп", "tma", "webapp", "web app",
    
    # Сайты и верстка
    "сайт", "сайта", "сайты", "верстка", "сверстать", "html", "css", "landing", "лендинг", 
    "веб-сайт", "web-сайт", "одностраничник", "поправить верстку", "доработать сайт",
    
    # Веб-дизайн и Figma
    "дизайн", "дизайна", "дизайнер", "ui/ux", "ui-ux", "ui", "ux", "figma", "фигма", 
    "макет", "макета", "прототип", "редизайн", "оформление сайта",
    
    # Парсеры и скрипты
    "парсер", "парсить", "спарсить", "скрипт", "скрипта", "автоматизация", "сбор данных"
]

# ==========================================
# 3. ТОЧЕЧНЫЕ СТОП-СЛОВА (БЕЗ ЛОЖНЫХ СРАБАТЫВАНИЙ)
# ==========================================
STOP_WORDS = [
    # Платные биржи
    "kwork.ru", "fl.ru/projects", "freelance.ru/projects",
    
    # SMM, маркетинг, контент (не путать с веб-дизайном)
    "smm", "смм", "smm-специалист", "смм-специалист", "ведение канала",
    "ведение telegram", "контент-мейкер", "копирайтер", "копирайтинг",
    "таргетолог", "таргет", "рилс", "reels", "shorts", "монтажер",
    "сторисмейкер", "закупка рекламы", "трафик", "инвайтинг", "накрутка",
    "дизайн карточек вайлдберриз", "дизайн карточек wildberries", "дизайн карточек ozon",
    
    # Слишком высокий грейд (где требуют 3+ года опыта в компании)
    "senior", "lead", "teamlead", "руководитель отдела", "арт-директор"
]

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_matching_skills(text: str) -> bool:
    text_lower = text.lower()
    
    # Отсеиваем только реальный SMM и платные биржи
    for stop in STOP_WORDS:
        if stop in text_lower:
            return False
            
    # Проверяем наличие ключевых слов
    return any(k in text_lower for k in TARGET_KEYWORDS)

def get_category(text: str) -> str:
    text_lower = text.lower()
    if any(k in text_lower for k in ["дизайн", "figma", "фигма", "ui/ux", "ui-ux", "макет", "прототип", "редизайн"]):
        return "Дизайн"
    elif any(k in text_lower for k in ["бот", "app", "tma", "aiogram", "telethon", "mini app"]):
        return "Telegram"
    elif any(k in text_lower for k in ["парсер", "спарсить", "скрипт"]):
        return "Парсеры"
    return "Веб-сайт"

# ==========================================
# 4. СБОР С ХАБРА (ДО 10 ОТКЛИКОВ)
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
            
            # До 10 откликов (чтобы не было огромной конкуренции)
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
        print(f"[!] Ошибка Хабра: {e}")
        
    return tasks

# ==========================================
# 5. СБОР ИЗ TELEGRAM (ПРЯМОЙ КОНТАКТ)
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
        
        for msg in messages[-30:]:
            text_el = msg.select_one(".tgme_widget_message_text")
            date_el = msg.select_one(".tgme_widget_message_date time")
            link_el = msg.select_one(".tgme_widget_message_date")
            
            if not text_el or not link_el:
                continue
                
            text = text_el.text.strip()
            if not is_matching_skills(text):
                continue

            published_str = "Сегодня"
            msg_iso = datetime.now(timezone.utc).isoformat()
            
            if date_el and date_el.get("datetime"):
                try:
                    dt = datetime.fromisoformat(date_el.get("datetime"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    
                    # Проверяем: не старше 48 часов
                    if (now - dt).total_seconds() > 48 * 3600:
                        continue
                    published_str = dt.strftime("%d.%m %H:%M")
                    msg_iso = dt.isoformat()
                except Exception:
                    pass

            first_line = clean_text(text.split("\n")[0])
            title = (first_line[:95] + "...") if len(first_line) > 95 else first_line
            link = link_el.get("href")

            # Извлечение прямого юзернейма заказчика
            direct_contact = None
            found_usernames = re.findall(r"@[a-zA-Z0-9_]{4,}", text)
            if found_usernames:
                valid_usernames = [u for u in found_usernames if channel.lower() not in u.lower() and "bot" not in u.lower()]
                if valid_usernames:
                    direct_contact = valid_usernames[0]

            tasks.append({
                "title": title,
                "price": "В описании",
                "url": link,
                "category": get_category(text),
                "source": f"TG (@{channel})",
                "published_at": published_str,
                "responses": "0–1 чел. (в ЛС)",
                "direct_contact": direct_contact,
                "discovered_at": msg_iso
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
    print(f"[*] Сбор заказов с {len(TG_CHANNELS)} каналов...")
    for ch in TG_CHANNELS:
        new_scraped.extend(parse_tg(ch))
        
    print("[*] Сбор заказов с Хабр Фриланс...")
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
        
    print(f"[+] Готово! В базе {len(final_orders)} задач (боты, сайты, веб-дизайн, скрипты).")
