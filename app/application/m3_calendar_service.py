from __future__ import annotations

from typing import Optional


class CalendarService:
	"""Skeleton service for the M3 calendar feature."""

	def __init__(self, reservation_repository) -> None:
		self._reservation_repository = reservation_repository

	def generate_month_calendar(self, year: int, month: int, plateau_id: Optional[int] = None) -> str:
		_ = self._reservation_repository
		return f"<html><body><h1>Calendrier {year}-{month:02d}</h1><p>Plateau: {plateau_id}</p></body></html>"

