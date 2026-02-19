# Contract: 003 — Performance compliance (internal)

**Scope**: Пакет `hnh/`.

- **JSON**: В core path допускается только `orjson`. Запрещены `import json`, `json.dumps`, `json.loads` (допустимые исключения, если есть, перечисляются в тестах и в Cursor rule).
- **Хеширование**: Все хеши (identity_hash, configuration_hash, memory_signature, transit_signature, replay signature) считаются через `xxhash` (xxh3_128 или xxh64). Запрещён `hashlib` в `hnh/` для этих целей.
- **Циклы**: По правилам из `.cursor/rules/performance-optimization.mdc` (вынос инвариантов, предвыделение/comprehensions; при наличии NumPy — векторизация в hot path).

Проверка: автоматические тесты (запрет json/hashlib в core) + референсный бенчмарк без регрессии.
