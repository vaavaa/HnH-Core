# Локальный релиз (без GitHub Actions)

Если вы не используете GitHub Actions (лимиты, биллинг), релизы можно делать полностью на своей машине.

## Шаги

1. **Обновите версию** в `pyproject.toml` (например, `0.1.0` → `0.1.1`).

2. **Запустите тесты и сборку локально:**

   ```bash
   cd /path/to/core
   source .venv/bin/activate   # или ваш venv
   pip install -e ".[dev]"
   pytest tests/ -v
   pip install build
   python -m build
   ```

   В каталоге `dist/` появятся `hnh-<version>.tar.gz` и `hnh-<version>-py3-none-any.whl`.

3. **Закоммитьте версию и запушьте в main** (если ещё не запушено):

   ```bash
   git add pyproject.toml
   git commit -m "Release v0.1.1"
   git push origin main
   ```

4. **Создайте тег и запушьте тег:**

   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```

5. **Создайте Release на GitHub вручную:**
   - Откройте репозиторий на GitHub → вкладка **Releases** → **Draft a new release**.
   - В поле **Choose a tag** выберите только что запушенный тег (например, `v0.1.1`).
   - В поле **Describe this release** вставьте (подставьте свой тег и путь к репо):

   ```
   HnH — детерминированный движок симуляции личности (Identity Core, Dynamic State, натал/транзиты). Python 3.12+.

   Установка по тегу: `pip install git+https://github.com/USER/REPO@vX.Y.Z`
   Или скачать исходник (tar.gz) / wheel ниже.
   ```
   - В блок **Attach binaries** перетащите файлы из вашего локального `dist/`:
     - `hnh-0.1.1.tar.gz`
     - `hnh-0.1.1-py3-none-any.whl`
   - Нажмите **Publish release**.

Готово. Другие смогут ставить по тегу: `pip install git+https://github.com/<user>/<repo>@v0.1.1` или скачать артефакты со страницы Release.
