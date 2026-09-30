import re
import ast
import math


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def fmt(value, decimals=2):
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")

    return f"{value:,.{decimals}f}".replace(",", " ")


def pct(value):
    return f"{value:.2f}%"


def extract_numbers(text):
    text = text.replace(",", ".").replace(" ", "")
    matches = re.findall(r"-?\d+(?:\.\d+)?", text)
    return [float(x) for x in matches]


def extract_percent(text):
    text = text.replace(",", ".")

    matches = re.findall(
        r"(-?\d+(?:\.\d+)?)\s*%",
        text
    )

    return [float(x) for x in matches]


def contains(text, words):
    return any(word in text.lower() for word in words)


# ============================================================
# ПРОСТОЙ БЕЗОПАСНЫЙ МАТЕМАТИЧЕСКИЙ КАЛЬКУЛЯТОР
# ============================================================

ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "abs": abs,
    "ceil": math.ceil,
    "floor": math.floor,
    "pow": pow,
}


def safe_eval(expression):
    expression = expression.replace("^", "**")
    expression = expression.replace(",", ".")

    try:
        tree = ast.parse(expression, mode="eval")
    except Exception:
        return None

    def evaluate(node):

        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError()

        if isinstance(node, ast.BinOp):

            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Add):
                return left + right

            if isinstance(node.op, ast.Sub):
                return left - right

            if isinstance(node.op, ast.Mult):
                return left * right

            if isinstance(node.op, ast.Div):
                return left / right

            if isinstance(node.op, ast.Pow):
                return left ** right

            if isinstance(node.op, ast.Mod):
                return left % right

            raise ValueError()

        if isinstance(node, ast.UnaryOp):

            value = evaluate(node.operand)

            if isinstance(node.op, ast.USub):
                return -value

            if isinstance(node.op, ast.UAdd):
                return value

            raise ValueError()

        if isinstance(node, ast.Call):

            if not isinstance(node.func, ast.Name):
                raise ValueError()

            name = node.func.id

            if name not in ALLOWED_FUNCTIONS:
                raise ValueError()

            args = [
                evaluate(arg)
                for arg in node.args
            ]

            return ALLOWED_FUNCTIONS[name](*args)

        raise ValueError()

    try:
        return evaluate(tree)
    except Exception:
        return None


# ============================================================
# ПРОЦЕНТЫ
# ============================================================

def percentage_calculation(text):

    numbers = extract_numbers(text)
    percentages = extract_percent(text)

    if len(numbers) >= 1 and len(percentages) >= 1:

        amount = numbers[0]
        rate = percentages[0]

        result = amount * rate / 100

        return (
            "🧮 РАСЧЁТ\n\n"
            f"Сумма: {fmt(amount)}\n"
            f"Процент: {pct(rate)}\n\n"
            f"Результат: {fmt(result)}"
        )

    return None


# ============================================================
# ПРОСТОЙ ПРОЦЕНТ
# ============================================================

def simple_interest(text):

    if not contains(text, [
        "простой процент",
        "простые проценты"
    ]):
        return None

    numbers = extract_numbers(text)
    percentages = extract_percent(text)

    if len(numbers) < 1 or len(percentages) < 1:
        return None

    principal = numbers[0]
    rate = percentages[0]

    years = 1

    if len(numbers) >= 2:
        years = numbers[1]

    interest = principal * rate / 100 * years
    total = principal + interest

    return (
        "🏦 ПРОСТОЙ ПРОЦЕНТ\n\n"
        f"Начальная сумма: {fmt(principal)}\n"
        f"Ставка: {pct(rate)} годовых\n"
        f"Срок: {years} лет\n\n"
        f"Доход: {fmt(interest)}\n"
        f"Итоговая сумма: {fmt(total)}"
    )


# ============================================================
# СЛОЖНОЙ ПРОЦЕНТ
# ============================================================

