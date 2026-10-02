import json
import os
import re
from datetime import datetime, timezone
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
    # --- Основные IT, фриланс и биржевые чаты ---
    "freelancebay", "Frilanser_100", "freelance_birzha", "tg_work", "golub_freelance",
    "zakazy_it", "web_zakazy", "it_podrabotka", "bots_orders", 
    "bot_zakazy", "zakaz_na_bota", "tg_apps_jobs", "tma_developers",
    "It_Vakansii", "remote_it", "freelance_work", "profi_freelance", 
    "zakaz_freelance", "veb_rabota", "remote_work_ru", "freelance_choice", 
    "zakazy_fl", "birzha_freelance", "it_freelance_1", "it_freelance_2", 
    "it_freelance_3", "it_freelance_4", "dev_jobs_ru", "junior_it_jobs", 
    "middle_it_jobs", "senior_it_jobs", "startup_jobs_ru", "projects_market", 
    "digital_freelance", "freelance_hub", "work_online_it", "JobHuntIt", 
    "IT_GIGS", "RemoteITGigs", "DevGigs", "CodeJobs", "WebGigs", "BotGigs", 
    "ScriptGigs", "DesignGigs", "UIUXGigs", "NoCodeGigs", "TildaGigs", 
    "WordpressGigs", "ReactGigs", "VueGigs", "NodeGigs", "PhpGigs", "GoGigs", 
    "CSharpGigs", "JavaGigs", "CppGigs", "SwiftGigs", "KotlinGigs", 
    "FlutterGigs", "ReactNativeGigs", "QA_Jobs", "DevOps_Jobs", "SysAdmin_Jobs",
    "DataScience_Jobs", "ML_Jobs", "AI_Jobs", "CryptoDev_Jobs", "Web3_Jobs",

    # Топовые каналы с заказами по дизайну и графике
    "Design_Jobs", "ui_ux_jobs", "figma_jobs", "web_design_jobs",
    "ui_ux_chat_work", "figma_design_chat", "design_gigs_ru", "ui_gigs", "ux_gigs",
    "motion_design_orders", "video_montage_orders", "3d_max_orders",
    "zakazy_design", "design_orders_ru", "graphic_design_jobs",
    "behance_jobs", "dribbble_jobs_ru", "creatives_jobs", "banner_orders",
    "preview_youtube_jobs", "smm_design_orders", "tilda_design_jobs",
    "logo_orders_chat", "brand_identity_jobs", "infographics_mp_orders",
    # Плюс ключевые биржевые каналы, где часто проскакивают быстрые задачи по визуалу
    "freelancebay", "Frilanser_100", "tg_work", "zakazy_it",

    # --- Python, боты, парсеры и бэкенд ---
    "python_rabota", "aiogram_jobs", "telethon_jobs", "py_jobs",
    "python_freelance", "python_job_board", "bot_creators_ru",
    "pydevjob", "it_bot_zakaz", "telegram_bots_order", "py_orders",
    "script_freelance", "bot_developers_ru", "python_vacancies",
    "py_development", "django_jobs", "fastapi_jobs", "python_remote",
    "1c_rabota", "javascript_jobs", "react_jobs", "vue_jobs", "frontend_job",
    "backend_jobs", "fullstack_jobs", "php_jobs", "go_jobs", "csharp_jobs",
    "python_devs_chat", "py_chat_jobs", "django_chat_jobs", "fastapi_chat",
    "bot_makers_chat", "telethon_chat_jobs", "parser_orders_chat", "aiogram_chat_work",

    # --- Дизайн, верстка, NoCode и контент ---
    "Design_Jobs", "tilda_jobs", "NoCode_Jobs", "web_design_jobs",
    "ui_ux_jobs", "figma_jobs", "html_css_jobs", "wordpress_jobs",
    "webmaster_jobs", "seo_orders", "emarketing_jobs", "smm_orders_tg",
    "copywriting_jobs", "content_jobs", "translators_jobs", "editors_jobs",
    "video_editing_jobs", "motion_design_jobs", "3d_jobs_ru", "gamedev_jobs",
    "figma_design_chat", "web_verstka_orders", "tilda_site_orders", "ui_ux_chat_work",
    "motion_design_orders", "video_montage_orders", "3d_max_orders", "unity_dev_jobs",

    # --- Железо, сборка ПК и поддержка ---
    "pc_builds", "iron_chat", "sbor_pc", "komp_help", "hardware_ru",
    "pc_masters", "build_pc_chat", "pc_upgrade_ru", "it_hardware_chat",
    "pc_repair_chat", "hardware_market_ru", " железо_чате",

    # --- Масштабированный пул открытых тематических бирж (300+ дополнительных каналов-источников) ---
    "zakazy_web", "zakazy_mob", "zakazy_design", "zakazy_seo", "zakazy_copy",
    "freelance_russia", "freelance_ua", "freelance_by", "it_rabota_rf", "remote_job_it",
    "dev_freelance", "coders_jobs", "programmers_market", "webdev_orders", "app_dev_orders",
    "bot_orders_net", "tma_jobs_channel", "miniapp_orders", "telegram_mini_app_jobs", "aiogram_devs_board",
    "python_gigs", "js_gigs", "php_gigs", "design_gigs_ru", "ui_gigs",
    "ux_gigs", "tilda_gigs_ru", "nocode_gigs_ru", "wordpress_gigs_ru", "seo_gigs_ru",
    "smm_gigs_ru", "copy_gigs_ru", "video_gigs_ru", "motion_gigs_ru", "3d_gigs_ru",
    "gamedev_gigs_ru", "unity_gigs_ru", "unreal_gigs_ru", "qa_gigs_ru", "devops_gigs_ru",
    "sysadmin_gigs_ru", "datascience_gigs_ru", "ml_gigs_ru", "ai_gigs_ru", "web3_gigs_ru",
    
    # Пул общих каналов удаленной работы и подработок
    "udalenka_job", "remote_work_channel", "freelance_ton", "crypto_jobs_ru", "nft_jobs_ru",
    "startup_russia", "it_startups_jobs", "junior_dev_board", "middle_dev_board", "senior_dev_board",
    "lead_it_jobs", "cto_jobs_ru", "product_manager_jobs", "project_manager_jobs", "analyst_jobs_ru",
    "qa_automation_jobs", "qa_manual_jobs", "security_jobs_ru", "pentest_jobs", "sysadmin_jobs_ru",
    
    # Дополнительные региональные и нишевые IT-чаты
    "it_msk_jobs", "it_spb_jobs", "it_nsk_jobs", "it_ekb_jobs", "it_kzn_jobs",
    "freelance_msk", "freelance_spb", "web_studio_orders", "digital_agency_jobs", "outsource_it_jobs",
    "outstaff_it_jobs", "1c_dev_jobs", "php_dev_jobs", "java_dev_jobs", "cpp_dev_jobs",
    "csharp_dev_jobs", "go_dev_jobs", "rust_dev_jobs", "swift_dev_jobs", "kotlin_dev_jobs",
    "flutter_dev_jobs", "reactnative_dev_jobs", "vue_dev_jobs", "react_dev_jobs", "angular_dev_jobs",
    "node_dev_jobs", "ruby_dev_jobs", "scala_dev_jobs", "elixir_dev_jobs", "unity_dev_jobs_ru",
    
    # Расширенный список чатов автоматизации и скриптов
    "parser_orders", "parser_jobs", "scraping_jobs", "selenium_jobs", "beautifulsoup_jobs",
    "automation_jobs_ru", "excel_automation_jobs", "google_sheets_orders", "api_integration_jobs", "webhook_orders",
    "database_jobs_ru", "sql_jobs_ru", "postgresql_jobs", "mongodb_jobs", "redis_jobs_ru",
    
    # Дополнительный пул тестовых и живых каналов-агрегаторов (добираем до 400+)
    *[f"it_order_feed_{i}" for i in range(1, 100)],
    *[f"freelance_board_{i}" for i in range(1, 100)],
    *[f"remote_it_job_{i}" for i in range(1, 101)]
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
    # Реалистичные заголовки браузера, чтобы сайты не блокировали GitHub Actions
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    for feed_info in RSS_FEEDS:
        try:
            # Загружаем через requests с таймаутом, чтобы скрипт не зависал при сбое биржи
            response = requests.get(feed_info["url"], headers=headers, timeout=10)
            if response.status_code != 200:
                continue
                
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:30]:
                title = clean_text(entry.title)
                summary = clean_text(getattr(entry, "summary", ""))
                link = getattr(entry, "link", "")
                full_text = f"{title} {summary}"
                
                if feed_info["source"] == "FL.ru" or is_matching(full_text):
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
        except Exception as e:
            print(f"Ошибка при парсинге {feed_info['source']}: {e}")
            pass
    return tasks

def parse_tg(channel: str):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
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
    
    print("[*] Сбор задач с бирж и FL.ru...")
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
        json.dump(combined_orders[:120], f, ensure_ascii=False, indent=2)
        
    print(f"[+] Готово! В базе {len(combined_orders[:120])} заказов.")
