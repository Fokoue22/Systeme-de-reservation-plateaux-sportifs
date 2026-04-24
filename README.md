# Systeme-de-reservation-plateaux-sportifs
Un système permettant à des équipes et des individus de réserver des créneaux sur des plateaux sportifs (gymnases, terrains de tennis, piscines, etc.). Le système gère les disponibilités, détecte et résout automatiquement les conflits, génère des calendriers exportables, et envoie des confirmations et rappels par email.

## Site Web Statique

Le site est accessible sur S3 à l'adresse suivante:
**http://systeme-de-reservation-plateaux-sportifs.s3-website-us-east-1.amazonaws.com**

Les fichiers HTML statiques sont:
- `index.html` - Page d'accueil
- `login.html` - Page de connexion
- `register.html` - Page d'inscription

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

### Configuration Requise

Pour mettre en place ce pipeline, vous devez avoir:
- Un compte AWS avec les permissions IAM appropriées
- Un repository GitHub
- Un bucket S3 configuré pour le static website hosting
- Un token GitHub (stocké dans AWS Parameter Store ou en secret GitHub)

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

## Déploiement avec Docker

Pour déployer l'application avec Docker, consultez le fichier **[DEPLOIEMENT.md](DEPLOIEMENT.md)** qui contient:
- Instructions de construction de l'image Docker
- Configuration du `docker-compose.yml`
- Déploiement en production
- Variables d'environnement requises
