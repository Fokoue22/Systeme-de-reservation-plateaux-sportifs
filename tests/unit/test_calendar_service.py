from app.application.m3_calendar_service import CalendarService


class DummyRepo:
    def list_by_plateau_and_date(self, start, end, plateau_id=None):
        return []


def test_generate_month_calendar_minimal():
    service = CalendarService(DummyRepo())

    html = service.generate_month_calendar(2026, 5, plateau_id=1)

    assert "Calendar" in html or "Calendrier" in html
