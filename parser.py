import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import feedparser

# ==========================================
# 1. ОТКРЫТЫЕ БИРЖИ (БЕЗ ПЛАТНЫХ ОТКЛИКОВ)
# ==========================================
RSS_FEEDS = [
    # Хабр Фриланс (целевые категории разработки и дизайна)
    {
        "url": "https://freelance.habr.com/tasks.rss?categories=development_all_inclusive,development_backend,development_frontend,development_scripts,development_bots,design_websites,design_landings,design_app_interfaces",
        "source": "Хабр Фриланс"
    },
    # Freelancehunt (открытые проекты без PRO)
    {
        "url": "https://freelancehunt.com/rss/projects",
        "source": "Freelancehunt"
    },
    # Открытые ленты проектов для фрилансеров
    {
        "url": "https://freten.ru/rss/orders",
        "source": "Freten (Открытая доска)"
    }
]

# ==========================================
# 2. 50+ TELEGRAM-КАНАЛОВ И ЧАТОВ С ПРЯМОЙ СВЯЗЬЮ
# ==========================================
TG_CHANNELS = [
    # --- Боты, TMA, Python, Скрипты ---
    "zakazy_it", "web_zakazy", "it_podrabotka", "bots_orders", 
    "bot_zakazy", "zakaz_na_bota", "tg_apps_jobs", "tma_developers",
    "python_rabota", "aiogram_jobs", "telethon_jobs", "py_jobs",
    "python_freelance", "python_job_board", "bot_creators_ru",
    "pydevjob", "it_bot_zakaz", "telegram_bots_order", "py_orders",
    "script_freelance", "bot_developers_ru",
    
    # --- Веб-дизайн, UI/UX, Figma ---
    "design_zakaz", "figma_orders", "design_podrabotka", "freelancedesign",
    "webdesign_jobs", "freelance_design_ru", "uiux_jobs", "webdesign_freelance",
    "designers_chat_ru", "figma_freelance", "ui_ux_orders", "landing_design_ru",
    "web_designer_zakaz", "figma_jobs_ru", "design_projects_it",
    
    # --- Сайты, Верстка, Быстрый фриланс без регистраций ---
    "freelansim_ru", "freelancehunt_orders", "forfreelance", "it_freelance_zakaz",
    "freelance_orders_ru", "pomogator_freelance", "verstka_jobs", "freelancetavern",
    "freeworkfeed", "ru_freelance", "it_job_board", "work_in_it",
    "html_css_jobs", "front_jobs", "frontend_jobs_ru", "webdev_orders",
    "freelance_chat_it", "zakazy_na_sait", "sayty_pod_kluch", "verstka_zakaz",
    "web_freelance_feed", "it_projects_ru", "freelance_daily_ru"
]

# ==========================================
# 3. ТОЧНЫЕ КЛЮЧЕВЫЕ СЛОВА (ТОЛЬКО РЕАЛЬНЫЕ ЗАКАЗЫ)
# ==========================================
TARGET_PHRASES = [
    # Telegram боты и TMA
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бота в тг",
    "бота для", "написать бота", "сделать бота", "создать бота", "починить бота",
    "aiogram", "pyrogram", "telethon", "mini app", "tma", "webapp", "кликер",
    
    # Сайты под ключ и верстка
    "сверстать", "верстка", "лендинг", "landing", "сайт-визитка", "сайт визитка",
    "сделать сайт", "создать сайт", "разработать сайт", "доработать сайт",
    "одностраничник", "поправить верстку", "адаптивная верстка", "натянуть верстку",
    "верстка макета", "сайт под ключ",
    
    # Веб-дизайн и Figma
    "дизайн сайта", "дизайн лендинга", "макет в figma", "макет сайта",
    "редизайн сайта", "прототип сайта", "ui/ux", "ui-ux", "дизайн интерфейса",
    "макет лендинга", "дизайн для сайта", "оформить сайт", "макет страницы",
    
    # Парсеры и скрипты автоматизации
    "парсер", "написать скрипт", "сделать парсер", "спарсить",
    "парсер на python", "скрипт на python", "автоматизация"
]

