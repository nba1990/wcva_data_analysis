from __future__ import annotations

from src.generate_presentation import (
    _apply_demo_mode_to_slides,
    generate_html,
    generate_pdf,
)


def _slides() -> list[dict]:
    return [
        {
            "title": "Baromedr Cymru Wave 2",
            "subtitle": "Volunteering in the Welsh Voluntary Sector",
            "body": "<p>Intro body</p>",
            "chart": None,
            "alt_text": "",
        },
        {
            "title": "Questions & Next Steps",
            "subtitle": "",
            "body": "<p>Closing body</p>",
            "chart": None,
            "alt_text": "",
        },
    ]


def test_apply_demo_mode_to_slides_updates_open_and_close() -> None:
    slides = _slides()

    _apply_demo_mode_to_slides(slides, "/tmp/sample.csv")

    assert "DEMO / SAMPLE DATA" in slides[0]["title"]
    assert "bundled sample dataset" in slides[0]["subtitle"]
    assert "sample fixture" in slides[0]["body"]
    assert "sample fixture dataset" in slides[-1]["body"]


def test_generate_html_in_demo_mode_includes_warning_banner() -> None:
    html = generate_html(_slides(), demo_mode=True)
    assert "DEMO / SAMPLE DATA MODE" in html
    assert "Executive Presentation (DEMO / SAMPLE DATA)" in html


def test_generate_pdf_in_demo_mode_returns_bytes() -> None:
    pdf = generate_pdf(_slides(), demo_mode=True)
    assert pdf.startswith(b"%PDF")
