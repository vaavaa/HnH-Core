#!/usr/bin/env bash
# Локальная подготовка к релизу: тесты + сборка пакета (без GitHub Actions).
# После запуска: запушьте тег и создайте Release на GitHub, прикрепив файлы из dist/.
# Подробно: scripts/release_local.md

set -e
cd "$(dirname "$0")/.."
[ -d .venv ] && source ./.venv/bin/activate
echo "Running tests..."
python3 -m pytest tests/ -v --tb=short
echo "Building package..."
python3 -m pip install -q build
python3 -m build
echo "Done. Artifacts in dist/. Next: git tag vX.Y.Z && git push origin vX.Y.Z, then create Release on GitHub and upload dist/*"
ls -la dist/
