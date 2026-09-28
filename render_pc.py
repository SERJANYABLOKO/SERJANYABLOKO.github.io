import time
import sys

# Настройки кодировки для нормального вывода в консоль
if sys.platform.startswith('win'):
  import os

  os.system('chcp 65001 >nul')

# Ключевые слова для поиска клиентов на покупку ПК, сборку или апгрейд
KEYWORDS = [
    "сборка пк",
    "собрать пк",
    "подбор комплектующих",
    "купить компьютер",
    "апгрейд",
    "видеокарта",
    "посоветуйте сборку",
]


def check_new_leads():
  print("=" * 50)
  print("🚀 render_pc.py запущен: мониторинг клиентов активирован...")
  print("=" * 50)

  # Имитация поступающих данных с бирж / TG каналов
  # (Здесь в реальном проекте вы подключаете BeautifulSoup для сайтов или Telethon для Telegram)
  mock_feed = [
      {
          "text": (
              "Ищу спеца, кто поможет собрать игровой ПК с нуля под ключ, бюджет"
              " 100к."
          ),
          "source": "Telegram канал 'Фриланс / Железо'",
      },
      {
          "text": (
              "Привет! Нужен апгрейд видеокарты и блока питания, посоветуйте"
              " что купить."
          ),
          "source": "Биржа заказов (Бесплатный отклик)",
      },
      {
          "text": "Просто продаю свой старый монитор",
          "source": "Барахолка",
      },  # Этот пост программа отсеиет, так как нет ключевых слов ПК
  ]

  found_count = 0
  for item in mock_feed:
    post_text = item["text"].lower()
    # Проверяем, есть ли нужные слова в посте клиента
    matched = any(kw in post_text for kw in KEYWORDS)

    if matched:
      found_count += 1
      print(f"\n🔥 [КЛИЕНТ НАЙДЕН #{found_count}]")
      print(f"📌 Текст заявки: {item['text']}")
      print(f"🔗 Источник: {item['source']}")
      print("-" * 50)

  print(
      "\n[Ожидание новых постов... Нажмите Ctrl+C для выхода из программы]"
  )


if __name__ == "__main__":
  try:
    while True:
      check_new_leads()
      # Проверка новых заказов каждые 30 секунд
      time.sleep(30)
  except KeyboardInterrupt:
    print("\n⚠️ Работа парсера остановлена пользователем.")
