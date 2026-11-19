"""Публикует реальные заказы из orders.json в Telegram-канал.

Токен бота и ID канала берутся из переменных окружения (GitHub Secrets):
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

В канале публикуется полезный пост для разработчиков + ненавязчивая подпись
с ссылкой на автора. Один заказ за запуск, каждый заказ — только один раз.
"""

import html
import json
import os
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORDERS_FILE = BASE / "orders.json"
STATE_FILE = BASE / "posted_ids.json"

PROMO_URL = "https://t.me/serjantyabloko"

TIPS = [
    "Перед откликом уточните критерии приёмки. Без них даже простой заказ превращается в бесконечные правки — зафиксируйте их в первом же сообщении.",
    "Для Telegram-бота закладывайте отдельным пунктом тестирование на реальных пользователях: сценарии «пустой чат», «отмена» и «старая ссылка» ловят больше багов, чем юнит-тесты.",
    "Не беритесь за правку «за 500 ₽» без предоплаты: мелкие задачи часто съедают времени больше, чем средний проект.",
    "В портфолио показывайте не скриншоты, а задачу → решение → результат. Заказчику важно видеть, как вы мыслите.",
    "Для Mini Apps проверяйте поведение именно внутри Telegram WebApp, а не только в браузере: отличаются заголовок, безопасные зоны и жесты.",
    "Токены и ключи храните в переменных окружения, а не в коде. Публичный репозиторий быстро превращает токен в уязвимость.",
    "Оценивая заказ, сразу уточните про доступы к API и хостингу. Без них сроки «вчера» превращаются в неделю ожидания.",
    "Если просят «сделать как у конкурента», попросите 2–3 ссылки и уточните, что именно нужно повторить: UX, логику или только внешний вид.",
]


def e(value):
    return html.escape(str(value or ""), quote=True)


def telegram(method, payload):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def load_state():
    if not STATE_FILE.exists():
        return []
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def main():
    required = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit("Не заданы секреты: " + ", ".join(missing))

    orders = json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
    posted = set(load_state())

    fresh = [o for o in orders if o.get("url") and o["url"] not in posted]
    if not fresh:
        print("Новых заказов для публикации нет.")
        return

    order = fresh[0]
    tip = TIPS[len(posted) % len(TIPS)]

    text = (
        "⚡ <b>Заказ для разработчиков</b>\n\n"
        f"📌 {e(order.get('title'))}\n"
        f"💰 {e(order.get('price'))}\n"
        f"📡 {e(order.get('source'))}\n"
        f"🔗 <a href=\"{e(order.get('url'))}\">Открыть объявление</a>\n\n"
        f"💡 <b>Полезное:</b> {e(tip)}\n\n"
        "——\n"
        "🤖 Делаю Telegram-ботов, Mini Apps и сайты под ключ — "
        f"<a href=\"{PROMO_URL}\">написать мне</a>"
    )

    result = telegram("sendMessage", {
        "chat_id": os.environ["TELEGRAM_CHANNEL_ID"],
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })

    if not result.get("ok"):
        raise SystemExit(f"Telegram отклонил запрос: {result}")

    posted.add(order["url"])
    STATE_FILE.write_text(
        json.dumps(sorted(posted), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Опубликовано:", order["url"])


if __name__ == "__main__":
    main()
