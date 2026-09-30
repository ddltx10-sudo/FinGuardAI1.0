import re


def clean_ai_text(text: str) -> str:
    # Убираем Markdown-заголовки
    text = re.sub(
        r"^#{1,6}\s*",
        "",
        text,
        flags=re.MULTILINE
    )

    # Обрабатываем Markdown-таблицы
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        if "|" in line:
            parts = [part.strip() for part in line.split("|")]
            parts = [part for part in parts if parts]

            # Если это строка таблицы-разделитель — пропускаем
            if parts and all(
                re.fullmatch(r"[-:]+", part)
                for part in parts
            ):
                continue

            line = " — ".join(parts)

        # Убираем строки-разделители
        if re.fullmatch(r"[\s|:-]+", line):
            continue

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Убираем LaTeX
    text = text.replace(r"\(", "")
    text = text.replace(r"\)", "")
    text = text.replace(r"\[", "")
    text = text.replace(r"\]", "")

    return text.strip()