def compound_interest(text):

    if not contains(text, [
        "сложн",
        "капитализац",
        "капитализацией"
    ]):
        return None

    numbers = extract_numbers(text)
    percentages = extract_percent(text)

    if len(numbers) < 1 or len(percentages) < 1:
        return None

    principal = numbers[0]
    rate = percentages[0]

    years = 1

    if len(numbers) >= 2:
        years = numbers[1]

    compounds = 12

    if contains(text, ["ежегодн", "раз в год"]):
        compounds = 1

    elif contains(text, ["ежекварт", "квартал"]):
        compounds = 4

    elif contains(text, ["ежеднев", "каждый день"]):
        compounds = 365

    monthly_rate = rate / 100 / compounds

    total = principal * (
        1 + monthly_rate
    ) ** (compounds * years)

    income = total - principal

    return (
        "📈 СЛОЖНОЙ ПРОЦЕНТ\n\n"
        f"Начальная сумма: {fmt(principal)}\n"
        f"Ставка: {pct(rate)} годовых\n"
        f"Срок: {years} лет\n"
        f"Капитализация: {compounds} раз/год\n\n"
        f"Доход: {fmt(income)}\n"
        f"Итог: {fmt(total)}"
    )


# ============================================================
# ДЕПОЗИТ С ЕЖЕМЕСЯЧНЫМ ПОПОЛНЕНИЕМ
# ============================================================

def deposit_monthly(text):

    if not contains(text, [
        "депозит",
        "вклад"
    ]):
        return None

    if not contains(text, [
        "каждый месяц",
        "ежемесяч",
        "пополня",
        "добавля"
    ]):
        return None

    numbers = extract_numbers(text)
    percentages = extract_percent(text)

    if len(numbers) < 2 or not percentages:
        return None

    initial = numbers[0]
    monthly = numbers[1]
    rate = percentages[0]

    years = 1

    if len(numbers) >= 3:
        years = numbers[2]

    months = int(years * 12)

    monthly_rate = rate / 100 / 12

    if monthly_rate == 0:
        final = initial + monthly * months
    else:
        final = (
            initial * (1 + monthly_rate) ** months
            +
            monthly *
            (
                ((1 + monthly_rate) ** months - 1)
                / monthly_rate
            )
        )

    contributions = initial + monthly * months
    income = final - contributions

    return (
        "🏦 ДЕПОЗИТ + ЕЖЕМЕСЯЧНОЕ ПОПОЛНЕНИЕ\n\n"
        f"Начальная сумма: {fmt(initial)} ₸\n"
        f"Пополнение: {fmt(monthly)} ₸/мес.\n"
        f"Ставка: {pct(rate)} годовых\n"
        f"Срок: {years} лет\n\n"
        f"Внесено всего: {fmt(contributions)} ₸\n"
        f"Доход от процентов: {fmt(income)} ₸\n\n"
        f"💰 Итоговая сумма: {fmt(final)} ₸"
    )


# ============================================================
# КРЕДИТ
# ============================================================

def loan_calculation(text):

    if not contains(text, [
        "кредит",
        "ипотек",
        "займ"
    ]):
        return None

    numbers = extract_numbers(text)
    percentages = extract_percent(text)

    if len(numbers) < 1 or not percentages:
        return None

    principal = numbers[0]
    rate = percentages[0]

    years = 1

    if len(numbers) >= 2:
        years = numbers[1]

    months = int(years * 12)

    monthly_rate = rate / 100 / 12

    if monthly_rate == 0:
        payment = principal / months
    else:
        payment = principal * (
            monthly_rate *
            (1 + monthly_rate) ** months
        ) / (
            (1 + monthly_rate) ** months - 1
        )

    total = payment * months
    overpayment = total - principal

    return (
        "💳 КРЕДИТ\n\n"
        f"Сумма кредита: {fmt(principal)}\n"
        f"Ставка: {pct(rate)} годовых\n"
        f"Срок: {years} лет\n\n"
        f"Ежемесячный платёж: {fmt(payment)}\n"
        f"Всего выплат: {fmt(total)}\n"
        f"Переплата: {fmt(overpayment)}"
    )


# ============================================================
# ROI
# ============================================================

