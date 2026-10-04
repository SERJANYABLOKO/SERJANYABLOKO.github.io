import json
import os
import re
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup
import feedparser

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
        "url": "https://www.fl.ru/rss/all.rss?specs=1",
        "source": "FL.ru"
    }
]

TG_CHANNELS = [
    "freelancebay", "Frilanser_100", "freelance_birzha", "tg_work", "golub_freelance",
    "zakazy_it", "web_zakazy", "it_podrabotka", "bots_orders", "bot_zakazy",
    "zakaz_na_bota", "tg_apps_jobs", "tma_developers", "It_Vakansii", "remote_it",
    "freelance_work", "profi_freelance", "zakaz_freelance", "veb_rabota",
    "Design_Jobs", "ui_ux_jobs", "figma_jobs", "web_design_jobs", "ui_ux_chat_work",
    "figma_design_chat", "design_gigs_ru", "ui_gigs", "ux_gigs", "motion_design_orders",
    "video_montage_orders", "3d_max_orders", "zakazy_design", "design_orders_ru",
    "graphic_design_jobs", "behance_jobs", "dribbble_jobs_ru", "creatives_jobs",
    "banner_orders", "preview_youtube_jobs", "smm_design_orders", "tilda_design_jobs",
    "logo_orders_chat", "brand_identity_jobs", "infographics_mp_orders",
    "python_rabota", "aiogram_jobs", "telethon_jobs", "py_jobs", "python_freelance",
    "python_job_board", "bot_creators_ru", "pydevjob", "it_bot_zakaz", "telegram_bots_order",
    "py_orders", "script_freelance", "bot_developers_ru", "python_vacancies", "py_development",
    "django_jobs", "fastapi_jobs", "python_remote", "javascript_jobs", "react_jobs", "vue_jobs",
    "frontend_job", "backend_jobs", "fullstack_jobs", "php_jobs", "go_jobs", "csharp_jobs",
    "bot_makers_chat", "aiogram_chat_work", "parser_orders_chat", "miniapp_orders",
    "tilda_jobs", "NoCode_Jobs", "wordpress_jobs", "webmaster_jobs", "seo_orders",
    "emarketing_jobs", "smm_orders_tg", "web_verstka_orders", "tilda_site_orders",
    "pc_builds", "iron_chat", "sbor_pc", "komp_help", "hardware_ru", "pc_masters",
    "build_pc_chat", "pc_upgrade_ru", "it_hardware_chat", "vps_hosting_chat", "sysadmin_jobs"
]

# Стоп-слова и корни для полного исключения штата, офиса и постоянной занятости
STOP_STEMS = [
    "штат", "офис", "фуллтайм", "full-time", "тк рф", "оформлен", 
    "постоян", "долгосроч", "месяц", "оклад", "зарплат", "гибрид"
]

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_matching(text: str) -> bool:
    text_lower = text.lower()
    for stem in STOP_STEMS:
        if stem in text_lower:
            return False
    return True

def get_category(text: str, source: str) -> str:
    if "FL.ru" in source:
        return "FL.ru"
    text_lower = text.lower()
    if any(k in text_lower for k in ["сборка", "апгрейд", "пк", "компьютер", "детал"]):
        return "Железо / ПК"
    elif any(k in text_lower for k in ["дизайн", "figma", "фигма", "ui/ux", "макет", "прототип", "баннер", "аватар"]):
        return "Дизайн"
    elif any(k in text_lower for k in ["бот", "app", "tma", "aiogram", "mini app"]):
        return "Telegram"
    elif any(k in text_lower for k in ["парсер", "спарсить", "скрипт"]):
        return "Парсеры"
    return "Веб-сайт"

def parse_rss_feeds():
    tasks = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    for feed_info in RSS_FEEDS:
        try:
            response = requests.get(feed_info["url"], headers=headers, timeout=10)
            if response.status_code != 200: continue
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:30]:
                title = clean_text(entry.title)
                summary = clean_text(getattr(entry, "summary", ""))
                link = getattr(entry, "link", "")
                full_text = f"{title} {summary}"

                pub_date = datetime.now(timezone.utc)
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try: pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except Exception: pass

                if pub_date >= week_ago and (feed_info["source"] == "FL.ru" or is_matching(full_text)):
                    tasks.append({
                        "title": title[:95] + "..." if len(title) > 95 else title,
                        "price": "Договорная",
                        "url": link,
                        "category": get_category(full_text, feed_info["source"]),
                        "source": feed_info["source"],
                        "published_at": pub_date.strftime("%d.%m %H:%M"),
                        "responses": "Открытый отклик",
                        "direct_contact": None,
                        "discovered_at": pub_date.isoformat()
                    })
        except Exception: pass
    return tasks

def parse_tg(channel: str):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    tasks = []
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200: return tasks
        soup = BeautifulSoup(res.text, "html.parser")
        messages = soup.select(".tgme_widget_message")
        for msg in messages[-15:]:
            text_el = msg.select_one(".tgme_widget_message_text")
            date_el = msg.select_one(".tgme_widget_message_date time")
            link_el = msg.select_one(".tgme_widget_message_date")
            if not text_el or not link_el: continue

            msg_dt = datetime.now(timezone.utc)
            if date_el and date_el.get("datetime"):
                try:
                    dt = datetime.fromisoformat(date_el.get("datetime"))
                    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                    msg_dt = dt
                except Exception: pass

            if msg_dt < week_ago: continue
            text = text_el.text.strip()
            if not is_matching(text): continue

            published_str = msg_dt.strftime("%d.%m %H:%M")
            first_line = clean_text(text.split("\n")[0])
            title = (first_line[:95] + "...") if len(first_line) > 95 else first_line
            link = link_el.get("href")

            direct_contact = None
            found_usernames = re.findall(r"@[a-zA-Z0-9_]{4,}", text)
            if found_usernames:
                valid_usernames = [u for u in found_usernames if channel.lower() not in u.lower() and "bot" not in u.lower()]
                if valid_usernames: direct_contact = valid_usernames[0]

            tasks.append({
                "title": title,
                "price": "В описании",
                "url": link,
                "category": get_category(text, "Telegram"),
                "source": f"TG (@{channel})",
                "published_at": published_str,
                "responses": "В ЛС",
                "direct_contact": direct_contact,
                "discovered_at": msg_dt.isoformat()
            })
    except Exception: pass
    return tasks

def load_existing_orders() -> list:
    if not os.path.exists("orders.json"): return []
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception: return []

if __name__ == "__main__":
    old_orders = load_existing_orders()
    new_scraped = []
    
    print("[*] Сканирование заказов за неделю с фильтрацией стоп-слов...")
    new_scraped.extend(parse_rss_feeds())
    for ch in TG_CHANNELS:
        new_scraped.extend(parse_tg(ch))
        
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    combined_orders = []
    seen_urls = set()

    for order in new_scraped + old_orders:
        url = order.get("url")
        discovered_at = order.get("discovered_at")
        is_fresh = True
        if discovered_at:
            try:
                order_date = datetime.fromisoformat(discovered_at)
                if order_date.tzinfo is None: order_date = order_date.replace(tzinfo=timezone.utc)
                if order_date < week_ago: is_fresh = False
            except Exception: pass

        if is_fresh and url and url not in seen_urls:
            seen_urls.add(url)
            combined_orders.append(order)
            
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(combined_orders[:150], f, ensure_ascii=False, indent=2)
        
    print(f"[+] Успешно! Чистых актуальных заказов: {len(combined_orders[:150])}")