# ==========================================
# 4. СТОП-СЛОВА (ШТАТ, SMM, ВАКАНСИИ, FL.RU)
# ==========================================
STOP_WORDS = [
    # Платные биржи (жесткий запрет)
    "fl.ru", "fl_ru", "kwork", "кворк", "freelance.ru",
    
    # Штатный найм и вакансии на зарплату
    "опыт работы от", "опыт от 3", "опыт от 2", "опыт от 5",
    "в штат", "фуллтайм", "fulltime", "full-time", "оформление по тк",
    "испытательный срок", "оклад", "зарплата от", "зп от",
    "middle+", "senior", "teamlead", "lead", "руководитель",
    "qa engineer", "тестировщик", "aqa", "manual qa",
    
    # SMM, маркетинг, тексты
    "traffic manager", "media buyer", "арбитраж", "баер",
    "smm", "смм", "таргет", "таргетолог", "копирайтер", "копирайтинг",
    "рилс", "reels", "shorts", "монтажер", "инвайтинг", "прогрев",
    "wildberries", "вайлдберриз", "ozon", "озон", "карточек товара",
    "закупка рекламы", "контент план", "написание статей",
    
    # Нецелевой тяжелый стек
    "1с", "1c", "bitrix", "битрикс", "flutter", "react native",
    "swift", "kotlin", "ios", "android", "c#", "c++", ".net", "java", "golang", "rust"
]

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_matching(text: str) -> bool:
    text_lower = text.lower()
    
    # 1. Отсеиваем спам, вакансии, SMM и платные биржи
    for stop in STOP_WORDS:
        if stop in text_lower:
            return False
            
    # 2. Требуем совпадение с целевыми задачами
    return any(p in text_lower for p in TARGET_PHRASES)

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
# 5. СБОР ИЗ ОТКРЫТЫХ RSS-ЛЕНТ
# ==========================================
def parse_rss_feeds():
    tasks = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"], request_headers=headers)
            for entry in feed.entries[:25]:
                title = clean_text(entry.title)
                summary = clean_text(getattr(entry, "summary", ""))
                link = getattr(entry, "link", "")
                
                # Защита от попадания ссылок на платные биржи
                if "fl.ru" in link.lower() or "kwork" in link.lower():
                    continue
                    
                full_text = f"{title} {summary}"
                if not is_matching(full_text):
                    continue

                tasks.append({
                    "title": title[:95] + "..." if len(title) > 95 else title,
                    "price": "Договорная",
                    "url": link,
                    "category": get_category(full_text),
                    "source": feed_info["source"],
                    "published_at": "Сегодня",
                    "responses": "Открытый отклик",
                    "direct_contact": None,
                    "discovered_at": datetime.now(timezone.utc).isoformat()
                })
        except Exception:
            pass
            
    return tasks

# ==========================================
# 6. СБОР ИЗ TELEGRAM (ПРЯМОЙ КОНТАКТ В ЛС)
# ==========================================
def parse_tg(channel: str):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=7)
        if res.status_code != 200:
            return tasks
            
        soup = BeautifulSoup(res.text, "html.parser")
        messages = soup.select(".tgme_widget_message")
        
        for msg in messages[-20:]:
            text_el = msg.select_one(".tgme_widget_message_text")
            date_el = msg.select_one(".tgme_widget_message_date time")
            link_el = msg.select_one(".tgme_widget_message_date")
            
            if not text_el or not link_el:
                continue
                
            text = text_el.text.strip()
            
            # Отсекаем посты со ссылками на платные биржи
            if "fl.ru" in text.lower() or "kwork" in text.lower():
                continue
                
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
                    
                    if (now - dt).total_seconds() > 48 * 3600:
                        continue
                    published_str = dt.strftime("%d.%m %H:%M")
                    msg_iso = dt.isoformat()
                except Exception:
                    pass

            first_line = clean_text(text.split("\n")[0])
            title = (first_line[:95] + "...") if len(first_line) > 95 else first_line
            link = link_el.get("href")

            # Извлечение контакта заказчика в Telegram
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
# 7. ХРАНЕНИЕ И АВТООЧИСТКА ЗА 48 ЧАСОВ
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
        url = order.get("url", "").lower()
        title = order.get("title", "")
        
        # Удаляем любые остатки FL.ru
        if "fl.ru" in url or "kwork" in url:
            continue
            
        if not is_matching(title):
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
    
    print("[*] Сбор задач с открытых бирж...")
    new_scraped.extend(parse_rss_feeds())
    
    print(f"[*] Сбор прямых заказов из {len(TG_CHANNELS)} каналов Telegram...")
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