def roi_calculation(text):

    if not contains(text, [
        "roi",
        "доходность",
        "доходность инвестиции"
    ]):
        return None

    numbers = extract_numbers(text)

    if len(numbers) < 2:
        return None

    initial = numbers[0]
    final = numbers[1]

    roi = (final - initial) / initial * 100

    profit = final - initial

    return (
        "📊 ROI\n\n"
        f"Инвестиция: {fmt(initial)}\n"
        f"Итоговая стоимость: {fmt(final)}\n\n"
        f"Прибыль: {fmt(profit)}\n"
        f"ROI: {pct(roi)}"
    )


# ============================================================
# CAGR
# ============================================================

def cagr_calculation(text):

    if not contains(text, [
        "cagr",
        "среднегодов",
        "среднегодовая доходность"
    ]):
        return None

    numbers = extract_numbers(text)

    if len(numbers) < 3:
        return None

    initial = numbers[0]
    final = numbers[1]
    years = numbers[2]

    result = (
        (final / initial) ** (1 / years) - 1
    ) * 100

    return (
        "📈 CAGR\n\n"
        f"Начальная сумма: {fmt(initial)}\n"
        f"Конечная сумма: {fmt(final)}\n"
        f"Период: {years} лет\n\n"
        f"CAGR: {pct(result)} в год"
    )


# ============================================================
# ВОССТАНОВЛЕНИЕ ПОСЛЕ ПАДЕНИЯ
# ============================================================

def recovery_calculation(text):

    if not contains(text, [
        "упал",
        "упала",
        "падени",
        "просадк"
    ]):
        return None

    percentages = extract_percent(text)

    if not percentages:
        return None

    loss = abs(percentages[0])

    if loss >= 100:
        return None

    required = (
        1 / (1 - loss / 100) - 1
    ) * 100

    return (
        "📉 ВОССТАНОВЛЕНИЕ ПОСЛЕ ПАДЕНИЯ\n\n"
        f"Падение: {pct(loss)}\n\n"
        f"Для возврата к исходной цене "
        f"нужен рост: {pct(required)}"
    )


# ============================================================
# ИНФЛЯЦИЯ
# ============================================================

def inflation_calculation(text):

    if not contains(text, [
        "инфляц"
    ]):
        return None

    numbers = extract_numbers(text)
    percentages = extract_percent(text)

    if len(numbers) < 1 or not percentages:
        return None

    amount = numbers[0]
    inflation = percentages[0]

    years = 1

    if len(numbers) >= 2:
        years = numbers[1]

    future_value = amount / (
        (1 + inflation / 100) ** years
    )

    required = amount * (
        (1 + inflation / 100) ** years
    )

    return (
        "📉 ИНФЛЯЦИЯ\n\n"
        f"Сумма: {fmt(amount)}\n"
        f"Инфляция: {pct(inflation)}\n"
        f"Период: {years} лет\n\n"
        f"Реальная покупательная способность: "
        f"{fmt(future_value)}\n\n"
        f"Чтобы сохранить покупательную способность "
        f"{fmt(amount)}, потребуется: "
        f"{fmt(required)}"
    )


# ============================================================
# ОБЫЧНОЕ МАТЕМАТИЧЕСКОЕ ВЫРАЖЕНИЕ
# ============================================================

def math_calculation(text):

    expression = text.strip()

    allowed_chars = set(
        "0123456789+-*/().,^% sqrtlogabcdef"
    )

    # Не пытаемся считать длинные предложения
    if len(expression) > 150:
        return None

    # Должны присутствовать цифры
    if not re.search(r"\d", expression):
        return None

    # Исключаем очевидные предложения
    if re.search(r"[а-яА-ЯёЁa-zA-Z]{4,}", expression):
        return None

    result = safe_eval(expression)

    if result is None:
        return None

    return (
        "🧮 КАЛЬКУЛЯТОР\n\n"
        f"{expression}\n\n"
        f"= {fmt(result)}"
    )


# ============================================================
# ГЛАВНЫЙ РОУТЕР КАЛЬКУЛЯТОРА
# ============================================================

def calculate_finance(text):

    functions = [
        deposit_monthly,
        loan_calculation,
        cagr_calculation,
        roi_calculation,
        recovery_calculation,
        inflation_calculation,
        compound_interest,
        simple_interest,
        percentage_calculation,
        math_calculation,
    ]

    for function in functions:

        try:
            result = function(text)

            if result:
                return result

        except Exception:
            continue

    return None