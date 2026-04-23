# Déploiement rapide avec Docker

## Prérequis
- [Docker](https://www.docker.com/products/docker-desktop) installé
- [Docker Compose](https://docs.docker.com/compose/) installé (si besoin)

## Lancer l'application

1. Clonez le dépôt :
   ```sh
   git clone https://github.com/Fokoue22/Systeme-de-reservation-plateaux-sportifs.git
   cd Systeme-de-reservation-plateaux-sportifs
   ```
2. Lancez l'application avec Docker Compose :
   ```sh
   docker-compose up --build
   ```
3. Accédez à l'application sur [http://localhost:8000](http://localhost:8000)

## Arrêter l'application
```sh
docker-compose down
```

## Variables d'environnement
- Vous pouvez personnaliser les variables dans le fichier `docker-compose.yml` si besoin (ex: email, SMS, etc).

---

Pour toute question, contactez l'équipe projet.
