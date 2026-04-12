from __future__ import annotations

from app.domain.models import Creneau, Disponibilite, Plateau, WeekDay
from app.domain.repositories import DisponibiliteRepository, PlateauRepository


class NotFoundError(ValueError):
    """Raised when a required resource does not exist."""


class ConflictError(ValueError):
    """Raised when a requested operation conflicts with current state."""


def _overlaps(a: Creneau, b: Creneau) -> bool:
    return a.debut < b.fin and b.debut < a.fin


class PlateauService:
    def __init__(self, plateau_repo: PlateauRepository):
        self.plateau_repo = plateau_repo

    def create_plateau(self, nom: str, type_sport: str, capacite: int, emplacement: str) -> Plateau:
        plateau = Plateau(
            id=None,
            nom=nom,
            type_sport=type_sport,
            capacite=capacite,
            emplacement=emplacement,
        )
        return self.plateau_repo.create(plateau)

    def get_plateau(self, plateau_id: int) -> Plateau:
        plateau = self.plateau_repo.get_by_id(plateau_id)
        if plateau is None:
            raise NotFoundError("Plateau introuvable.")
        return plateau

    def list_plateaux(self) -> list[Plateau]:
        return self.plateau_repo.list_all()

    def update_plateau(
        self,
        plateau_id: int,
        nom: str,
        type_sport: str,
        capacite: int,
        emplacement: str,
    ) -> Plateau:
        self.get_plateau(plateau_id)
        plateau = Plateau(
            id=plateau_id,
            nom=nom,
            type_sport=type_sport,
            capacite=capacite,
            emplacement=emplacement,
        )
        return self.plateau_repo.update(plateau)

    def delete_plateau(self, plateau_id: int) -> None:
        deleted = self.plateau_repo.delete(plateau_id)
        if not deleted:
            raise NotFoundError("Plateau introuvable.")


class DisponibiliteService:
    def __init__(self, plateau_repo: PlateauRepository, disponibilite_repo: DisponibiliteRepository):
        self.plateau_repo = plateau_repo
        self.disponibilite_repo = disponibilite_repo

    def add_disponibilite(
        self,
        plateau_id: int,
        jour: WeekDay,
        creneau: Creneau,
    ) -> Disponibilite:
        if self.plateau_repo.get_by_id(plateau_id) is None:
            raise NotFoundError("Le plateau cible n'existe pas.")

        existing = self.disponibilite_repo.list_by_plateau(plateau_id)
        for item in existing:
            if item.jour == jour and _overlaps(item.creneau, creneau):
                raise ConflictError("Le creneau se chevauche avec une disponibilite existante.")

        dispo = Disponibilite(id=None, plateau_id=plateau_id, jour=jour, creneau=creneau)
        return self.disponibilite_repo.create(dispo)

    def list_disponibilites(self, plateau_id: int) -> list[Disponibilite]:
        if self.plateau_repo.get_by_id(plateau_id) is None:
            raise NotFoundError("Le plateau cible n'existe pas.")
        return self.disponibilite_repo.list_by_plateau(plateau_id)
