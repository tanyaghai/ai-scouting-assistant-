import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from src.export.scout_template_docx import export_chapman_style_docx


def export_chapman_style_pdf(team_name: str, scout_date: str = None) -> BytesIO:
    docx_bytes = export_chapman_style_docx(team_name, scout_date)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        docx_path = tmpdir / "scout.docx"
        pdf_path = tmpdir / "scout.pdf"

        docx_path.write_bytes(docx_bytes.getvalue())

        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmpdir),
                str(docx_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        output = BytesIO(pdf_path.read_bytes())
        output.seek(0)
        return output