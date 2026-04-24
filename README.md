# Systeme-de-reservation-plateaux-sportifs
Un système permettant à des équipes et des individus de réserver des créneaux sur des plateaux sportifs (gymnases, terrains de tennis, piscines, etc.). Le système gère les disponibilités, détecte et résout automatiquement les conflits, génère des calendriers exportables, et envoie des confirmations et rappels par email.

## Site Web Statique

Le site est accessible sur S3 à l'adresse suivante:
**http://systeme-de-reservation-plateaux-sportifs.s3-website-us-east-1.amazonaws.com**

### Note Importante - Authentification

Pour le moment, l'authentification fonctionne uniquement en **développement local**. Les pages S3 tentent de communiquer avec l'API Flask sur `http://localhost:8000`, ce qui n'est pas accessible depuis internet.

### Déploiement en production** (à venir):
Dans les prochains jours, nous déploierons l'application complète avec:
- **AWS Lambda** pour l'API backend
- **DynamoDB** pour la base de données
- **API Gateway** pour les routes HTTP
- **Cognito** pour l'authentification (optionnel)

Une fois déployée, les pages S3 communiqueront avec l'API en production et fonctionneront complètement.


## Structure initiale du projet

```text
Systeme-de-reservation-plateaux-sportifs/
	app/
		api/
		application/
		domain/
		infrastructure/
		main.py
	aws/
	docs/
	Images/	
	scripts/
	static/
	templates/
	tests/
		unit/
		integration/
	DEPLOIEMENT.md
	docker-compose.yml
	Dockerfile
	index.html
	login.html
	register.html	
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

## Déploiement avec Docker

Pour déployer l'application avec Docker, consultez le fichier **[DEPLOIEMENT.md](DEPLOIEMENT.md)** qui contient:
- Instructions de construction de l'image Docker
- Configuration du `docker-compose.yml`
- Déploiement en production
- Variables d'environnement requises


## Couverture de Code

Le projet maintient actuellement une couverture de tests de **83%** sur le code applicatif.

- `M1` : `100%`
- `M2` : `80%`
- `M4` : `91%`
- `M5` : `87%`

**Commande pour générer le rapport de couverture :**
```bash
# Activer l'environnement virtuel d'abord
.venv\Scripts\activate

# Puis lancer les tests avec couverture
pytest --cov=app --cov-report=term-missing --cov-report=xml

