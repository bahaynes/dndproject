# Product Requirements Document: DnD Westmarches Hub

## 1. Introduction

DnD Westmarches Hub is a web-based companion app for running West Marches–style or other open-table role-playing campaigns. It provides a centralized platform for players and game masters (GMs) to coordinate sessions, manage missions, track in-game economy, and leverage AI tools for adventure generation.

The application is built with **SvelteKit (frontend)** and **FastAPI (backend)**. Data is stored in **SQLite by default**, with optional **PostgreSQL** support for larger groups. Character stats and sheets are managed in external tools (**Foundry VTT** or **D&D Beyond**), while the Hub handles campaign logistics. The system is designed for **easy self-hosting** using **Podman**.

## 2. Goals and Objectives

* **Streamline Campaign Logistics**: Centralize session scheduling, mission management, and in-game economy so the GM spends less time on bookkeeping and more on storytelling.
* **Enable Player Agency**: Give players a clear mission board, a session proposal system, and a store—empowering them to drive the campaign's direction.
* **Augment GM Creativity with AI**: Provide AI-assisted adventure generation that exports directly to Foundry VTT, accelerating prep time.
* **Complement External VTT/Sheet Tools**: Integrate with Foundry VTT and D&D Beyond rather than replacing them—character stats live where they're best managed.
* **Enable Self-Hosting**: Deliver a containerized application that can be deployed with minimal setup.

## 3. Target Audience

* **Role-Playing Game Players** – players who want to browse missions, propose sessions, and manage their in-game economy.
* **Game Masters** – GMs who run and manage West Marches–style campaigns and want AI-assisted prep tools.
* **Self-Hosters and Hobbyists** – people who like running their own apps with Docker/Podman.

Initial scope: **1 GM and 5–10 players per deployment**.

## 4. Features and Functionality

### 4.1. Authentication and Roles

* **Discord OAuth (default)**: Users authenticate via Discord, which naturally maps to the Discord server that hosts the campaign community. JWT session handling is used after initial auth.
* **Privacy Contingency**: If Discord implements privacy-breaching age verification or other hostile changes, the system should be designed to allow swapping to an alternative OAuth provider (e.g., Google, self-hosted OIDC) with minimal code changes. The auth module should remain provider-agnostic behind a clean interface.
* **User Roles**:
  * **Player** – browse missions, propose/back sessions, manage inventory, purchase from the store.
  * **Admin (Game Master)** – manage all game content, generate AI adventures, configure campaigns.
  * **Optional Future Role**: Co-GM (limited admin rights).
* **Campaign Scoping**: Users are scoped to a campaign. A single deployment can host multiple campaigns (multi-tenancy), and users select their campaign after authenticating.

### 4.2. Player Features (MVP)

* **Character Profile** – name, description, image, and external sheet link (Foundry VTT or D&D Beyond URL).
* **In-Game Economy** – XP and Scrip (in-game currency) tracked by the Hub; detailed stats managed externally.
* **Inventory Management** – add, remove, and view items earned through missions or purchased from the store.
* **Mission Board** – browse available/completed missions; sign up for available missions.
* **Session Calendar** – view scheduled game sessions, see proposals, back proposals to vote on content.
* **Company Store** – browse and purchase items with Scrip.

#### User Stories – Player
1. *As a player, I want to browse the Mission Board so I can see what adventures are available and sign up.*
2. *As a player, I want to propose a mission for an upcoming session slot so my party can vote on what to play.*
3. *As a player, I want to "back" another player's proposal so the group can reach consensus and lock in a session.*
4. *As a player, I want to view my character's inventory and Scrip balance so I know what resources I have.*
5. *As a player, I want to purchase items from the Company Store using Scrip so I can gear up for missions.*
6. *As a player, I want to explore the campaign hex map so I can see what regions are discovered and where missions are located.*
7. *As a player, I want to click a hex on the map and see its terrain, location name, and any linked missions.*
8. *As a player, I want to view session details (date, confirmed mission, roster) so I know when and what I'm playing.*

