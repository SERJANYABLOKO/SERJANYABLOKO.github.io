import json
import re
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. СПИСОК ПРОВЕРЕННЫХ TELEGRAM-КАНАЛОВ
# ==========================================
TG_CHANNELS = [
    "freelancetavern",
    "digitaltender",
    "forfreelance",
    "it_freelance_zakaz",
    "zakazy_it",
    "work_in_it",
    "job_python"
]

# ==========================================
# 2. ФИЛЬТРЫ ТЕХНОЛОГИЙ И СТОП-СЛОВА
# ==========================================
TARGET_KEYWORDS = [
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", "бота",
    "mini app", "мини апп", "tma", "webapp", "web app",
    "верстка", "сверстать", "html", "css", "landing", "лендинг", 
    "сайт визитка", "простой сайт", "статический сайт", "поправить верстку"
]

STOP_WORDS = [
    # Запрещаем любые платные биржи и спам Kwork
    "kwork", "кворк", "fl.ru", "freelance.ru",
    # Неподходящие технологии
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
    """Проверяет, что дата — сегодня или вчера (не старше 48 часов)."""
    now = datetime.now(timezone.utc)
    delta = now - dt
    return delta.total_seconds() <= 48 * 3600

# ==========================================
# 3. СБОР С ХАБР ФРИЛАНС
# ==========================================
def parse_habr():
    url = "https://freelance.habr.com/tasks"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select(".task-card")
        
        for card in cards:
            title_el = card.select_one(".task-card__title a")
            if not title_el:
                continue
                
            title = clean_text(title_el.text)
            if not is_matching_skills(title):
                continue
            
            # 1. ПРОВЕРКА ОТКЛИКОВ (максимум 5)
            responses_el = card.select_one(".task-params__item_responses")
            responses_count = 0
            responses_text = "0 откликов"
            
            if responses_el:
                responses_text = clean_text(responses_el.text)
                digits = re.findall(r"\d+", responses_text)
                if digits:
                    responses_count = int(digits[0])
            
            if responses_count > 5:
                continue  # Пропускаем, если откликов больше 5

            # 2. ПРОВЕРКА ДАТЫ (только сегодня и вчера)
            date_el = card.select_one(".task-params__item_published")
            published_text = clean_text(date_el.text).lower() if date_el else ""
            
            # Хабр пишет: "сегодня", "вчера", или дату вроде "15 сентября"
            if not any(word in published_text for word in ["сегодня", "вчера", "назад", "минут", "час"]):
                continue  # Старый заказ

            price_el = card.select_one(".task-card__price")
            price = clean_text(price_el.text) if price_el else "Договорная"
            link = "https://freelance.habr.com" + title_el.get("href", "")
            cat = "Telegram" if any(k in title.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"

            tasks.append({
                "title": title,
                "price": price,
                "url": link,
                "category": cat,
                "source": "Хабр Фриланс",
                "published_at": published_text.capitalize(),
                "responses": f"{responses_count} откл.",
                "direct_contact": None
            })
    except Exception as e:
        print(f"[!] Ошибка Хабра: {e}")
        
    return tasks

# ==========================================
# 4. СБОР ИЗ TELEGRAM (БЕЗ KWORK И СТАРЬЯ)
# ==========================================
def parse_tg(channel: str):
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tasks = []
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        messages = soup.select(".tgme_widget_message")
        
        for msg in messages[-20:]:
            text_el = msg.select_one(".tgme_widget_message_text")
            date_el = msg.select_one(".tgme_widget_message_date time")
            link_el = msg.select_one(".tgme_widget_message_date")
            
            if not text_el or not link_el:
                continue
                
            text = text_el.text.strip()
            
            # Фильтр навыков и стоп-слов (включая Kwork)
            if not is_matching_skills(text):
                continue

            # ПРОВЕРКА ДАТЫ: только сегодня или вчера
            published_str = "Недавно"
            if date_el and date_el.get("datetime"):
                raw_time = date_el.get("datetime")
                try:
                    msg_dt = datetime.fromisoformat(raw_time)
                    if not is_fresh_date(msg_dt):
                        continue  # Старше вчерашнего дня — пропускаем
                    published_str = msg_dt.strftime("%d.%m %H:%M")
                except Exception:
                    pass

            first_line = clean_text(text.split("\n")[0])
            title = (first_line[:90] + "...") if len(first_line) > 90 else first_line
            link = link_el.get("href")

            # Поиск прямого контакта @username
            direct_contact = None
            found_usernames = re.findall(r"@[a-zA-Z0-9_]{5,}", text)
            if found_usernames:
                # Отсекаем юзернейм самого канала
                valid_usernames = [u for u in found_usernames if channel.lower() not in u.lower()]
                if valid_usernames:
                    direct_contact = valid_usernames[0]

            cat = "Telegram" if any(k in text.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"

            tasks.append({
                "title": title,
                "price": "В описании",
                "url": link,
                "category": cat,
                "source": f"@{channel}",
                "published_at": published_str,
                "responses": "Прямой контакт",
                "direct_contact": direct_contact
            })
    except Exception as e:
        print(f"[!] Ошибка @{channel}: {e}")
        
    return tasks

# ==========================================
# 5. ОСНОВНОЙ ЗАПУСК
# ==========================================
if __name__ == "__main__":
    all_orders = []
    
    # 1. Telegram
    for ch in TG_CHANNELS:
        all_orders.extend(parse_tg(ch))
        
    # 2. Хабр Фриланс
    all_orders.extend(parse_habr())
    
    # 3. Удаление дубликатов по URL
    unique_orders = []
    seen_urls = set()
    for o in all_orders:
        if o["url"] not in seen_urls:
            seen_urls.add(o["url"])
            unique_orders.append(o)
            
    # 4. Сохранение
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(unique_orders, f, ensure_ascii=False, indent=2)
        
    print(f"Готово! Найдено {len(unique_orders)} свежих заказов (<= 5 откликов, сегодня/вчера).")
