import json
import requests
from bs4 import BeautifulSoup

# 1. ЧТО МЫ ИЩЕМ (хотя бы одно совпадение обязательно)
TARGET_KEYWORDS = [
    # Telegram боты и мини-приложения
    "тг бот", "телеграм бот", "telegram бот", "тг-бот", 
    "mini app", "мини апп", "tma", "webapp", "web app",
    
    # Сайты и верстка
    "верстка", "сверстать", "html", "css", "landing", "лендинг", 
    "сайт визитка", "простой сайт", "статический сайт", "правки на сайте"
]

# 2. ЧТО МЫ СТРОГО ОТСЕКАЕМ (если есть хоть одно слово — заказ пропускается)
STOP_WORDS = [
    # Сложные или неподходящие стеки
    "1с", "1c", "bitrix", "битрикс", "wordpress",
    "senior", "lead", "teamlead",
    "flutter", "react native", "swift", "kotlin", "ios", "android",
    "c#", "c++", ".net", "java ", "golang", "go ", "rust", "php"
]

def is_matching_order(text: str) -> bool:
    """Проверяет текст заказа на соответствие твоим навыкам."""
    text_lower = text.lower()
    
    # Если есть хотя бы одно стоп-слово — сразу отказ
    if any(stop in text_lower for stop in STOP_WORDS):
        return False
        
    # Проверяем наличие целевых слов
    return any(keyword in text_lower for keyword in TARGET_KEYWORDS)

def parse_habr():
    url = "https://freelance.habr.com/tasks"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    matched_tasks = []
    cards = soup.select(".task-card")
    
    for card in cards:
        title_elem = card.select_one(".task-card__title a")
        price_elem = card.select_one(".task-card__price")
        
        if not title_elem:
            continue
            
        title = title_elem.text.strip()
        link = "https://freelance.habr.com" + title_elem["href"]
        price = price_elem.text.strip() if price_elem else "По договоренности"
        
        # Фильтруем заказ
        if is_matching_order(title):
            # Присваиваем бейдж для красоты на сайте
            category = "Telegram" if any(k in title.lower() for k in ["бот", "app", "tma"]) else "Веб-сайт"
            
            matched_tasks.append({
                "title": title,
                "price": price,
                "url": link,
                "category": category
            })
            
    return matched_tasks

if __name__ == "__main__":
    orders = parse_habr()
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    print(f"Найдено подходящих заказов: {len(orders)}")
