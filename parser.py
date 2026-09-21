import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import feedparser

# ==========================================
# 1. ОТКРЫТЫЕ ИСТОЧНИКИ ДЛЯ РАЗОВЫХ ЗАКАЗОВ
# ==========================================

# Открытые RSS-ленты бирж (парсятся без регистрации и капчи)
RSS_FEEDS = [
    # Хабр Фриланс: разработка и дизайн
    {"url": "https://freelance.habr.com/tasks.rss", "source": "Хабр Фриланс"},
    # FL.ru: открытые RSS-ленты по направлениям подработки
    {"url": "https://www.fl.ru/rss/all.xml?category=5", "source": "FL (Веб-разработка)"},
    {"url": "https://www.fl.ru/rss/all.xml?subcat=38", "source": "FL (Боты и скрипты)"},
    {"url": "https://www.fl.ru/rss/all.xml?category=1", "source": "FL (Дизайн сайтов)"},
]

# Каналы Telegram с разовыми заказами, проектной работой и подработкой
TG_CHANNELS = [
    # Боты, Python, Скрипты
    "zakazy_it", "web_zakazy", "it_podrabotka", "bots_orders", 
    "bot_zakazy", "zakaz_na_bota", "tg_apps_jobs", "tma_developers",
    "python_rabota", "aiogram_jobs", "telethon_jobs", "py_jobs",
    
    # Веб-дизайн, лендинги, Figma, интерфейсы
    "design_zakaz", "figma_orders", "design_podrabotka", "freelancedesign",
    "webdesign_jobs", "freelance_design_ru", "uiux_jobs", "webdesign_freelance",
    
    # Фриланс, верстка, сайты под ключ
    "freelansim_ru", "freelancehunt_orders", "forfreelance", "it_freelance_zakaz",
    "freelance_orders_ru", "pomogator_freelance", "verstka_jobs", "freelancetavern",
    "freeworkfeed", "ru_freelance", "it_job_board", "work_in_it",
    "html_css_jobs", "front_jobs", "frontend_jobs_ru"
]

# ==========================================
# 2. КЛЮЧЕВЫЕ СЛОВА (ТОЛЬКО РАЗОВЫЕ IT И ДИЗАЙН ЗАКАЗЫ)
# ==========================================
TARGET_KEYWORDS = [
    # Боты и TMA
    "бот", "боты", "бота", "боту", "тг бот", "тг-бот", "telegram bot",
    "aiogram", "telethon", "pyrogram", "mini app", "tma", "webapp", "кликер",
    
    # Сайты и верстка
    "сайт", "сайта", "сайты", "верстка", "сверстать", "html", "css",
    "landing", "лендинг", "одностраничник", "поправить верстку", "доработать сайт",
    
    # Дизайн и Figma
    "дизайн", "дизайна", "дизайнер", "ui/ux", "ui-ux", "figma", "фигма",
    "макет", "прототип", "баннер", "оформление", "редизайн",
    
    # Скрипты и парсеры
    "парсер", "парсить", "спарсить", "скрипт", "автоматизация", "сбор данных"
]

# ==========================================
# 3. СТОП-СЛОВА (ШТАТ, АРБИТРАЖ, SMM, ВАКАНСИИ)
# ==========================================
STOP_WORDS = [
    # Штатный найм и вакансии на зарплату
    "traffic manager", "media buyer", "lead", "teamlead",
    "qa automation", "qa engineer", "тестировщик", "manual qa", "aqa",
    "опыт работы от", "опыт от 3", "опыт от 2", "опыт от 5",
    "оформление по тк", "в штат", "фуллтайм", "fulltime", "full-time",
    "испытательный срок", "оклад", "зарплата от", "зп от",
    "middle+", "senior",
    
    # Маркетинг, арбитраж, трафик, SMM
    "google ads", "meta ads", "facebook ads", "арбитраж", "баер",
    "smm", "смм", "таргет", "таргетолог", "копирайтер", "копирайтинг",
    "рилс", "reels", "shorts", "монтажер", "инвайтинг", "прогрев",
    "карточек wildberries", "карточек ozon", "вайлдберриз", "wb",
    
    # Тяжелый корпоративный стек
    "1с", "1c", "bitrix", "битрикс", "flutter", "react native",
    "swift", "kotlin", "ios", "android", "c#", "c++", ".net", "java", "golang", "rust"
]

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_matching(text: str) -> bool:
    text_lower = text.lower()
    
    # 1. Проверяем стоп-слова
    for stop in STOP_WORDS:
        if stop in text_lower:
            return False
            
    # 2. Проверяем целевые навыки
    return any(k in text_lower for k in TARGET_KEYWORDS)

def get_category(text: str) -> str:
    text_lower = text.lower()
    if any(k in text_lower for k in ["дизайн", "figma", "фигма", "ui/ux", "ui-ux", "макет", "прототип", "баннер"]):
        return "Дизайн"
    elif any(k in text_lower for k in ["бот", "app", "tma", "aiogram", "telethon", "mini app"]):
        return "Telegram"
    elif any(k in text_lower for k in ["парсер", "спарсить", "скрипт"]):
        return "Парсеры"
    return "Веб-сайт"

# ==========================================
# 4. СБОР ИЗ RSS-ЛЕНТ БЕСПЛАТНЫХ БИРЖ
# ==========================================
def parse_rss_feeds():
    tasks = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"], request_headers=headers)
            for entry in feed.entries[:20]:
                title = clean_text(entry.title)
                summary = clean_text(getattr(entry, "summary", ""))
                full_text = f"{title} {summary}"
                
                if not is_matching(full_text):
                    continue
                    
                link = getattr(entry, "link", "")
                if not link:
                    continue

                tasks.append({
                    "title": title[:95] + "..." if len(title) > 95 else title,
                    "price": "Договорная",
                    "url": link,
                    "category": get_category(full_text),
                    "source": feed_info["source"],
                    "published_at": "Сегодня",
                    "responses": "Открытый заказ",
                    "direct_contact": None,
                    "discovered_at": datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            print(f"[!] Ошибка RSS {feed_info['source']}: {e}")
            
    return tasks

# ==========================================
# 5. СБОР ИЗ TELEGRAM-КАНАЛОВ (С ПРЯМОЙ СВЯЗЬЮ В ЛС)
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
            if not is_matching(text):
                continue

            published_str = "Сегодня"
            msg_iso = datetime.now(timezone.utc).isoformat()
            
            if date_el and date_el.get("datetime"):
                try:
                    dt = datetime.fromisoformat(date_el.get("datetime"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    
                    # Заказ не старше 48 часов
                    if (now - dt).total_seconds() > 48 * 3600:
                        continue
                    published_str = dt.strftime("%d.%m %H:%M")
                    msg_iso = dt.isoformat()
                except Exception:
                    pass

            first_line = clean_text(text.split("\n")[0])
            title = (first_line[:95] + "...") if len(first_line) > 95 else first_line
            link = link_el.get("href")

            # Поиск контакта @username заказчика
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
        if not is_matching(order.get("title", "")):
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
    
    print("[*] Сбор заказов из бесплатных RSS бирж...")
    new_scraped.extend(parse_rss_feeds())
    
    print(f"[*] Сбор заказов из Telegram ({len(TG_CHANNELS)} каналов)...")
    for ch in TG_CHANNELS:
        new_scraped.extend(parse_tg(ch))
        
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
        
    print(f"[+] Готово! В базе {len(final_orders)} реальных разовых заказов.")
