import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. ТОЛЬКО КАНАЛЫ С ФРИЛАНС-ЗАКАЗАМИ И ПОДРАБОТКОЙ
# (Убраны каналы поиска сотрудников в штат и IT-агентств)
# ==========================================
TG_CHANNELS = [
    # Заказы на ботов и Python
    "zakazy_it",
    "web_zakazy",
    "it_podrabotka",
    "bots_orders",
    "bot_zakazy",
    "zakaz_na_bota",
    "tg_apps_jobs",
    "tma_developers",
    
    # Фриланс по веб-дизайну и сайтам
    "design_zakaz",
    "figma_orders",
    "design_podrabotka",
    "freelancedesign",
    "webdesign_jobs",
    "freelance_design_ru",
    
    # Открытые ленты фриланс-бирж (только проекты, не вакансии)
    "freelansim_ru",
    "freelancehunt_orders",
    "forfreelance",
    "it_freelance_zakaz",
    "freelance_orders_ru",
    "pomogator_freelance",
    "verstka_jobs"
]

# ==========================================
# 2. МАРКЕРЫ ЗАКАЗА / ПРОЕКТНОЙ РАБОТЫ
# ==========================================
PROJECT_TRIGGERS = [
    "нужен", "нужно", "требуется", "ищу", "ищем", "заказ", "задача",
    "проект", "подработка", "сделать", "разработать", "написать",
    "сверстать", "доработать", "починить", "бюджет", "оплата", "тз"
]

# ==========================================
# 3. ЦЕЛЕВЫЕ НАПРАВЛЕНИЯ
# ==========================================
SKILL_KEYWORDS = [
    # Telegram боты и TMA
    "бот", "боты", "бота", "боту", "тг бот", "тг-бот", "telegram bot",
    "aiogram", "telethon", "pyrogram", "mini app", "tma", "webapp",
    
    # Сайты и верстка
    "сайт", "сайта", "сайты", "верстка", "сверстать", "html", "css",
    "landing", "лендинг", "одностраничник", "поправить верстку",
    
    # Веб-дизайн и Figma
    "дизайн", "дизайна", "дизайнер", "ui/ux", "ui-ux", "figma", "фигма",
    "макет", "прототип", "редизайн сайта", "дизайн сайта", "дизайн лендинга",
    
    # Парсеры и скрипты
    "парсер", "парсить", "спарсить", "скрипт", "автоматизация"
]

# ==========================================
# 4. СТОП-СЛОВА (ШТАТНЫЕ ВАКАНСИИ, SMM, АРБИТРАЖ, ТЕСТЕРЫ)
# ==========================================
STOP_WORDS = [
    # Корпоративный найм и штатная работа
    "traffic manager", "media buyer", "lead", "teamlead",
    "qa automation", "qa engineer", "тестировщик", "manual qa", "aqa",
    "опыт работы от", "опыт от 3", "опыт от 2", "опыт от 5",
    "оформление по тк", "в штат", "полная занятость", "фуллтайм", "fulltime",
    "испытательный срок", "оклад", "зарплата от", "зп от",
    "middle+", "senior",
    
    # Маркетинг, арбитраж, трафик, SMM
    "google ads", "meta ads", "facebook ads", "арбитраж", "баер",
    "smm", "смм", "таргет", "таргетолог", "контент", "копирайтер",
    "рилс", "reels", "shorts", "монтажер", "инвайтинг", "прогрев",
    "карточек wildberries", "карточек ozon", "вайлдберриз", "wb",
    
    # Сложный или неподходящий стек
    "1с", "1c", "bitrix", "битрикс", "flutter", "react native",
    "swift", "kotlin", "ios", "android", "c#", "c++", ".net", "java", "golang", "rust"
]

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_valid_freelance_order(text: str) -> bool:
    text_lower = text.lower()
    
    # 1. Отсеиваем любые совпадения по стоп-словам (вакансии, арбитраж, фуллтайм)
    for stop in STOP_WORDS:
        if stop in text_lower:
            return False
            
    # 2. Проверяем, что это реальная задача/заказ, а не просто статья или опрос
    has_trigger = any(t in text_lower for t in PROJECT_TRIGGERS)
    if not has_trigger:
        return False
        
    # 3. Проверяем наличие целевого стека (бот, сайт, дизайн, парсер)
    return any(k in text_lower for k in SKILL_KEYWORDS)

def is_fresh_date(dt: datetime) -> bool:
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() <= 48 * 3600

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
# 5. СБОР С ХАБР ФРИЛАНСА (ПРОЕКТЫ ДО 10 ОТКЛИКОВ)
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
            if not is_valid_freelance_order(title):
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
# 6. СБОР ИЗ TELEGRAM-КАНАЛОВ ФРИЛАНСА
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
            
            # Строгая фильтрация от штатных вакансий и медиабаеров
            if not is_valid_freelance_order(text):
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
# 7. ХРАНЕНИЕ И ОЧИСТКА СТАРЫХ ВАКАНСИЙ
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
        # Автоматически удаляем старый мусор и вакансии из orders.json
        if not is_valid_freelance_order(order.get("title", "")):
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
    print(f"[*] Сбор заказов с проверенных каналов ({len(TG_CHANNELS)})...")
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
        
    print(f"[+] Готово! В базе {len(final_orders)} реальных заказов под твои навыки.")
