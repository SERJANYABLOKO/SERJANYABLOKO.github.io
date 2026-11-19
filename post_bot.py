"""Публикует контент в Telegram-канал @serjantdev.

Типы постов (чередуются автоматически):
  1) реальный заказ из orders.json,
  2) полезный разбор для разработчика/фрилансера,
  3) полезный сайт/инструмент,
  4) обновление проекта.

Секреты: TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID.
Состояние published_ids.json: какие заказы уже публиковались и сколько было постов.
"""

import html
import json
import os
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORDERS_FILE = BASE / "orders.json"
STATE_FILE = BASE / "posted_ids.json"
TOPICS_FILE = BASE / "topics.json"

TOPIC_NAMES = {
    "order": "Заказы",
    "tip": "Полезное",
    "tool": "Инструменты",
    "update": "Обновы",
}

PROMO_URL = "https://t.me/serjantyabloko"
PROMO = (
    "——\n"
    "🤖 Делаю Telegram-ботов, Mini Apps и сайты под ключ — "
    f"<a href=\"{PROMO_URL}\">написать мне</a>"
)

TIPS = [
    ("Как оценивать заказ на бота",
     "Считайте не только код. В стоимость закладывайте аналитику сценариев, тестирование на реальных пользователях и правки по их обратной связи. Один «простой» бот с нестандартными сценариями обычно занимает в 2–3 раза больше, чем кажется на старте."),
    ("Критерии приёмки — ваш лучший друг",
     "Перед стартом зафиксируйте письменно, что считается готовым: список сценариев, формат данных, срок ответа и число правок. Это экономит часы споров и превращает «доделай ещё чуть-чуть» в конкретную задачу."),
    ("Чек-лист перед сдачей Mini App",
     "Проверьте открытие внутри Telegram, а не только в браузере: заголовок, безопасные зоны, жесты, состояние при потере сети и повторное открытие по старой ссылке. Именно на этом чаще всего горят сдачи."),
    ("Где брать первые заказы",
     "Не ждите идеального биржевого профиля. Начните с 2–3 узких кейсов («бот записи», «лендинг для курсов»), выложите живые демо и откликайтесь с готовым решением под задачу, а не с общим «умею Python»."),
    ("Почему не стоит брать «микрофиксы» бесплатно",
     "Маленькая правка без предоплаты часто превращается в полноценный проект. Даже за 500 ₽ зафиксируйте объём и срок — так вы защищаете и своё время, и нервы заказчика."),
    ("Токены не живут в коде",
     "Любой публичный репозиторий — это открытый доступ к вашим ключам. Храните токены в переменных окружения и GitHub Secrets, а при подозрении на утечку сразу отзывайте их через настройки бота."),
    ("Как писать отклик, который читают",
     "Не копируйте ТЗ и не пишите «сделаю быстро». Напишите: 1) что именно вы сделаете, 2) из чего состоит результат, 3) срок и цена, 4) один вопрос по уточнению. Такие отклики отвечают в разы чаще."),
    ("Портфолио — это не скриншоты",
     "Показывайте задачу, ваше решение и цифры результата. Заказчик покупает не красивый интерфейс, а уверенность, чтозадача будет решён. Один разобранный кейс сильнее десяти картинок."),
]

TOOLS = [
    ("Regex101", "https://regex101.com",
     "Регулярные выражения с пояснением каждой части выражения и тестом на живых примерах. Экономит часы, когда нужно вытащить данные из текста."),
    ("Can I use", "https://caniuse.com",
     "Проверка поддержки HTML/CSS/JS-фич браузерами. Перед внедрением новой возможности сразу видно, где она сломается."),
    ("MDN Web Docs", "https://developer.mozilla.org/ru/",
     "Авторитетная документация по вебу на русском. Лучший источник, когда нужно понять, как именно работает API, а не просто скопировать пример."),
    ("Telegram Bot API", "https://core.telegram.org/bots/api",
     "Официальная документация по бот-API: методы, типы, обновления. Использую её при каждом новом боте."),
    ("Excalidraw", "https://excalidraw.com",
     "Быстрые схемы и вайрфреймы «от руки». Идеально, чтобы набросать архитектуру или экран и согласовать идею с заказчиком за минуту."),
    ("JSON Formatter", "https://jsonformatter.org",
     "Форматирует и проверяет JSON. Спасает, когда приходит «кривой» ответ API или нужно быстро посмотреть структуру данных."),
    ("StackBlitz", "https://stackblitz.com",
     "Онлайн-редактор, который запускает фронтенд прямо в браузере. Удобно показать живой прототип без установки всего окружения."),
    ("Figma Community", "https://www.figma.com/community",
     "Готовые UI-киты и компоненты. Хорошая отправная точка для макета, если нужно быстро собрать аккуратный интерфейс."),
    ("Carbon", "https://carbon.now.sh",
     "Красивые картинки с фрагментами кода. Полезно для постов и портфолио, когда нужно показать решение, а не просто описать его."),
    ("Python docs", "https://docs.python.org/3/",
     "Официальная документация Python. Перечитываю её даже после сотен проектов — всегда находишь более простой способ."),
]

