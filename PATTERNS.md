# PATTERNS

Ce document decrit les patterns et principes SOLID appliques pendant le module M1.

## M1 - Gestion des plateaux

Portee M1 implementee:
- CRUD des plateaux sportifs
- Definition des creneaux horaires
- Gestion des disponibilites par jour et plage horaire

### Pattern 1 - Repository Pattern

- Emplacement:
	- app/domain/repositories.py
	- app/infrastructure/repositories.py
- Probleme resolu:
	- Decoupler la logique metier de la persistence (SQLite aujourd'hui, autre source demain).
- Pourquoi ce pattern:
	- La couche application manipule des abstractions (interfaces) et non du SQL direct.
	- Les tests unitaires peuvent utiliser des repositories en memoire sans base de donnees.
- Alternatives considerees:
	- SQL direct dans les services: plus rapide au debut, mais fort couplage et tests plus difficiles.
	- Active Record: pratique, mais moins adapte pour separer clairement domaine et infrastructure dans ce projet de cours.

### Pattern 2 - Service Layer (Application Service)

- Emplacement:
	- app/application/m1_services.py
- Probleme resolu:
	- Centraliser les regles metier du module M1 (validation existence, conflit de creneaux, orchestrations CRUD).
- Pourquoi ce pattern:
	- Evite de mettre la logique metier dans les endpoints API ou dans les repositories.
	- Rend la logique facilement testable en isolation.
- Alternatives considerees:
	- Mettre la logique dans les routes FastAPI: simple initialement, mais devient vite difficile a maintenir.
	- Mettre la logique dans la couche repository: melange metier + acces donnees.

### Pattern 3 - Dependency Injection (composition manuelle)

- Emplacement:
	- app/main.py
	- app/api/m1_routes.py
- Probleme resolu:
	- Fournir les dependances (services/repos) sans que les routes creent elles-memes les objets techniques.
- Pourquoi ce pattern:
	- Simplifie le remplacement d'implementations (ex: in-memory pour tests, SQLite en production).
	- Facilite la lisibilite de l'architecture et la testabilite.
- Alternatives considerees:
	- Instancier partout dans les endpoints: plus de duplication, couplage fort.
	- Conteneur DI externe: possible, mais surdimensionne pour la taille actuelle du module.

### Pattern 4 - Value Object

- Emplacement:
	- app/domain/models.py (Creneau)
- Probleme resolu:
	- Representer un intervalle horaire avec invariants metier (debut < fin) dans un objet immuable.
- Pourquoi ce pattern:
	- Validation metier faite a la creation, donc etat invalide impossible a propager.
	- Reutilisable dans Disponibilite sans dupliquer les verifications.
- Alternatives considerees:
	- Utiliser deux champs primitifs partout (debut/fin): plus de risque d'incoherence et duplication des regles.

### Pattern 5 - Factory Pattern (Seed Data Initialization)

- Emplacement:
	- app/infrastructure/seeds.py (definition des donnees + factory method)
	- app/infrastructure/sqlite.py (méthode seed_initial_data)
	- app/api/deps.py (appel au startup)
- Probleme resolu:
	- Decoupler les donnees initiales de la logique de persistence.
	- Rendre extensible l'ajout de nouveaux plateaux sans modifier le code application.
	- Respecter l'OCP: ajouter de nouveaux sports (Gymnase, Tennis, Piscine, Soccer, Volleyball) sans toucher aux services ou routes.
- Pourquoi ce pattern:
	- Les donnees initiales sont maintenues separement dans PLATEAUX_DATA.
	- La factory method `create_plateau_from_data()` transforme chaque entree en objet domaine.
	- L'operation est idempotente: re-executer ne duplique pas les donnees.
	- Prepares le code pour des variantes futures (seed par fichier YAML, import depuis une API externe, etc).
- Alternatives considerees:
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
