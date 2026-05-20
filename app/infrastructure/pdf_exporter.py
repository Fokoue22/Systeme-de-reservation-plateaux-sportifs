from __future__ import annotations

from typing import Protocol


class PDFExporter(Protocol):
	def export_html_to_pdf(self, html: str) -> bytes:
		...


class WeasyPrintExporter:
	def export_html_to_pdf(self, html: str) -> bytes:
		try:
			from weasyprint import HTML
		except Exception as exc:  # pragma: no cover - optional dependency
			raise ImportError("weasyprint is required for PDF export") from exc

		return HTML(string=html).write_pdf()