### 4.3. Admin Features (MVP)

* **Admin Dashboard** – toggle between player view and admin tools.
* **Mission Management** – create, edit, retire, and assign rewards (XP, Scrip, items) to missions. Status lifecycle: Available → In Progress → Completed. Distribute rewards to enrolled players.
* **Item Management** – manage master item list and store inventory (prices, stock).
* **Session Management** – create session slots, review proposals, force-confirm or veto proposals, manage rosters, mark sessions as completed, and attach after-action reports.
* **Campaign Map Editor** – create and manage hex-based campaign maps, edit terrain types, mark hexes as discovered, link hexes to missions and locations.
* **Data Tools** – export/import all game data to/from JSON backups.

#### User Stories – Admin
1. *As a GM, I want to create a new mission with a name, description, tier, region, and rewards so players can see it on the Mission Board.*
2. *As a GM, I want to mark a mission as "Completed" and distribute XP/Scrip/items to all enrolled heroes with one click.*
3. *As a GM, I want to create a session time slot so players can propose and vote on what mission to run.*
4. *As a GM, I want to force-confirm a proposal or veto one so I maintain creative control over session content.*
5. *As a GM, I want to use the AI Generator to create a 3-act adventure outline, then link it to a mission.*
6. *As a GM, I want to export a generated adventure as a Foundry VTT module so I can import it directly into my game.*
7. *As a GM, I want to edit the campaign hex map—changing terrain, marking discovered hexes, and linking missions to locations—so the map reflects campaign progress.*
8. *As a GM, I want to manage the Company Store's item catalog and pricing so players can spend their Scrip.*

### 4.4. AI-Assisted Adventure Generation

* **One-Shot Generator**: GMs can generate 3-act adventure outlines via an LLM (OpenRouter with configurable model). Parameters include party size, level, duration, tone, and optional mission/region context from the campaign.
* **Context Aggregation**: The generator pulls campaign context (campaign name, selected mission descriptions, hex region) into the LLM prompt for grounded output.
* **Structured Output**: Adventures are generated as structured JSON (title, hook, acts with scenes, encounters, NPCs, climax, resolution).
* **Foundry VTT Export**: Generated adventures can be exported as Foundry VTT modules containing JournalEntry documents, ready for import into a Foundry world.
* **Job Tracking**: Generation requests are tracked with status (pending → processing → completed/failed), allowing asynchronous generation.

#### User Stories – AI Generation
1. *As a GM, I want to click "AI Generator" while creating a mission so I can quickly scaffold an adventure outline.*
2. *As a GM, I want to tweak the generated adventure before linking it to a mission so I maintain creative control.*
3. *As a GM, I want to download the adventure as a Foundry module ZIP so I can import it directly into my VTT.*

### 4.5. UX Improvements Needed

The following areas have been identified as needing significant UX work:

#### Mission Board & Management
* The player-facing Mission Board needs better visual hierarchy—mission descriptions, rewards, and sign-up status should be scannable at a glance.
* The admin Mission Management page uses a basic modal form that becomes unwieldy with many fields (name, tier, region, cooldown, discoverable, retired, rewards). Consider a multi-step wizard or dedicated page.
* Mission descriptions are plain text. **Markdown support** should be added so GMs can format briefings with headers, bold text, and lists.

#### Session Tools
* The session proposal/backing system is functional but unintuitive for new users. The relationship between sessions, proposals, missions, and backing is not immediately clear.
* Players need clearer guidance on *what* a proposal is, *why* they should back one, and *what happens* when critical mass is reached.
* Consider inline tooltips, a brief "How It Works" explainer, and clearer visual states for proposal progress.

#### Campaign Map Editor
* The hex map editor (`/admin/maps`) is clunky and hard to use.
* Editing individual hexes (terrain, notes, linked missions) should use a click-to-edit panel rather than requiring separate navigation.
* Pan/zoom should feel smooth and responsive.
* Consider adding a terrain palette toolbar and batch-edit support for painting regions.

