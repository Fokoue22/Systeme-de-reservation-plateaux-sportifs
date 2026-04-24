# PATTERNS

Ce document décrit les patterns et principes SOLID appliqués pendant les modules M1 à M5.

## M1 - Gestion des plateaux

Portée M1 implémentée :
- CRUD des plateaux sportifs
- Définition des créneaux horaires
- Gestion des disponibilités par jour et plage horaire

### Pattern 1 - Repository Pattern

- **Emplacement** :
  - `app/domain/repositories.py`
  - `app/infrastructure/repositories.py`
- **Problème résolu** :
  - Découpler la logique métier de la persistence (SQLite aujourd'hui, autre source demain).
- **Pourquoi ce pattern** :
  - La couche application manipule des abstractions (interfaces) et non du SQL direct.
  - Les tests unitaires peuvent utiliser des repositories en mémoire sans base de données.
- **Alternatives considérées** :
  - Active Record : aurait mélangé logique métier et persistence.

### Pattern 2 - Service Layer (Application Service)

- **Emplacement** :
  - `app/application/m1_services.py`
- **Problème résolu** :
  - Centraliser les règles métier du module M1 (validation existence, conflit de créneaux, orchestrations CRUD).
- **Pourquoi ce pattern** :
  - Évite de mettre la logique métier dans les endpoints API ou dans les repositories.
  - Rend la logique facilement testable en isolation.
- **Alternatives considérées** :
  - Mettre la logique dans les routes FastAPI : simple initialement, mais devient vite difficile à maintenir.
  - Mettre la logique dans la couche repository : mélange métier + accès données.

### Pattern 3 - Dependency Injection (composition manuelle)

- **Emplacement** :
  - `app/main.py`
  - `app/api/m1_routes.py`
- **Problème résolu** :
  - Fournir les dépendances (services/repos) sans que les routes créent elles-mêmes les objets techniques.
- **Pourquoi ce pattern** :
  - Simplifie le remplacement d'implémentations (ex: in-memory pour tests, SQLite en production).
  - Facilite la lisibilité de l'architecture et la testabilité.
- **Alternatives considérées** :
  - Instancier partout dans les endpoints : plus de duplication, couplage fort.
  - Conteneur DI externe : possible, mais surdimensionné pour la taille actuelle du module.

### Pattern 4 - Value Object

- **Emplacement** :
  - `app/domain/models.py` (Creneau)
- **Problème résolu** :
  - Représenter un intervalle horaire avec invariants métier (début < fin) dans un objet immuable.
- **Pourquoi ce pattern** :
  - Validation métier faite à la création, donc état invalide impossible à propager.
  - Réutilisable dans Disponibilite sans dupliquer les vérifications.
- **Alternatives considérées** :
  - Utiliser deux champs primitifs partout (début/fin) : plus de risque d'incohérence et duplication des règles.

### Pattern 5 - Factory Pattern (Seed Data Initialization)

- **Emplacement** :
  - `app/infrastructure/seeds.py` (définition des données + factory method)
  - `app/infrastructure/sqlite.py` (méthode seed_initial_data)
  - `app/api/deps.py` (appel au startup)
- **Problème résolu** :
  - Découpler les données initiales de la logique de persistence.
  - Rendre extensible l'ajout de nouveaux plateaux sans modifier le code application.
  - Respecter l'OCP : ajouter de nouveaux sports (Gymnase, Tennis, Piscine, Soccer, Volleyball) sans toucher aux services ou routes.
- **Pourquoi ce pattern** :
  - Les données initiales sont maintenues séparément dans PLATEAUX_DATA.
  - La factory method `create_plateau_from_data()` transforme chaque entrée en objet domaine.
  - L'opération est idempotente : ré-exécuter ne duplique pas les données.
  - Prépare le code pour des variantes futures (seed par fichier YAML, import depuis une API externe, etc).
- **Alternatives considérées** :
	- SQL INSERT direct dans initialize_schema: couple le schema et les donnees, difficile a maintenir.
	- Seed lors d'un appel API manuel: oubli facile et data inconsistente entre environnements.

### Fichiers modifies (traceabilite)

- app/infrastructure/seeds.py
	- Creation du catalogue de seed et de la factory method `create_plateau_from_data`.
	- Generation des series M1..Mn par sport/zone pour faciliter les extensions futures.
	- Specialisation des piscines par zone qualifiee: `Zone Est - Olympique` (M1..M3) et `Zone Est - Semi-olympique` (M1..M3).
- app/infrastructure/sqlite.py
	- Ajout/maintien de `seed_initial_data` avec logique idempotente (insertion uniquement des plateaux manquants).
	- Migration defensive des anciens noms de seed (suppression uniquement si aucune reservation liee), y compris les anciennes series piscine M4/M5.
	- Provisionnement automatique des disponibilites par defaut pour chaque plateau (LUNDI-DIMANCHE, 08:00-22:00) pour garantir la reservation immediate.
	- Garde-fou concurrence: contrainte unique partielle pour bloquer deux reservations CONFIRMED identiques (meme plateau/date/creneau).
	- Index SQL de performance: recherches rapides sur disponibilites et reservations (plateau/date/creneau/statut, created_at).
- app/infrastructure/repositories.py
	- Fallback transactionnel: en cas de collision concurrente sur un creneau confirme exact, la reservation bascule automatiquement en WAITLISTED.
	- Ajout de la mise a jour metier d'une reservation (plateau/date/creneau/statut/nb_personnes).
- app/api/deps.py
	- Appel du seed au demarrage via `init_schema()`.
- app/api/m1_routes.py
	- Provisionnement automatique des disponibilites par defaut lors de la creation d'un nouveau plateau API (M1), pour eviter un plateau non reservable apres creation.
- app/api/m2_routes.py
	- Endpoint d'edition de reservation (`PUT /m2/reservations/{id}`).
- app/application/m2_services.py
	- Regles metier d'edition: verif proprietaire, capacite, disponibilite et recalcul CONFIRMED/WAITLISTED.
- app/domain/repositories.py
	- Extension du contrat `ReservationRepository` avec `update_reservation`.
- static/js/calendar.js
	- Alignement UX/API des messages d'erreur: mapping des details backend (409/422) vers des messages utilisateur coherents en creation/annulation de reservation.
	- Section "Mes reservations" (liste par date), actions crayon/poubelle sur ses cartes et mode edition via formulaire.
- templates/calendar.html
	- Ajout de la section "Mes reservations" dans la colonne de droite.
- static/css/calendar.css
	- Styles de la section "Mes reservations", actions de cartes et double etiquetage haut/bas des colonnes.
- PATTERNS.md
	- Documentation des patterns et ajout de la trace des fichiers modifies.

## Principes SOLID appliques dans M1

### SRP - Single Responsibility Principle

- Application:
	- models.py: entites et invariants de domaine
	- m1_services.py: logique metier/orchestration
	- repositories.py (infrastructure): acces SQLite
	- m1_routes.py: adaptation HTTP
- Pourquoi:
	- Chaque couche a une responsabilite unique, ce qui limite les effets de bord lors des modifications.

### OCP - Open/Closed Principle

- Application:
	- Les services travaillent avec les interfaces PlateauRepository et DisponibiliteRepository.
	- On peut ajouter une nouvelle implementation (PostgreSQL, API externe, in-memory) sans modifier la logique metier.
- Pourquoi:
	- Le module peut evoluer par extension des implementations techniques plutot que par modification du coeur metier.

### LSP - Liskov Substitution Principle

- Application:
	- Les implementations SQLite*Repository et les doubles de tests in-memory respectent les memes contrats.
- Pourquoi:
	- Les services fonctionnent avec n'importe quelle implementation conforme, sans changer leur comportement attendu.

### ISP - Interface Segregation Principle

- Application:
	- Deux interfaces separees: PlateauRepository et DisponibiliteRepository.
- Pourquoi:
	- Chaque client depend seulement des methodes dont il a besoin.

### DIP - Dependency Inversion Principle

- Application:
	- Les services dependent des abstractions de repository, pas des classes SQLite concretes.
- Pourquoi:
	- Reduit le couplage metier/infrastructure, facilite les tests et l'evolution technique.

## Pourquoi ces choix pour M1

- M1 est la base du projet: il faut privilegier une architecture stable et testable.
- Ces patterns sont simples, concrets, et directement relies aux exigences de qualite OO du cours.
- Ils preparent naturellement les modules suivants:
	- M2 (reservations et conflits) pourra reutiliser les memes services + repositories.
	- M4 (notifications) pourra etre ajoute sans casser le coeur metier de M1.

## M2 - Reservation et gestion des conflits

Portee M2 implementee:
- Creation de reservation
- Detection de conflits sur creneaux
- Mise en liste d'attente automatique (waitlist)
- Annulation avec politique configurable

### Pattern 6 - Strategy Pattern (politique d'annulation)

- Emplacement:
	- app/domain/cancellation_policies.py
	- app/api/m2_routes.py
	- app/application/m2_services.py
- Probleme resolu:
	- Changer la regle d'annulation sans modifier le service de reservation.
- Pourquoi ce pattern:
	- `FlexibleCancellationPolicy` et `Strict24hCancellationPolicy` encapsulent chacune une regle.
	- Le service consomme l'abstraction `CancellationPolicy`.
- Alternatives considerees:
	- `if/else` dans le service selon un flag: plus rapide au debut, mais moins extensible.

### Pattern 7 - State (etat de reservation)

- Emplacement:
	- app/domain/models.py (`ReservationStatus`)
	- app/application/m2_services.py
- Probleme resolu:
	- Encadrer clairement le cycle de vie d'une reservation (CONFIRMED, WAITLISTED, CANCELLED).
- Pourquoi ce pattern:
	- Les transitions sont explicites et testables (ex: annulation puis promotion d'un element en attente).
- Alternatives considerees:
	- Boolens multiples (`is_cancelled`, `is_waitlisted`): plus ambigu et source d'incoherence.

### Pattern 8 - Queue-like Waitlist Policy

- Emplacement:
	- app/application/m2_services.py (`_promote_waitlist`)
	- app/infrastructure/repositories.py (tri par `created_at`)
- Probleme resolu:
	- Determiner quel element en attente doit etre promu quand une reservation confirmee est annulee.
- Pourquoi ce pattern:
	- Les reservations waitlist sont traitees dans l'ordre de creation pour garder un comportement previsible.
- Alternatives considerees:
	- Priorite manuelle ou score complexe: non necessaire pour M2.

## Principes SOLID appliques dans M2

### SRP - Single Responsibility Principle

- Application:
	- `m2_services.py` contient les regles metier de reservation et conflits.
	- `m2_routes.py` adapte uniquement la couche HTTP.
	- `SQLiteReservationRepository` gere uniquement la persistence des reservations.

### OCP - Open/Closed Principle

- Application:
	- Ajout de nouvelles politiques d'annulation possible en implementant `CancellationPolicy`.
	- Service inchangé pour introduire une nouvelle strategie.

### LSP - Liskov Substitution Principle

- Application:
	- Toute implementation de `CancellationPolicy` est interchangeable dans `cancel_reservation`.
	- Toute implementation de `ReservationRepository` respectant le contrat fonctionne avec le service.

### ISP - Interface Segregation Principle

- Application:
	- `ReservationRepository` expose un contrat specifique a M2, sans imposer des methodes M1.
	- Les clients de M1 ne dependent pas des operations de reservation.

### DIP - Dependency Inversion Principle

- Application:
	- `ReservationService` depend des abstractions (`PlateauRepository`, `DisponibiliteRepository`, `ReservationRepository`).
	- Les details SQLite restent confines a la couche infrastructure.

## Pourquoi ces choix pour M2

- Le module M2 introduit des regles metier evolutives (conflits, annulation, liste d'attente).
- Les patterns Strategy et State rendent ces regles lisibles et extensibles.
- Cette base permet de brancher M4 (notifications) sans modifier le coeur decisionnel de M2.

## M4 - Notifications

Portee M4 implementee:
- Gestion des preferences de notification par utilisateur (email/SMS, recap hebdo, admin)
- Emission de notifications sur les evenements reservation (creation, attente, annulation, modification, promotion)
- Historique des notifications envoyees/echouees
- Planification et execution des rappels J-1
- Generation d'un recapitulatif hebdomadaire pour administrateurs

### Pattern 9 - Adapter Pattern (delivery providers)

- Emplacement:
	- app/application/m4_delivery.py
- Probleme resolu:
	- Decoupler le service metier de notification des fournisseurs externes (SendGrid, Twilio, etc.).
- Pourquoi ce pattern:
	- `EmailSender` et `SmsSender` servent de ports.
	- Les implementations `ConsoleEmailSender`/`ConsoleSmsSender` permettent le dev/test local sans dependance externe.
- Alternatives considerees:
	- Appeler directement un provider dans `NotificationService`: plus rapide au debut, mais fort couplage.

### Pattern 10 - Template Method / Message Builder

- Emplacement:
	- app/application/m4_templates.py
- Probleme resolu:
	- Standardiser la generation de contenus notification selon le type d'evenement.
- Pourquoi ce pattern:
	- `build_message(...)` centralise les sujets/corps et evite les duplications.
	- Facilite la localisation et l'evolution des formulations.

### Pattern 11 - Domain Events Integration (M2 -> M4)

- Emplacement:
	- app/application/m2_services.py
- Probleme resolu:
	- Notifier automatiquement sans exposer la logique de notification dans les routes HTTP.
- Pourquoi ce pattern:
	- Le service M2 emet des appels vers M4 apres transitions metier (CONFIRMED, WAITLISTED, CANCELLED, UPDATE, PROMOTION).
	- Conserve l'encapsulation metier dans les services applicatifs.

### Fichiers modifies (traceabilite) - M4

- app/domain/notifications.py
	- Modeles domaine M4 (preferences, messages, reminder tasks, enums canal/evenement/statut).
- app/domain/repositories.py
	- Contrats repository M4 (preferences, notifications, reminders).
- app/infrastructure/sqlite.py
	- Tables M4 + indexes (notification_preferences, notifications, reminder_tasks).
- app/infrastructure/repositories.py
	- Implementations SQLite des repositories M4.
- app/application/m4_delivery.py
	- Adaptateurs d'envoi email/SMS (console/dev).
- app/application/m4_templates.py
	- Builder de messages par evenement reservation.
- app/application/m4_services.py
	- Service M4: preferences, emission, historique, rappels J-1, recap hebdo admin.
- app/api/deps.py
	- Injection des dependances M4 et exposition de `get_notification_service`.
- app/api/schemas.py
	- Schemas API M4 (preferences, notifications, resultats de jobs).
- app/api/m4_routes.py
	- Endpoints M4 (preferences, historique, reminders run, weekly-summary run).
- app/main.py
	- Enregistrement du router M4.
- tests/integration/test_m4_api.py
	- Tests d'integration de bout en bout M4.

## Principes SOLID appliques dans M4

### SRP - Single Responsibility Principle

- Application:
	- `m4_services.py`: orchestration metier de notifications
	- `m4_delivery.py`: livraison canal
	- `m4_templates.py`: contenu des messages
	- repositories M4: persistence
	- routes M4: adaptation HTTP

### OCP - Open/Closed Principle

- Application:
	- Ajout d'un nouveau canal possible via nouvelle implementation de sender sans modifier le service.
	- Ajout de nouveaux types d'evenements via enums + templates.

### DIP - Dependency Inversion Principle

- Application:
	- `NotificationService` depend des abstractions repository et sender, pas de SQLite/provider concret.

## Pourquoi ces choix pour M4

- Le module M4 introduit des integrations externes potentiellement instables (email/SMS).
- La separation ports/adapters + templates + orchestration rend le module testable et evolutif.
- L'integration M2 -> M4 preserve la logique metier existante tout en ajoutant des comportements transverses (notifications).

## M5 - Authentification et comptes

Portée M5 implémentée :
- Création de compte (register)
- Connexion/déconnexion avec session persistante via cookie HTTP-only
- Résolution de l'utilisateur courant (`/auth/me`)
- Liaison compte -> préférences M4 pour email/SMS

### Pattern 12 - Session-based Authentication (State + Repository)

- **Emplacement** :
  - `app/api/m5_auth_routes.py`
  - `app/application/m5_auth_services.py`
  - `app/domain/models.py`
  - `app/domain/repositories.py`
  - `app/infrastructure/repositories.py`
  - `app/infrastructure/sqlite.py`
- **Problème résolu** :
  - Identifier un utilisateur authentifié sans transmettre manuellement son identité à chaque requête.
- **Pourquoi ce pattern** :
  - Le service auth encapsule hashage de mot de passe, vérification, création/invalidation de session.
  - Les tables `user_accounts` et `user_sessions` permettent une persistence simple et testable.
  - Les routes M2 peuvent réutiliser l'identité de session pour verrouiller la propriété des réservations.
- **Alternatives considérées** :
  - JWT stateless : plus flexible, mais plus de complexité (rotation/revocation) inutile à ce stade.
  - Session mémoire : simple, mais non persistante et moins robuste en redémarrage.

### Pattern 13 - Uniqueness Constraint + Service Guard (email utilisateur)

- **Emplacement** :
  - `app/infrastructure/sqlite.py`
  - `app/infrastructure/repositories.py`
  - `app/application/m5_auth_services.py`
  - `app/api/m5_auth_routes.py`
- **Problème résolu** :
  - Empêcher qu'un second compte réutilise la même adresse e-mail.
- **Pourquoi ce pattern** :
  - La contrainte SQL `uq_user_accounts_email_lower` protège la base même en cas de concurrence.
  - Le service applique aussi une vérification explicite pour afficher un message métier clair avant l'erreur technique.
- **Alternatives considérées** :
  - Vérifier uniquement dans l'API : insuffisant face aux accès concurrents ou aux autres points d'entrée.
  - Laisser la contrainte seule : robuste, mais l'erreur SQLite serait moins lisible pour l'utilisateur.

### Pattern 14 - Account Settings Modal (UI composition)

- **Emplacement** :
  - `templates/calendar.html`
  - `static/js/calendar.js`
  - `static/css/calendar.css`
- **Problème résolu** :
  - Offrir des actions compte dans l'application principale sans polluer la page de réservation.
- **Pourquoi ce pattern** :
  - Le bouton `Paramètres pro` ouvre un panneau dédié avec sections distinctes (profil, sécurité, support, suppression, affichage).
  - Le mode compact est une préférence locale non intrusive qui améliore la lisibilité du planning.
- **Alternatives considérées** :
  - Plusieurs pages séparées pour chaque sous-action : plus lourd pour l'utilisateur et plus coûteux à naviguer.
  - Popups dispersées sur la page principale : moins cohérentes et moins maintenables.

### Pattern 15 - Branded Authentication Surface

- **Emplacement** :
  - `templates/auth_login.html`
  - `templates/auth_register.html`
  - `static/css/auth.css`
  - `app/main.py`
- **Problème résolu** :
  - Donner au service d'authentification une présentation distincte et plus immersive avant l'entrée dans le calendrier.
- **Pourquoi ce pattern** :
  - Le fond visuel utilise une image du dossier `Images` avec superposition pour garder la lisibilité.
  - L'accès à `calendar` reste protégé par session ; l'auth est la porte d'entrée officielle.
- **Alternatives considérées** :
  - Réutiliser la page calendrier pour l'auth : plus simple, mais confond la connexion avec la réservation.
  - Garder un fond uni : plus sobre, mais moins conforme à la demande visuelle et moins distinctif.

## Intégration d'API Externe

### Pattern 16 - External API Integration (Adaptateur)

- **Emplacement** :
  - `app/application/m4_delivery.py`
  - `app/application/m4_services.py`
- **Problème résolu** :
  - Intégrer des services externes (email/SMS) sans coupler le code métier.
- **Pourquoi ce pattern** :
  - Interfaces `EmailSender` et `SmsSender` permettent de changer d'implémentation (SendGrid, Twilio, etc.).
  - Implémentations console pour développement, vraies implémentations en production.
- **Alternatives considérées** :
  - Appels directs aux APIs externes : couplerait le métier aux détails d'intégration.

## CI/CD et Déploiement

## CI/CD et Déploiement

### Pattern 17 - Infrastructure as Code (Docker + AWS)

- **Emplacement** :
  - `Dockerfile`
  - `docker-compose.yml`
  - `DEPLOIEMENT.md`
  - `.github/workflows/deploy.yml`
  - `aws/`
- **Problème résolu** :
  - Déployer l'application de façon reproductible et automatisée.
- **Pourquoi ce pattern** :
  - Docker containerise l'application pour la portabilité.
  - AWS CodePipeline automatise le déploiement du frontend statique.
  - GitHub Actions avec OIDC pour l'authentification sécurisée.
  - Couverture de tests maintenue à environ **61%** sur le code applicatif.
- **Alternatives considérées** :
  - Déploiement manuel : sujet aux erreurs et non reproductible.

### Pattern 18 - Configuration Environment (12-Factor App)

- **Emplacement** :
  - `.env.example`
  - Variables d'environnement dans docker-compose.yml
- **Problème résolu** :
  - Gérer les configurations (DB, secrets) selon l'environnement.
- **Pourquoi ce pattern** :
  - Séparation configuration/code selon les 12 facteurs.
  - Variables d'environnement injectées au runtime.
- **Alternatives considérées** :
  - Configuration hardcodée : non sécurisée et non flexible.

## Patterns non utilisés et où ils auraient pu servir

### Observer Pattern
- **Où il aurait pu servir** : Dans M4 pour notifier plusieurs services (email, SMS, push) lors d'un événement de réservation.
- **Pourquoi pas utilisé** : L'approche directe dans le service M4 était suffisante pour les besoins actuels.

### Command Pattern
- **Où il aurait pu servir** : Pour encapsuler les opérations de réservation/annulation dans M2 avec undo/redo.
- **Pourquoi pas utilisé** : Complexité non nécessaire pour les opérations actuelles.

### Decorator Pattern
- **Où il aurait pu servir** : Pour ajouter des fonctionnalités transversales (logging, cache) aux services.
- **Pourquoi pas utilisé** : AOP serait plus approprié pour les préoccupations transversales.

### Singleton Pattern
- **Où il aurait pu servir** : Pour les services partagés comme la connexion DB.
- **Pourquoi pas utilisé** : Injection de dépendances plus testable et flexible.

### Abstract Factory Pattern
- **Où il aurait pu servir** : Pour créer des familles d'objets liées (repository + service).
- **Pourquoi pas utilisé** : Factory simple suffisait pour les besoins actuels.
