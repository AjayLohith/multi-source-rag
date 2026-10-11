import io
import os
import sqlite3
from pathlib import Path
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont

FIXTURES_DIR = Path(__file__).parent


def create_text_pdf(path: Path) -> None:
    """Creates a 5-page text PDF with rich text content (no OCR needed)."""
    doc = fitz.open()
    for i in range(1, 6):
        page = doc.new_page(width=595, height=842)  # A4
        text = (
            f"Orbital Robotics Specification Document - Page {i}\n"
            f"This is official page {i} of the engineering manual.\n"
            f"Section {i}.0 covers subsystem telemetry, propulsion diagnostics, "
            f"and scheduled service routines for unmanned orbital platforms."
        )
        page.insert_text((50, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()


def create_scanned_image_pdf(path: Path) -> None:
    """Creates a 1-page PDF containing only an image and no text layer."""
    # Create an image with readable, crisp font
    img = Image.new("RGB", (800, 160), color="white")
    draw = ImageDraw.Draw(img)
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    if font_path.exists():
        font = ImageFont.truetype(str(font_path), 36)
    else:
        font = ImageFont.load_default()

    draw.text(
        (40, 50),
        "OCR fallback must extract this line",
        fill="black",
        font=font,
    )
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")

    doc = fitz.open()
    page = doc.new_page(width=800, height=160)
    page.insert_image(page.rect, stream=img_bytes.getvalue())
    doc.save(str(path))
    doc.close()


def create_corrupt_pdf(path: Path) -> None:
    """Creates a corrupted file pretending to be a PDF."""
    with open(path, "wb") as f:
        f.write(b"%PDF-1.4\n%MalformedGarbageDataNotInPdfFormat\x00\xff\xfe\x12\x34\x56")


def create_csv_fixtures(dir_path: Path) -> None:
    """Creates schema-varied CSV fixtures."""
    # 1. Changed column order
    csv1 = dir_path / "changed_order.csv"
    with open(csv1, "w", encoding="utf-8") as f:
        f.write("department,name,id,salary\n")
        f.write("Engineering,Alice,101,95000\n")
        f.write("Product,Bob,102,88000\n")

    # 2. Unexpected column
    csv2 = dir_path / "unexpected_column.csv"
    with open(csv2, "w", encoding="utf-8") as f:
        f.write("id,name,department,clearance_level,notes\n")
        f.write("201,Charlie,Security,TopSecret,Active badge\n")
        f.write("202,Dana,Operations,Secret,Remote worker\n")


def create_sqlite_fixture(db_path: Path) -> None:
    """Creates a SQLite test database with sample tables and rows."""
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL
        );
        """
    )
    cur.executemany(
        "INSERT INTO employees (id, name, role, department) VALUES (?, ?, ?, ?);",
        [
            (1, "Elena Vance", "Lead Propulsion Engineer", "Propulsion"),
            (2, "Gordon Freeman", "Research Scientist", "Anomalous Materials"),
            (3, "Alyx Vance", "Systems Integrator", "Robotics"),
        ],
    )
    conn.commit()
    conn.close()


def generate_all_fixtures() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    create_text_pdf(FIXTURES_DIR / "sample_text_5page.pdf")
    create_scanned_image_pdf(FIXTURES_DIR / "scanned_image.pdf")
    create_corrupt_pdf(FIXTURES_DIR / "corrupt.pdf")
    create_csv_fixtures(FIXTURES_DIR)
    create_sqlite_fixture(FIXTURES_DIR / "test_records.db")
    print(f"All fixtures generated in {FIXTURES_DIR}")


if __name__ == "__main__":
    generate_all_fixtures()
