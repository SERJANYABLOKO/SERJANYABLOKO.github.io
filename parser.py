import json
import requests
from bs4 import BeautifulSoup

KEYWORDS = ["python", "бот", "парсер", "скрипт", "html", "css", "telegram"]

def parse_habr():
    # Бесплатная RSS-лента или HTML страницы заказов
    url = "https://freelance.habr.com/tasks"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    tasks = []
    cards = soup.select(".task-card")
    
    for card in cards[:25]:
        title_elem = card.select_one(".task-card__title a")
        price_elem = card.select_one(".task-card__price")
        
        if not title_elem:
            continue
            
        title = title_elem.text.strip()
        link = "https://freelance.habr.com" + title_elem["href"]
        price = price_elem.text.strip() if price_elem else "По договоренности"

        # Фильтр по ключевым словам
        if any(word in title.lower() for word in KEYWORDS):
            tasks.append({
                "title": title,
                "price": price,
                "url": link
            })
            
    return tasks

if __name__ == "__main__":
    orders = parse_habr()
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