### 4.6. Real-time Updates

* **Server-Sent Events (SSE)** should be implemented for lightweight live updates to the mission board, session proposal status, and store inventory.
* **Scope**: Real-time covers *list refresh and status changes*, not simultaneous editing.
* Future: optional WebSockets for richer collaboration (chat, shared editing).

### 4.7. Shared Features (Stretch Goals)

* **Session Notes / Journals** – players can keep notes, admins can add shared logs.
* **Tags & Filters** – tag missions, items, or sessions for easier search.
* **Notifications Panel** – simple in-app alerts when new missions/sessions are posted.
* **Markdown Support** – allow markdown in mission descriptions, session descriptions, notes, and reports.
* **Search & Filters** – mission board and store item search/filter.
* **Dark Mode** toggle (currently partially supported via DaisyUI themes).
* **Mobile Responsiveness** – ensure full functionality on mobile devices.

### 4.8. Quality of Life Features

* **Audit Logs** – simple activity history for admins (missions created, rewards distributed).
* **Error & Health Monitoring** – optional integration with Sentry, Prometheus, or similar.
* **Accessibility** – ensure screen reader compatibility, color contrast, and keyboard navigation.
* **Test Data Seeder** – ability to populate with sample characters/missions for demo/testing.

## 5. Technical Requirements

### 5.1. Technology Stack

* **Frontend**: SvelteKit + TailwindCSS (DaisyUI)
* **Backend**: FastAPI (Python, async)
* **Database**: SQLite (default) or PostgreSQL (optional)
* **Authentication**: Discord OAuth with JWT
* **Real-time Updates**: Server-Sent Events (SSE) *(planned)*
* **LLM Integration**: OpenRouter (OpenAI-compatible API), configurable model (default: DeepSeek V3)
* **Containerization**: Podman + Podman Kube YAML
* **State Management**: Svelte stores

### 5.2. Database Schema

Core models:

* `User` – Discord auth data + campaign role
* `Campaign` – campaign metadata and settings
* `Character` – player character profile (name, description, image, external sheet URL)
* `CharacterStats` – XP and Scrip balances
* `Mission` – missions with tier, region, cooldown, prerequisites, discoverable/retired flags
* `MissionReward` – mission reward entries (XP, Scrip, items)
* `Item` – item definitions
* `InventoryItem` – mapping of items → character inventory
* `StoreItem` – store availability + price
* `GameSession` – scheduled sessions with status lifecycle and player capacity
* `GameSessionPlayer` – player signups per session
* `SessionProposal` – mission proposals for a session, with backers
* `HexMap` – campaign map definition
* `Hex` – individual hex tiles with terrain, coordinates, notes, linked missions
* `GeneratedOneShot` – AI-generated adventure data with LLM metadata
* `Note` (stretch) – player or shared campaign notes
* `Tag` (stretch) – tags applied to missions, items, or sessions
* `AuditLog` (stretch) – system events for tracking GM/admin actions

### 5.3. Deployment

* Single repository with both frontend + backend.
* Podman Kube YAML manifests for development and production.
* Default config: separate containers (frontend, backend, database).
* Deployment ready for minimal cloud hosting (Fly.io, Railway, or bare VPS).
* SystemD integration via Podman Quadlet for VPS auto-start.
* CI/CD pipeline (GitHub Actions) for linting, testing, and build.

## 6. Future Enhancements

* **Alternative OAuth Providers** (Google, self-hosted OIDC) as Discord contingency.
* **Enhanced AI Integration** – NPC dialogue generation, encounter balancing, loot table generation.
* **Foundry VTT Plugin** – deeper bidirectional integration (sync characters, push scenes directly).
* **Dice Roller** – lightweight command syntax for in-app rolls.
* **Advanced Real-time** – WebSocket support for richer collaboration (chat, shared editing).
* **Performance Monitoring** – especially for Postgres deployments.
* **Offline-first PWA** – add service worker for caching and mobile play.
* **Plugin System** – allow optional modules (house rules, custom sheets).
