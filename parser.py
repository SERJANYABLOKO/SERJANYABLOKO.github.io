import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import feedparser

# ==========================================
# 1. ОТКРЫТЫЕ БИРЖИ И ПОИСКОВЫЕ ЛЕНТЫ
# ==========================================
RSS_FEEDS = [
    {
        "url": "https://freelance.habr.com/tasks.rss?categories=development_all_inclusive,development_backend,development_frontend,development_scripts,development_bots,design_websites,design_landings,design_app_interfaces",
        "source": "Хабр Фриланс"
    },
    {
        "url": "https://freelancehunt.com/rss/projects",
        "source": "Freelancehunt"
    },
    {
        "url": "https://freten.ru/rss/orders",
        "source": "Freten (Доска)"
    },
    {
        "url": "https://www.fl.ru/rss/all.rss?category=4",
        "source": "FL.ru"
    }
]

TG_CHANNELS = [
    "freelancebay", "Frilanser_100", "freelance_birzha", "tg_work", "golub_freelance",
    "zakazy_it", "web_zakazy", "it_podrabotka", "bots_orders", 
    "bot_zakazy", "zakaz_na_bota", "tg_apps_jobs", "tma_developers",
    "python_rabota", "aiogram_jobs", "telethon_jobs", "py_jobs",
    "python_freelance", "python_job_board", "bot_creators_ru",
    "pydevjob", "it_bot_zakaz", "telegram_bots_order", "py_orders",
    "script_freelance", "bot_developers_ru",
    "pc_builds", "iron_chat", "sbor_pc", "komp_help"
]

TARGET_PHRASES = [
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бота в тг",
    "написать бота", "сделать бота", "aiogram", "pyrogram", "mini app", "tma", "webapp",
    "сверстать", "верстка", "лендинг", "landing", "сайт-визитка", "сделать сайт", "создать сайт",
    "дизайн сайта", "дизайн лендинга", "макет в figma", "макет сайта", "ui/ux",
    "парсер", "написать скрипт", "сделать скрипт", "спарсить", "автоматизация",
    "сборка пк", "собрать пк", "апгрейд пк", "компьютер", "подбор комплектующих"
]

STOP_WORDS = ["опыт работы от 5", "в штат", "фуллтайм", "full-time", "оформление по тк"]

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_matching(text: str) -> bool:
    text_lower = text.lower()
    for stop in STOP_WORDS:
        if stop in text_lower:
            return False
    return True

def get_category(text: str, source: str) -> str:
    # Жесткое разделение: если источник FL.ru, то категория строго FL.ru
    if "FL.ru" in source:
        return "FL.ru"
        
    text_lower = text.lower()
    if any(k in text_lower for k in ["сборка", "апгрейд", "пк", "компьютер", "детал"]):
        return "Железо / ПК"
    elif any(k in text_lower for k in ["дизайн", "figma", "фигма", "ui/ux", "макет", "прототип"]):
        return "Дизайн"
    elif any(k in text_lower for k in ["бот", "app", "tma", "aiogram", "mini app"]):
        return "Telegram"
    elif any(k in text_lower for k in ["парсер", "спарсить", "скрипт"]):
        return "Парсеры"
    return "Веб-сайт"

def parse_rss_feeds():
    tasks = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"], request_headers=headers)
            for entry in feed.entries[:30]:
                title = clean_text(entry.title)
                summary = clean_text(getattr(entry, "summary", ""))
                link = getattr(entry, "link", "")
                full_text = f"{title} {summary}"
                
                tasks.append({
                    "title": title[:95] + "..." if len(title) > 95 else title,
                    "price": "Договорная",
                    "url": link,
                    "category": get_category(full_text, feed_info["source"]),
                    "source": feed_info["source"],
                    "published_at": "Сегодня",
                    "responses": "Открытый отклик",
                    "direct_contact": None,
                    "discovered_at": datetime.now(timezone.utc).isoformat()
                })
        except Exception:
            pass
    return tasks

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
        for msg in messages[-15:]:
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
                    published_str = dt.strftime("%d.%m %H:%M")
                    msg_iso = dt.isoformat()
                except Exception:
                    pass

            first_line = clean_text(text.split("\n")[0])
            title = (first_line[:95] + "...") if len(first_line) > 95 else first_line
            link = link_el.get("href")

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
                "category": get_category(text, "Telegram"),
                "source": f"TG (@{channel})",
                "published_at": published_str,
                "responses": "В ЛС",
                "direct_contact": direct_contact,
                "discovered_at": msg_iso
            })
    except Exception:
        pass
    return tasks

def load_existing_orders() -> list:
    if not os.path.exists("orders.json"):
        return []
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

if __name__ == "__main__":
    old_orders = load_existing_orders()
    new_scraped = []
    
    print("[*] Сбор задач...")
    new_scraped.extend(parse_rss_feeds())
    for ch in TG_CHANNELS[:15]:
        new_scraped.extend(parse_tg(ch))
        
    combined_orders = []
    seen_urls = set()
    for order in new_scraped + old_orders:
        url = order.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            combined_orders.append(order)
            
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(combined_orders[:100], f, ensure_ascii=False, indent=2)
        
    print(f"[+] Готово! В базе {len(combined_orders[:100])} заказов.")
