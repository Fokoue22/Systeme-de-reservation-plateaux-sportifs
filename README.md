# Systeme-de-reservation-plateaux-sportifs
Un système permettant à des équipes et des individus de réserver des créneaux sur des plateaux sportifs (gymnases, terrains de tennis, piscines, etc.). Le système gère les disponibilités, détecte et résout automatiquement les conflits, génère des calendriers exportables, et envoie des confirmations et rappels par email.

## Structure initiale du projet

```text
Systeme-de-reservation-plateaux-sportifs/
	app/
		api/
		application/
		domain/
		infrastructure/
		main.py
	tests/
		unit/
		integration/
	docs/
	scripts/
	requirements.txt
	.env.example
	pytest.ini
	.coveragerc
	Makefile
	PATTERNS.md
```

## Installation rapide

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer l'application

```bash
uvicorn app.main:app --reload --port 8000
```

Endpoint de verification: `/health`
