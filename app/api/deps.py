from __future__ import annotations

from app.application import DisponibiliteService, PlateauService
from app.infrastructure import SQLiteDisponibiliteRepository, SQLiteManager, SQLitePlateauRepository

_db_manager = SQLiteManager()
_plateau_repo = SQLitePlateauRepository(_db_manager)
_disponibilite_repo = SQLiteDisponibiliteRepository(_db_manager)


def init_schema() -> None:
    _db_manager.initialize_schema()


def get_plateau_service() -> PlateauService:
    return PlateauService(_plateau_repo)


def get_disponibilite_service() -> DisponibiliteService:
    return DisponibiliteService(
        plateau_repo=_plateau_repo,
        disponibilite_repo=_disponibilite_repo,
    )
