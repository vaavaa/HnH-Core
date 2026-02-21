# 007 — Release tags required

- **Спека**: [spec.md](spec.md)
- **Суть**: каждый релиз HnH должен иметь git-тег, чтобы другие проекты могли ссылаться на версию (например, `pip install git+...@v0.1.0`).
- **Без GitHub Actions**: релизы делаются локально — см. [scripts/release_local.md](../../scripts/release_local.md). Запуск тестов и сборка: `./scripts/release_prepare.sh`; затем тег, push, создание Release на GitHub и загрузка файлов из `dist/`.
- **С Actions** (если включите): в workflow'ах раскомментируйте триггеры `push`/`pull_request` и `push.tags` и уберите `workflow_dispatch`.
- **Действия**: при выпуске новой версии обновить версию в `pyproject.toml`, закоммитить в main, затем тесты+сборка локально, тег, push, Release на GitHub с артефактами.
