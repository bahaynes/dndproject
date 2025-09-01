# Product Requirements Document: DnD Westmarches Hub

## 1. Introduction

DnD Westmarches Hub is a lightweight, web-based companion app for running West Marches–style or other open-table role-playing campaigns. It provides a centralized platform for players and game masters (Admins) to manage characters, missions, items, and game sessions.

The application is built with **SvelteKit (frontend)** and **FastAPI (backend)**. Data is stored in **SQLite by default**, with optional **PostgreSQL** support for larger groups. The system is designed for **easy self-hosting** using **Podman**.

## 2. Goals and Objectives

The primary goals of this project are to:

* **Enhance the RPG Experience**: Provide a digital companion that streamlines game management and supports immersion for both players and game masters.
* **Centralize Game Data**: Offer a single source of truth for campaign information, accessible in real-time.
* **Simplify Game Master Tasks**: Automate common GM tasks like mission creation, reward distribution, and character management.
* **Empower Players**: Provide a user-friendly interface to track characters, missions, and progress.
* **Enable Self-Hosting**: Deliver a containerized application that can be deployed with minimal setup.

## 3. Target Audience

* **Role-Playing Game Players** – players who want to track their characters and campaign progress.
* **Game Masters** – admins who run and manage role-playing games.
* **Self-Hosters and Hobbyists** – people who like running their own apps with Docker/Podman.

Initial scope: **1 GM and 5–10 players per deployment**.

## 4. Features and Functionality

### 4.1. User Roles and Authentication

* **Local Authentication (default)**: Username and password login with JWT session handling.
* **User Roles**:

  * **Player** – manage their character, join missions, view sessions.
  * **Admin (Game Master)** – manage game content and oversee sessions.
  * **Optional Future Role**: Co-GM (limited admin rights).
* **Optional OAuth (future)**: Support for external providers (e.g., Discord, Google).
* **Character Creation**: A new character is automatically created for each new user (editable by the player).

### 4.2. Player Features (MVP)

* **Character Sheet** – stats, XP, description, and inventory.
* **Character Customization** – update name, description, and image.
* **Inventory Management** – add, remove, and view items.
* **Mission Board** – browse available/completed missions; sign up for missions.
* **Session Calendar** – view scheduled game sessions.
* **Company Store** – browse items purchasable with in-game currency (“Scrip”).

### 4.3. Admin Features (MVP)

* **Admin Dashboard** – toggle between player/admin view.
* **Character Roster** – view and edit all characters.
* **Mission Management** – create, edit, assign rewards.
* **Item Management** – manage master item list and store inventory.
* **Session Management** – schedule sessions, track signups, mark as completed, and attach after-action reports.
* **Data Tools** – export/import all game data to/from JSON backups.

### 4.4. Shared Features (Stretch Goals)

* **Session Notes / Journals** – players can keep notes, admins can add shared logs.
* **Tags & Filters** – tag missions, items, or sessions for easier search.
* **Campaign Map (Pins)** – upload a campaign map image, add pins with text.
* **Notifications Panel** – simple in-app alerts when new missions/sessions are posted.
* **Markdown Support** – allow markdown in mission descriptions, notes, and reports.
* **Search & Filters** – mission board and store item search.
* **Dark Mode** toggle.
* **Mobile Responsiveness** – ensure full functionality on mobile devices.

### 4.5. Real-time Updates

* **Server-Sent Events (SSE)** for lightweight live updates (mission board, session signup, item store).
* **Clarification**: Real-time covers *list refresh and status changes*, not simultaneous editing.
* Future: optional WebSockets for richer collaboration (chat, shared editing).

### 4.6. Quality of Life Features

* **Audit Logs** – simple activity history for admins (missions created, rewards distributed).
* **Error & Health Monitoring** – optional integration with Sentry, Prometheus, or similar.
* **Accessibility** – ensure screen reader compatibility, color contrast, and keyboard navigation.
* **Test Data Seeder** – ability to populate with sample characters/missions for demo/testing.

## 5. Technical Requirements

### 5.1. Technology Stack

* **Frontend**: SvelteKit + TailwindCSS
* **Backend**: FastAPI (Python, async)
* **Database**: SQLite (default) or PostgreSQL (optional)
* **Authentication**:

  * Local username/password auth with JWT (default)
  * Optional OAuth (Discord/Google) in future
* **Real-time Updates**: Server-Sent Events (SSE)
* **Containerization**: Podman + Podman Compose
* **State Management**: Svelte stores

### 5.2. Database Schema

Core models:

* `User` – auth + role info
* `Character` – player character metadata
* `CharacterStats` – detailed stats for a character
* `Mission` – missions and properties
* `MissionReward` – mission reward entries
* `Item` – item definitions
* `InventoryItem` – mapping of items → character inventory
* `StoreItem` – store availability + price
* `GameSession` – scheduled sessions
* `GameSessionPlayer` – player signups per session
* `Note` (stretch) – player or shared campaign notes
* `Tag` (stretch) – tags applied to missions, items, or sessions
* `AuditLog` (stretch) – system events for tracking GM/admin actions

### 5.3. Deployment

* Single repository with both frontend + backend.
* `Dockerfile` and `podman-compose.yml` provided.
* Default config: one container runs FastAPI backend + serves static SvelteKit frontend.
* Optional: separate containers (frontend, backend, database) for advanced setups.
* Offline operation supported (SQLite + local auth), though not required.
* Deployment ready for minimal cloud hosting (Fly.io, Railway, or bare VPS).
* CI/CD pipeline (GitHub Actions) for linting, testing, and build.

## 6. Future Enhancements

* **OAuth Integration** (Discord/Google) for smoother logins.
* **AI Integration** – optional mission/item generation via OpenAI/Claude APIs.
* **Dice Roller** – lightweight command syntax for in-app rolls.
* **Advanced Real-time** – WebSocket support for richer collaboration.
* **Performance Monitoring** – especially for Postgres deployments.
* **Multi-Tenancy** – support multiple campaigns/worlds from one deployment.
* **Offline-first PWA** – add service worker for caching and mobile play.
* **Plugin System** – allow optional modules (house rules, custom sheets).

