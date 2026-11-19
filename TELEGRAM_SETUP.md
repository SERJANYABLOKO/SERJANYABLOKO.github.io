# Telegram-постинг — настроено

## Текущее состояние
- Беседа: супергруппа **Serjant Dev**, ID `-1004419646640` (секрет `TELEGRAM_CHANNEL_ID` обновлён).
- Бот: `@chaneltelebot`, токен в GitHub Secrets `TELEGRAM_BOT_TOKEN`.
- Права бота: администратор с «Публикация сообщений» и «Управление темами».
- Темы созданы (`topics.json`):

| Ключ | Тема | thread_id |
|---|---|---|
| order | 📌 Заказы | 2 |
| tip | 🧠 Полезное | 3 |
| tool | 🔧 Инструменты | 4 |
| update | 🆕 Обновы | 5 |

## Что публикуется
Бот чередует 4 типа постов:
1. **Реальный заказ** из `orders.json` + полезный комментарий.
2. **Полезное разработчику** — разбор по оценке заказов, ТЗ, чек-листы, фриланс.
3. **Полезный сайт дня** — реальный инструмент с рабочей ссылкой.
4. **Обновление проекта** — что изменилось на сайте и в радаре.

Каждый пост уходит в свою тему и имеет хэштег (`#заказы`, `#полезное`, `#инструменты`, `#обновы`) плюс короткую рекламу услуг внизу.

## Осталось: включить автозапуск
GitHub не разрешает создавать `.github/workflows/*` через API — один раз добавьте файл вручную:

1. Откройте https://github.com/SERJANYABLOKO/SERJANYABLOKO.github.io/new/main?filename=.github/workflows/telegram-poster.yml
2. Вставьте YAML из раздела ниже.
3. **Commit changes**.

```yaml
name: Telegram Poster

on:
  schedule:
    - cron: '23 */4 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Publish one post
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHANNEL_ID: ${{ secrets.TELEGRAM_CHANNEL_ID }}
        run: python post_bot.py
      - name: Save state
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add posted_ids.json topics.json
          if git diff --cached --quiet; then
            echo "No state changes"
          else
            git commit -m "chore: save poster state [skip ci]"
            git push
          fi
```

## Безопасность
Старый токен в публичном `index.html` нужно отозвать: `@BotFather` → `/revoke`. Новый токен для бота хранится только в GitHub Secrets.
