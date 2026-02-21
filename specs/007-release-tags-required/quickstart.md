# 007 — Release tags required

- **Спека**: [spec.md](spec.md)
- **Суть**: каждый релиз HnH должен иметь git-тег, чтобы другие проекты могли ссылаться на версию (например, `pip install git+...@v0.1.0`).
- **CI**: при push/PR в `main` запускаются тесты (`.github/workflows/ci.yml`).
- **Release**: создайте тег и запушьте — `git tag v0.1.0 && git push origin v0.1.0` — тогда запустится `.github/workflows/release.yml` (тесты, сборка, GitHub Release с артефактами).
- **Действия**: при выпуске новой версии обновить версию в `pyproject.toml`, закоммитить в main, затем создать и запушить тег.
