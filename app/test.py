import os
import re


skill_file_path = "./app/file"


def main() -> None:
    skills = []

    with open(skill_file_path, "r") as f:
        content = f.read()

    match = re.match(r"\A---\s*\n(.*?)\n---", content, re.DOTALL)

    if not match:
        raise ValueError("No front matter found")

    front_matter = match.group(1)

    name = re.search(r"^name:\s*(.*)$", front_matter,
                     re.MULTILINE).group(1)
    description = re.search(
        r"^description:\s*(.*)$", front_matter, re.MULTILINE
    ).group(1)
    skills.append({"name": name, "description": description})

    print(skills)

    print()


if __name__ == "__main__":
    main()