UPDATES = [
    "Радар теперь показывает только реальные заказы: убраны дизайн-заказы, вакансии и реклама курсов.",
    "Источник заказов расширен: парсер собирает реальные проекты с FL.ru и открытых Telegram-каналов.",
    "В портфолио добавлены новые кейсы: Neon Studio, CyberShop Mini App, Order Radar и AI-Moderator.",
    "Страницы кейсов получили собственные дизайны: светлый магазин, зелёный терминал и синий центр управления.",
    "В радаре появились сортировка, метки «новое» и сводка по ботам, сайтам и скриптам.",
    "Запущен этот канал: полезные материалы и реальные заказы теперь приходят сюда автоматически.",
]


def e(value):
    return html.escape(str(value or ""), quote=True)


def telegram(method, payload):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_topics():
    if not TOPICS_FILE.exists():
        return {}
    try:
        return json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def ensure_topics():
    """Создаёт темы канала, если они включены. Возвращает {тип: thread_id}."""
    topics = load_topics()
    if all(k in topics for k in TOPIC_NAMES):
        return topics
    for key, name in TOPIC_NAMES.items():
        try:
            result = telegram("createForumTopic", {
                "chat_id": os.environ["TELEGRAM_CHANNEL_ID"],
                "name": name,
            })
            if result.get("ok"):
                topics[key] = result["result"]["message_thread_id"]
        except Exception as ex:
            print(f"Тема «{name}» не создана: {type(ex).__name__}. "
                  "Включите «Темы» в настройках канала и запустите снова.")
            break
    if topics:
        TOPICS_FILE.write_text(json.dumps(topics, ensure_ascii=False, indent=2), encoding="utf-8")
    return topics


def load_state():
    if not STATE_FILE.exists():
        return {"posted_orders": [], "total_posts": 0, "last_type": None}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    if isinstance(data, list):
        return {"posted_orders": data, "total_posts": len(data), "last_type": None}
    data.setdefault("posted_orders", [])
    data.setdefault("total_posts", len(data["posted_orders"]))
    data.setdefault("last_type", None)
    return data


def order_post(order, tip):
    return (
        "⚡ #заказы <b>Заказ для разработчиков</b>\n\n"
        f"📌 {e(order.get('title'))}\n"
        f"💰 {e(order.get('price'))}\n"
        f"📡 {e(order.get('source'))}\n"
        f"🔗 <a href=\"{e(order.get('url'))}\">Открыть объявление</a>\n\n"
        f"💡 <b>Кстати:</b> {e(tip[0])}. {e(tip[1])}\n\n"
        + PROMO
    )


def tip_post(tip):
    return (
        "🧠 #полезное <b>Полезное разработчику</b>\n\n"
        f"<b>{e(tip[0])}</b>\n\n"
        f"{e(tip[1])}\n\n"
        + PROMO
    )


def tool_post(tool):
    return (
        "🔧 #инструменты <b>Полезный сайт дня</b>\n\n"
        f"<b>{e(tool[0])}</b> — {e(tool[2])}\n"
        f"🔗 {e(tool[1])}\n\n"
        + PROMO
    )


def update_post(update):
    return (
        "🆕 #обновы <b>Что нового</b>\n\n"
        f"• {e(update)}\n\n"
        "Сайт и радар продолжают обновляться — следите за каналом.\n\n"
        + PROMO
    )


def main():
    missing = [n for n in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID") if not os.environ.get(n)]
    if missing:
        raise SystemExit("Не заданы секреты: " + ", ".join(missing))

    state = load_state()
    posted = set(state["posted_orders"])
    orders = json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
    fresh = [o for o in orders if o.get("url") and o["url"] not in posted]

    types = ["order", "tip", "tool", "update"]
    kind = types[state["total_posts"] % len(types)]
    if kind == "order" and not fresh:
        kind = "tip"

    tip = TIPS[state["total_posts"] % len(TIPS)]
    tool = TOOLS[state["total_posts"] % len(TOOLS)]
    update = UPDATES[state["total_posts"] % len(UPDATES)]

    if kind == "order":
        order = fresh[0]
        text = order_post(order, tip)
    elif kind == "tip":
        text = tip_post(tip)
    elif kind == "tool":
        text = tool_post(tool)
    else:
        text = update_post(update)

    topics = ensure_topics()
    payload = {
        "chat_id": os.environ["TELEGRAM_CHANNEL_ID"],
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if kind in topics:
        payload["message_thread_id"] = topics[kind]

    result = telegram("sendMessage", payload)
    if not result.get("ok"):
        raise SystemExit(f"Telegram отклонил запрос: {result}")

    if kind == "order":
        posted.add(order["url"])
        state["posted_orders"] = sorted(posted)
    state["total_posts"] += 1
    state["last_type"] = kind
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Опубликовано:", kind)


if __name__ == "__main__":
    main()
