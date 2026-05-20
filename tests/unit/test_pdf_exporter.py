import pytest

from app.infrastructure.pdf_exporter import WeasyPrintExporter


def test_weasyprint_exporter_interface():
    exporter = WeasyPrintExporter()

    try:
        result = exporter.export_html_to_pdf("<p>hi</p>")
        assert isinstance(result, (bytes, bytearray))
    except ImportError:
        pytest.skip("weasyprint not installed in the test environment")
