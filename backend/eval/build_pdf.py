"""Build eval/os-notes.pdf from eval/corpus.py.  Needs reportlab (not an app dependency).

    pip install reportlab && python -m eval.build_pdf
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate

from eval.corpus import PAGES, TITLE

OUT = Path(__file__).with_name("os-notes.pdf")


def main() -> None:
    h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=21, spaceAfter=10)
    body = ParagraphStyle("body", fontName="Times-Roman", fontSize=11, leading=16, spaceAfter=7)
    story = []
    for i, (heading, paragraphs) in enumerate(PAGES):
        story.append(Paragraph(heading, h1))
        story += [Paragraph(p, body) for p in paragraphs]
        if i < len(PAGES) - 1:
            story.append(PageBreak())
    SimpleDocTemplate(
        str(OUT), pagesize=A4, title=TITLE, author="Pagewise benchmark",
        leftMargin=2.3 * cm, rightMargin=2.3 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    ).build(story)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
