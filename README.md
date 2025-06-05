# Simple Blog

Это очень простое приложение на Flask для ведения блога. Посты хранятся в JSON файле.

## Запуск

```bash
pip install -r requirements.txt
python app.py
```

Приложение будет доступно по адресу http://localhost:5000

## Деплой на GitHub Pages

Репозиторий содержит workflow GitHub Actions, который при каждом пуше в ветку `main`
создаёт статическую версию блога и публикует её через GitHub Pages. Сгенерированные
файлы попадают в директорию `docs/` и автоматически разворачиваются в Pages.