# Ou utiliser le Makefile (nécessite make installé)
make coverage
```

### Tests Disponibles
- **Tests unitaires** : Validation des services métier en isolation
- **Tests d'intégration** : Tests end-to-end des API REST
- **Tests de sécurité** : Validation de l'authentification et autorisation

### Métriques de Qualité
- **Linting** : `ruff check app tests`
- **Complexité** : Maintenue sous les seuils acceptables
- **Patterns SOLID** : 5 principes appliqués (voir PATTERNS.md)

## API Externe Intégrée

Le système intègre une **API de notifications externes** pour l'envoi d'emails et SMS :
- Service de livraison email/SMS configurable
- Templates de messages pour différents événements (réservation, annulation, rappels)
- Gestion des préférences utilisateur (email/SMS activés/désactivés)


## Patterns et Principes SOLID

Ce projet applique plusieurs patterns de conception et principes SOLID pour assurer une architecture maintenable et extensible. Voir **[PATTERNS.md](PATTERNS.md)** pour une documentation détaillée.

### Patterns Utilisés

- **Repository Pattern**: Découplage entre logique métier et persistence des données
- **Service Layer Pattern**: Centralisation des règles métier dans des services dédiés  
- **Dependency Injection**: Injection manuelle des dépendances pour faciliter les tests
- **Value Object**: Objets immuables pour représenter des concepts métier (ex: `Creneau`)
- **Factory Pattern**: Création des données de seed initiales dans `seeds.py`
- **Strategy Pattern**: Politiques d'annulation configurables (`FlexibleCancellationPolicy`, `Strict24hCancellationPolicy`)

### Principes SOLID Appliqués

#### 1. Single Responsibility Principle (SRP) - Responsabilité Unique

**Application**: Chaque couche a une responsabilité clairement définie :
- `app/domain/models.py`: Définit les entités métier et leurs invariants
- `app/application/m1_services.py`: Contient la logique métier et l'orchestration
- `app/infrastructure/repositories.py`: Gère l'accès aux données SQLite
- `app/api/m1_routes.py`: Adapte les requêtes HTTP vers les services métier

**Justification**: Cette séparation permet de modifier une couche sans impacter les autres. Par exemple, changer l'implémentation SQLite n'affecte pas la logique métier dans les services.

#### 2. Open/Closed Principle (OCP) - Ouvert à l'extension, fermé à la modification

**Application**: Les services utilisent des interfaces abstraites (`PlateauRepository`, `DisponibiliteRepository`) plutôt que des implémentations concrètes. Le système peut être étendu avec de nouvelles implémentations (PostgreSQL, API externe, in-memory pour les tests) sans modifier le code existant.

**Justification**: Dans `app/application/m1_services.py`, le `PlateauService` dépend de l'interface `PlateauRepository`, permettant de substituer facilement l'implémentation SQLite par une autre sans changer la logique métier.

#### 3. Dependency Inversion Principle (DIP) - Inversion des dépendances

**Application**: Les modules de haut niveau (services) ne dépendent pas des modules de bas niveau (repositories concrets). Au contraire, tous dépendent d'abstractions (interfaces).

**Justification**: Dans `app/api/deps.py`, les dépendances sont injectées manuellement, permettant aux tests d'utiliser des doubles in-memory (`InMemoryPlateauRepository`) au lieu de l'implémentation SQLite réelle, facilitant ainsi les tests unitaires et l'évolution technique.

#### 4. Interface Segregation Principle (ISP) - Ségrégation des interfaces

**Application**: Interfaces spécifiques au domaine plutôt qu'une interface générale :
- `PlateauRepository` pour les opérations sur les plateaux
- `DisponibiliteRepository` pour les disponibilités
- `ReservationRepository` pour les réservations

**Justification**: Chaque service dépend seulement des méthodes dont il a besoin. Par exemple, `PlateauService` n'est pas pollué par les méthodes de `ReservationRepository`.

#### 5. Liskov Substitution Principle (LSP) - Substitution de Liskov

**Application**: Toutes les implémentations respectent les contrats des interfaces. `SQLitePlateauRepository` et `InMemoryPlateauRepository` implémentent la même interface `PlateauRepository`.

**Justification**: Les services peuvent utiliser indifféremment n'importe quelle implémentation conforme sans changer leur comportement, garantissant la substituabilité des composants.


## CI/CD Pipeline

Un pipeline CI/CD automatisé a été mis en place avec:

### Architecture
- **Source**: GitHub (branche `main`)
- **Pipeline**: AWS CodePipeline
- **Déploiement**: S3 Static Website Hosting
- **Authentification**: GitHub Actions avec OIDC

### Fichiers de Configuration

#### 1. GitHub Actions Workflow (`.github/workflows/deploy.yml`)
Déclenche automatiquement le déploiement vers S3 lors d'un push sur la branche `main`.

**À modifier si vous changez**:
- La région AWS: `aws-region: us-east-1`
- Le bucket S3: `s3://systeme-de-reservation-plateaux-sportifs`
- Les fichiers à exclure dans la section `--exclude`

#### 2. AWS CodePipeline Configuration (`aws/codepipeline-config.json`)
Configure le pipeline avec les étapes Source et Deploy.

**À modifier si vous changez**:
- `Owner`: Votre nom d'utilisateur GitHub
- `Repo`: Le nom de votre repository
- `Branch`: La branche à surveiller (actuellement `main`)
- `BucketName`: Le nom de votre bucket S3

#### 3. IAM Policies

**`aws/codepipeline-role-policy.json`**: Permissions pour CodePipeline
**`aws/github-actions-s3-policy.json`**: Permissions pour GitHub Actions
**`aws/s3-public-policy.json`**: Rend le bucket S3 public

**À modifier si vous changez**:
- L'ARN du bucket S3 dans les policies
- Les permissions requises selon vos besoins

#### 4. Trust Policies

**`aws/trust-policy.json`**: Permet à CodePipeline d'assumer la role
**`aws/github-actions-trust-policy.json`**: Permet à GitHub Actions d'assumer la role avec OIDC

**À modifier si vous changez**:
- L'ARN du compte AWS
- Le repository GitHub dans la condition `sub`

### Commandes Utiles

```bash
# Créer le pipeline (déjà fait)
aws codepipeline create-pipeline --cli-input-json file://aws/codepipeline-config.json --region us-east-1

# Déclencher manuellement le pipeline
aws codepipeline start-pipeline-execution --name reservation-app-pipeline --region us-east-1

# Vérifier l'état du pipeline
aws codepipeline get-pipeline-state --name reservation-app-pipeline --region us-east-1

# Uploader un fichier vers S3
aws s3 cp index.html s3://systeme-de-reservation-plateaux-sportifs/index.html --content-type "text/html"
```

