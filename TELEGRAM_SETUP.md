# Публикация в Telegram-канал — почти готово

## Что уже сделано
- Канал: **Serjant Dev** (`@serjantdev`), ID `-1004319024415`.
- Секреты в репозитории GitHub уже сохранены:
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHANNEL_ID`
- Скрипт `post_bot.py` загружен, тестовый пост **уже опубликован** в канал.
- `posted_ids.json` хранит список опубликованных заказов (чтобы не было повторов).

## Остался один шаг — создать workflow через сайт GitHub
GitHub запрещает создавать файлы `.github/workflows/*` через API, поэтому это нужно сделать один раз вручную в браузере.

1. Откройте ссылку:
   ```
   https://github.com/SERJANYABLOKO/SERJANYABLOKO.github.io/new/main?filename=.github/workflows/telegram-poster.yml
   ```
2. Вставьте содержимое файла `telegram-poster.yml` (ниже).
3. Нажмите **Commit changes**.

После этого автоматика заработает: раз в 4 часа один новый реальный заказ будет публиковаться в канал с полезным советом для разработчиков и короткой подписью об услугах.

### Содержимое `telegram-poster.yml`

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
      - name: Publish one real order
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHANNEL_ID: ${{ secrets.TELEGRAM_CHANNEL_ID }}
        run: python post_bot.py
      - name: Save posted orders state
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add posted_ids.json
          if git diff --cached --quiet; then
            echo "No new posted orders"
          else
            git commit -m "chore: save posted orders [skip ci]"
            git push
          fi
```

## Проверка
**Actions → Telegram Poster → Run workflow** — появится ещё один пост с новым заказом.

## Что публикуется
Реальный заказ из `orders.json` (название, цена, источник, ссылка) + совет для разработчиков + лёгкая реклама: ссылка на `@serjantyabloko`. Один заказ за запуск, без повторов.

## Важно
В публичном `index.html` сайта остался старый Telegram-токен. Его нужно отозвать: `@BotFather` → `/revoke`. Новый бот для канала к сайту не относится и в коде не хранится — только в GitHub Secrets.
