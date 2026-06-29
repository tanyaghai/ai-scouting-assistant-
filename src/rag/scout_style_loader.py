from pathlib import Path

from docx import Document
from pypdf import PdfReader


SCOUT_DIR = Path("data/oldscouts/SCOUTS-TGAK")
SUPPORTED_EXTENSIONS = {".txt", ".docx", ".pdf"}


def read_txt(path: Path) -> str:
    return path.read_text(errors="ignore")


def read_docx(path: Path) -> str:
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())

    return "\n".join(pages)


def read_scout_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return read_txt(path)

    if suffix == ".docx":
        return read_docx(path)

    if suffix == ".pdf":
        return read_pdf(path)

    return ""


def load_style_examples(max_reports=3, max_chars_per_report=4000):
    examples = []

    files = sorted([
        file for file in SCOUT_DIR.glob("*")
        if (
            file.is_file()
            and not file.name.startswith(".")
            and file.suffix.lower() in SUPPORTED_EXTENSIONS
        )
    ])

    for file in files[:max_reports]:
        try:
            text = read_scout_file(file)
        except Exception as error:
            print(f"Skipping {file.name}: {error}")
            continue

        text = text.strip()

        if not text:
            continue

        if len(text) > max_chars_per_report:
            text = text[:max_chars_per_report]

        examples.append({
            "filename": file.name,
            "text": text,
        })

    return examples


if __name__ == "__main__":
    reports = load_style_examples()

    for report in reports:
        print("=" * 60)
        print(report["filename"])
        print(report["text"][:800])