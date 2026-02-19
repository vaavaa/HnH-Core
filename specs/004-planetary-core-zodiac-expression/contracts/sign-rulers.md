# Contract: 004 — Sign Rulers (Strength of sign ruler)

**Scope**: Zodiac Expression Layer (Spec 004). Определяет, какая планета является правителем данного зодиакального знака для расчёта «strength of sign ruler».

---

## 1. Sign indices

Знаки заданы фиксированным порядком. Индекс 0–11 используется в расчётах и в контракте данных.

| Index | Sign (EN)   |
|------:|-------------|
| 0     | Aries       |
| 1     | Taurus      |
| 2     | Gemini      |
| 3     | Cancer      |
| 4     | Leo         |
| 5     | Virgo       |
| 6     | Libra       |
| 7     | Scorpio     |
| 8     | Sagittarius |
| 9     | Capricorn   |
| 10    | Aquarius    |
| 11    | Pisces      |

---

## 2. Rulership schemes

Поддерживаются две схемы; реализация MUST предоставить одну как **default** (см. ниже).

### 2.1 Classical (7 planets)

Используются только светила и планеты до Сатурна. Два знака на одну планету (дневная/ночная «диспозиция» в классике здесь не различаются — один правитель на знак).

| Sign index | Sign       | Ruler   |
|-----------:|------------|---------|
| 0          | Aries      | Mars    |
| 1          | Taurus     | Venus   |
| 2          | Gemini     | Mercury |
| 3          | Cancer     | Moon    |
| 4          | Leo        | Sun     |
| 5          | Virgo      | Mercury |
| 6          | Libra      | Venus   |
| 7          | Scorpio    | Mars    |
| 8          | Sagittarius| Jupiter |
| 9          | Capricorn  | Saturn  |
| 10         | Aquarius   | Saturn  |
| 11         | Pisces     | Jupiter |

### 2.2 Modern (10 planets)

Внешние планеты назначены правителями трёх знаков; остальные — как в классике.

| Sign index | Sign       | Ruler   |
|-----------:|------------|---------|
| 0          | Aries      | Mars    |
| 1          | Taurus     | Venus   |
| 2          | Gemini     | Mercury |
| 3          | Cancer     | Moon    |
| 4          | Leo        | Sun     |
| 5          | Virgo      | Mercury |
| 6          | Libra      | Venus   |
| 7          | Scorpio    | Pluto   |
| 8          | Sagittarius| Jupiter |
| 9          | Capricorn  | Saturn  |
| 10         | Aquarius   | Uranus  |
| 11         | Pisces     | Neptune |

---

## 3. Default for Spec 004

- **Default rulership scheme**: **Modern (10 planets)**.  
  Модель 004 — 10 планет; схема Modern согласована с расширенной эфемеридой и даёт по одному правителю на знак из набора 10 планет.
- Конфигурация MAY позволять переключение на Classical; если переключение есть, оно MUST быть версионировано и не ломать детерминизм (один выбранный режим на весь расчёт).

---

## 4. Data contract (implementation)

Реализация MUST экспортировать отображение **sign index → ruler planet name** в одном месте (константа, конфиг или таблица):

- Ключ: целое 0–11 (sign index).
- Значение: строка имени планеты из набора `Sun`, `Moon`, `Mercury`, `Venus`, `Mars`, `Jupiter`, `Saturn`, `Uranus`, `Neptune`, `Pluto`.

Пример (Modern):

```python
# Sign index 0..11 → ruler planet name (default: modern)
SIGN_RULER_MODERN: tuple[str, ...] = (
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Pluto", "Jupiter", "Saturn", "Uranus", "Neptune",
)
```

Для Classical — аналогичная константа с именами из 7 планет (Mars, Venus, Mercury, Moon, Sun, Jupiter, Saturn).

**Strength of sign ruler**: вычисляется из позиции и аспектов **этой** планеты-правителя (долгота, дом, орбы, напряжение аспектов). Формула и нормализация — в рамках модуля zodiac expression; контракт задаёт только соответствие знак → планета-правитель.

---

## 5. References

- Spec 004: §4.2 Computation Rules (strength of sign ruler).
- Spec 004 plan: таблица правителей зафиксирована в контракте/данных 004.
