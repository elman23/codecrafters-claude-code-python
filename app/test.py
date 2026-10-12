import re


def replace_values(template: str, values: list[str]) -> str:
    replaced = template.replace('$ARGUMENTS', ' '.join(values))

    replaced = re.sub(
        r'\$(\d+)',
        lambda m: str(values[int(m.group(1))]),
        template
    )

    return replaced


if __name__ == "__main__":
    template = """
Respond with exactly: $ARGUMENTS

Do not add any other text, punctuation, or formatting.
"""
    replaced = replace_values(template, "a b c")
    print(replaced)
