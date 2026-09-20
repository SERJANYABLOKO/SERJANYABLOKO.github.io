import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. СПИСОК TELEGRAM-КАНАЛОВ И ЧАТОВ (~55 ИСТОЧНИКОВ)
# Все каналы открытые, парсятся через web-интерфейс t.me/s/ без API-ключей
# ==========================================
TG_CHANNELS = [
    # --- Python, Telegram-боты, Mini Apps, Скрипты ---
    "job_python",
    "py_jobs",
    "aiogram_jobs",
    "python_rabota",
    "it_podrabotka",
    "zakazy_it",
    "web_zakazy",
    "python_jobs",
    "pythonjob",
    "python_work",
    "django_jobs",
    "telethon_jobs",
    "tg_apps_jobs",
    "python_freelance",
    "pydevjob",
    "python_dev_jobs",

    # --- Официальные открытые ленты бирж (без платных тарифов) ---
    "freelansim_ru",          # Официальный канал заказов Хабр Фриланс
    "freelancehunt_orders",   # Открытый поток задач с Freelancehunt

    # --- Общие IT-заказы и подработка без переплат ---
    "freelancetavern",
    "digitaltender",
    "forfreelance",
    "it_freelance_zakaz",
    "work_in_it",
    "freelance_rabota_rf",
    "freelance_orders_ru",
    "it_job_board",
    "freeworkfeed",
    "pomogator_freelance",
    "freelance_choice",
    "freelance_it_job",
    "it_hiring_chat",
    "zakazy_na_sait",
    "ru_freelance",
    "freelance_daily",
    "freelancers_hub",
    "it_lead_jobs",
    "freelance_chat_it",
    "it_freelance_hub",
    "web_dev_jobs",
    "frontend_jobs_ru",
    "backend_jobs_ru",
    "it_projects_ru",

    # --- Веб-верстка, Frontend и Сайты ---
    "front_jobs",
    "html_css_jobs",
    "webdev_chat",
    "verstka_jobs",
    "tma_developers",
    "telegram_mini_apps",
    "miniapps_jobs",
    "bot_creators_ru",
    "bots_orders",
    "zakaz_na_bota",
    "bot_zakazy"
]

# ==========================================
# 2. ФИЛЬТР ЦЕЛЕВЫХ НАВЫКОВ (РАЗРАБОТКА)
# ==========================================
TARGET_KEYWORDS = [
    # Telegram боты и WebApp / Mini App
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бота", "бота для",
    "написать бота", "дописать бота", "починить бота", "разработка бота",
    "aiogram", "telethon", "pyrogram", "python-telegram-bot",
    "mini app", "мини апп", "tma", "webapp", "web app", "telegram mini app",
    
    # Сайты и верстка
    "верстка", "сверстать", "html", "css", "landing", "лендинг", 
    "сайт визитка", "простой сайт", "статический сайт", "поправить верстку",
    "сделать сайт", "доработать сайт", "натянуть верстку", "адаптивная верстка",
    
    # Парсеры, скрипты и автоматизация
    "написать скрипт", "сделать парсер", "парсер на python", "спарсить",
    "скрипт на python", "парсер данных", "автоматизация", "парсер",
    "выгрузить данные", "сбор данных"
]

# ==========================================
# 3. СТОП-СЛОВА (SMM + МАРКЕТИНГ + БИРЖИ С ОГРАНИЧЕНИЯМИ)
# ==========================================
STOP_WORDS = [
    # Биржи с платными откликами / обязательной верификацией
    "kwork", "кворк", "fl.ru", "freelance.ru",
    
    # SMM, маркетинг, контент и соцсети (полная блокировка)
    "smm", "смм", "smm-специалист", "смм-специалист", "ведение канала",
    "ведение telegram", "контент-мейкер", "копирайтер", "копирайтинг",
    "таргетолог", "таргет", "рилс", "reels", "shorts", "монтажер",
    "дизайнер", "дизайн карточек", "оформление канала", "сторисмейкер",
    "менеджер блогера", "закупка рекламы", "трафик", "инвайтинг",
    "накрутка", "прогрев", "reelsмейкер", "сторис", "маркетолог",
    "контент план", "постинг", "рассыльщик вручную", "отзывы",
    
    # Неподходящий или корпоративный стек
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
    
    # Жесткий фильтр SMM и стоп-слов
    for stop in STOP_WORDS:
        if stop in text_lower:
            return False
            
    # Проверка на наличие технической задачи
    return any(k in text_lower for k in TARGET_KEYWORDS)

def is_fresh_date(dt: datetime) -> bool:
    """Не старше 48 часов."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() <= 48 * 3600

# ==========================================
# 4. СБОР С ХАБР ФРИЛАНСА (СТРОГО ДО 10 ОТКЛИКОВ)
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
            
            # Фильтр: строго <= 10 откликов
            responses_el = card.select_one(".task-params__item_responses")
            responses_count = 0
            if responses_el:
                digits = re.findall(r"\d+", clean_text(responses_el.text))
                if digits:
                    responses_count = int(digits[0])
            
            if responses_count > 10:
                continue

            # Фильтр свежести: сегодня / вчера
            date_el = card.select_one(".task-params__item_published")
            published_text = clean_text(date_el.text).lower() if date_el else ""
            if not any(w in published_text for w in ["сегодня", "вчера", "назад", "минут", "час"]):
                continue

            price_el = card.select_one(".task-card__price")
            price = clean_text(price_el.text) if price_el else "Договорная"
            link = "https://freelance.habr.com" + title_el.get("href", "")
            
            title_lower = title.lower()
            if any(k in title_lower for k in ["бот", "app", "tma"]):
                cat = "Telegram"
            elif any(k in title_lower for k in ["парсер", "спарсить", "скрипт"]):
                cat = "Парсеры"
            else:
                cat = "Веб-сайт"

            tasks.append({
                "title": title,
                "price": price,
                "url": link,
                "category": cat,
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
# 5. СБОР ИЗ TELEGRAM-КАНАЛОВ И ЧАТОВ
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

            # Поиск контакта @username в сообщении
            direct_contact = None
            found_usernames = re.findall(r"@[a-zA-Z0-9_]{5,}", text)
            if found_usernames:
                valid_usernames = [u for u in found_usernames if channel.lower() not in u.lower()]
                if valid_usernames:
                    direct_contact = valid_usernames[0]

            text_lower = text.lower()
            if any(k in text_lower for k in ["бот", "app", "tma"]):
                cat = "Telegram"
            elif any(k in text_lower for k in ["парсер", "спарсить", "скрипт"]):
                cat = "Парсеры"
            else:
                cat = "Веб-сайт"

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
    except Exception:
        # Пропускаем недоступные или приватные каналы без прерывания
        pass
        
    return tasks

# ==========================================
# 6. ХРАНЕНИЕ И АВТООЧИСТКА ЗАКАЗОВ (48 ЧАСОВ)
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
        # Чистим историю от попавшего ранее SMM
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
    print(f"[*] Сканирование {len(TG_CHANNELS)} каналов и чатов...")
    for ch in TG_CHANNELS:
        new_scraped.extend(parse_tg(ch))
        
    print("[*] Сканирование Хабр Фриланс...")
    new_scraped.extend(parse_habr())
    
    # Объединяем старые и новые без повторов
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
        
    print(f"[+] Успешно! В базе {len(final_orders)} актуальных заказов без SMM за 48 часов.")
