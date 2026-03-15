# Spelljammer Westmarches Hub — Product Requirements Document

## 1. Product Overview

Spelljammer Westmarches Hub is a web-based campaign management platform for running West Marches–style D&D 5e games set aboard a persistent spelljammer ship. It provides a centralized place for players and Game Masters to coordinate sessions, manage missions, track the ship's economy, and keep a transparent record of everything that happens in the campaign.

**Core value proposition:** Enable Westmarches play where attendance is optional but consequences are real, through a single pane of glass that keeps every player informed and every resource accounted for.

The application is designed for easy self-hosting using containers (Podman/Docker), with a SvelteKit frontend, FastAPI backend, and SQLite by default (PostgreSQL optional). Character stats and sheets are managed in external tools (Foundry VTT or D&D Beyond); the Hub handles campaign logistics, economy, and coordination.

**Initial scope:** 1 GM and 5–10 players per deployment. A single deployment can host multiple campaigns (multi-tenancy).

---

## 2. Goals and Objectives

- **Streamline campaign logistics.** Centralize session scheduling, mission management, ship resources, and the in-game economy so the GM spends less time bookkeeping and more time storytelling.
- **Enable player agency.** Give players a clear mission board, session proposal system, and company store—empowering them to drive the campaign's direction.
- **Make consequences transparent.** An immutable ledger tracks every resource change, death, and mission outcome. No ambiguity about ship state.
- **Complement external tools.** Integrate with Foundry VTT and D&D Beyond rather than replacing them. Character stats live where they're best managed.
- **Augment GM creativity with AI.** Provide AI-assisted adventure generation that exports directly to Foundry VTT, accelerating prep time.
- **Enable self-hosting.** Deliver a containerized application deployable with minimal setup.

---

## 3. Target Audience

- **Players** — browse missions, propose and sign up for sessions, manage their in-game economy and inventory, and track ship status.
- **Game Masters** — run and manage the campaign, create missions, log session outcomes, configure the ship, and use AI-assisted prep tools.
- **Self-hosters and hobbyists** — people who prefer running their own apps with Docker/Podman on a VPS or cloud host.

---

## 4. Core Entities

### 4.1 Ship

The ship is the persistent hub of the campaign. Its state is always visible and always current.

| Field | Description |
|---|---|
| Name | Ship name |
| Level | Current ship level (1–20) |
| Fuel | Current / max fuel capacity |
| Crystals | Current crystal reserve |
| Credits | Treasury balance (in-game currency, a.k.a. Scrip) |
| Success rate | Missions succeeded / total missions (percentage) |
| Crew roster | All characters (active, dead, benched) |
| Status | Derived from resource levels: All Systems Nominal, Low Fuel Warning, Critical |
| Announcement / MOTD | GM-editable text for ship memos and news |
| Created date | When the campaign ship was established |

### 4.2 Character

Characters belong to players. A player may have multiple characters. Stats and detailed sheets are managed externally.

| Field | Description |
|---|---|
| Name | Character name |
| Player | Owning player |
| Class / Level | D&D class and current level |
| Description | Optional flavor text or backstory |
| Image | Character portrait (optional) |
| External sheet link | URL to Foundry VTT or D&D Beyond sheet |
| Status | Active, Dead, or Benched |
| XP | Experience points (tracked by Hub) |
| Scrip balance | In-game currency balance |
| Inventory | Items earned or purchased |
| Missions completed | Count of completed missions |
| Joined date | When the character was created |
| Date of death | If applicable |

### 4.3 Mission

Missions are the unit of adventure. They live on the mission board until completed or retired.

| Field | Description |
|---|---|
| Title | Mission name |
| Hex location | Map reference |
| Difficulty | Tier / level bracket (1–5) |
| Risk level | Flavor label: Low / Medium / High / Extreme |
| Fuel cost | Fuel consumed to travel |
| Expected crew size | Recommended party size |
| Rewards | Credits, Crystals, XP, and item rewards |
| Description | GM briefing (supports Markdown) |
| Status | Available → In Progress → Completed / Failed / Retired |
| Created by | GM who authored it |
| Scheduled date/time | When the session is planned |
| Sign-up deadline | Cutoff for player sign-ups |
| Cooldown | Optional cooldown before mission can repeat |
| Discoverable | Whether the mission appears on the board or must be found |

### 4.4 Session

A session is a scheduled play event tied to a mission.

| Field | Description |
|---|---|
| Date / time | Scheduled session time |
| Mission | Linked mission |
| Party | List of signed-up characters |
| Player capacity | Min and max party size |
| GM | GM running the session |
| Status | Scheduled → In Progress → Complete |
| Proposals | Player-submitted mission proposals (with backing votes) |
| Results | Success/Failure, loot earned, casualties |
| After-action report | GM summary of what happened |

### 4.5 Ledger Entry (Immutable)

The ledger is an append-only log. It is the source of truth for all ship state changes.

| Field | Description |
|---|---|
| Date | When the event occurred |
| Session | Linked session (if applicable) |
| Event type | Mission Completed, Mission Failed, Character Death, Level Up, Equipment Purchase, Reward Distribution |
| Description | Human-readable summary |
| Fuel delta | Fuel burned or earned |
| Crystal delta | Crystals earned or spent |
| Credit delta | Credits earned or spent |
| XP delta | XP distributed |
| Ship state snapshot | Ship level, fuel, crystals, credits after this entry |

### 4.6 Additional Entities

- **Item** — item definitions with name, description, and properties.
- **Store Item** — items available for purchase with Scrip (price, stock).
- **Inventory Item** — items owned by a character.
- **Hex Map** — campaign map definition with hex tiles.
- **Hex** — individual hex tile with terrain type, coordinates, notes, discovered status, and linked missions/locations.
- **Generated Adventure** — AI-generated adventure data with structured acts, scenes, and LLM metadata.
- **Sign-up** — join record linking a character to a mission/session.
- **Session Proposal** — a player-submitted mission suggestion for a session slot, with backer votes.

---

## 5. Key Screens

### 5.1 Dashboard (Home)

**Purpose:** Single pane of glass. See everything at a glance without navigating.

**Ship status panel** showing name, level, success rate, fuel bar (visual gauge), crystal count, credit balance, and a derived status indicator (nominal / low fuel / critical). The MOTD or latest GM announcement appears here if set.

**Upcoming missions** — the next 2–3 missions with title, hex, fuel cost, reward summary, sign-up count vs. needed, and a sign-up button. A "View mission board" link leads to the full list.

**Latest ledger entries** — the last 5 entries showing date, event type, resource deltas, and a short description. A "View full ledger" link leads to the complete history.

**Active crew summary** — a compact list of active characters with name, class, level, mission count, and last-active date. Dead characters appear with a marker and death date. A "Manage roster" link leads to the full crew roster.

**Actions available from this screen:** view full ledger, create new mission (GM), sign up for a mission, view ship details, manage roster.

### 5.2 Mission Board

**Purpose:** Browse all available and past missions. Sign up for upcoming ones. Propose missions for open session slots.

Each mission card shows title, hex, difficulty, fuel cost, reward summary, risk level, expected crew size, description excerpt, sign-up deadline, and current sign-up names with a count of how many more are needed. Expand a card for full description, GM notes (GM only), signed-up characters with player names, and post-mission summary (if complete).

**Sorting:** by date, fuel cost, reward, difficulty. **Filtering:** upcoming / past, by difficulty, by fuel cost, by reward, by status (open / full / completed / failed / cancelled).

**Session proposals:** For open session slots, players can propose a mission and other players can "back" the proposal to vote on what to play. The board should clearly explain the proposal/backing flow with inline guidance for new users.

### 5.3 Mission Detail / Sign-up

**Purpose:** View a single mission in full detail, sign up characters, or review results.

**For upcoming missions:** full description (Markdown rendered), schedule, GM name, sign-up deadline, current sign-ups with character details, and a character selector for signing up. Players see their eligible characters with checkboxes. Clear confirmation after sign-up.

**For completed missions:** result (succeeded/failed), fuel burned, loot earned, casualties listed, full party roster with survival status, GM after-action notes, and linked ledger entries from the session.

### 5.4 Ledger

**Purpose:** Immutable, transparent history of all resource transactions.

Displayed as a table or timeline with columns for date, event type, description, fuel delta, crystal delta, credit delta, XP delta, and ship state snapshot after the entry.

**Filtering:** by date range, by event type, by mission, by character. **Export:** CSV and JSON for record-keeping.

### 5.5 Ship Management (GM Only)

**Purpose:** Adjust ship state, manage missions, post updates.

**Ship editor** with fields for name, level, max fuel, current fuel, crystals, credits. **Quick actions:** create mission, log session result, record character death, post ship-wide announcement, edit crew roster. **Announcement editor** for the MOTD / ship memo. **Crew roster management** with add, edit, mark dead, and archive actions. **Data tools** for JSON export/import backups.

### 5.6 Character Management

**Purpose:** Create, view, and manage your characters.

**My characters list** showing each character's name, class, level, status, mission count, last active date, and actions (view, edit, retire, delete). Dead characters show an obituary link and death date.

**Character detail page** with full profile: name, class, level, player, ship, status, backstory/notes, external sheet link, inventory, Scrip balance, XP, and mission history (list of sessions with outcomes). Edit and archive actions.

**Create new character** flow with name, class, level, description, image upload, and external sheet URL.

### 5.7 Crew Roster

**Purpose:** See all characters across all players in one sortable, filterable table.

Columns: name, class, level, player, status, missions completed, last active. Sortable by any column. Filterable by status (active / dead / benched), level, class, player, and activity recency.

### 5.8 Company Store

**Purpose:** Browse and purchase items with Scrip.

Displays available items with name, description, price, and stock. Players can purchase items which are added to their character's inventory and deducted from their Scrip balance. GMs manage the item catalog and pricing from the admin side.

### 5.9 Campaign Hex Map

**Purpose:** Visual exploration of the campaign world.

Interactive hex map showing discovered regions, terrain types, and mission locations. Clicking a hex shows its terrain, location name, notes, and any linked missions. GMs can edit hexes (terrain, discovered status, notes, linked missions) via a click-to-edit panel. The map should support smooth pan/zoom and include a terrain palette toolbar.

### 5.10 AI Adventure Generator (GM Only)

**Purpose:** Scaffold adventure outlines quickly using an LLM.

Parameters: party size, level, duration, tone, and optional mission/region context pulled from the campaign. Generates a structured 3-act adventure outline (title, hook, acts with scenes, encounters, NPCs, climax, resolution). GMs can edit before linking to a mission. Export as a Foundry VTT module (ZIP with JournalEntry documents). Generation runs asynchronously with status tracking (pending → processing → completed / failed).

---

## 6. User Flows

### 6.1 Player Sign-up Flow

1. Log in via Discord OAuth.
2. Browse the mission board or view upcoming missions on the dashboard.
3. Click "Sign up my character" on a mission.
4. Select which character to send from an eligible list.
5. Receive confirmation: "You're signed up for [Mission] on [Date]."
6. Receive reminder notifications 24 hours and 1 hour before the session.
7. Session launches (or is cancelled if minimum crew is not met).

### 6.2 Session Proposal Flow

1. GM creates an open session time slot.
2. Players propose a mission for that slot from the mission board.
3. Other players "back" a proposal to vote for it.
4. When a proposal reaches critical mass (or the GM force-confirms), it locks in.
5. The session is now scheduled with that mission. Players sign up characters.

### 6.3 GM Session Logging Flow

1. GM starts the session.
2. During or after play, GM records: mission result (success/fail), loot earned (credits, crystals, XP, items), casualties (characters killed), fuel burned, and session notes.
3. System automatically: updates ship state, logs immutable ledger entries, distributes rewards to enrolled characters, and marks dead characters.
4. Players receive notification: "Mission complete! Rewards distributed."

### 6.4 Character Death Flow

1. Character dies during a session.
2. GM marks the character as Dead in the session log.
3. Player receives notification of the death.
4. Player creates a new character (at the ship's current level).
5. New character is ready for the next mission.

---

## 7. Authentication and Roles

**Discord OAuth (default):** Users authenticate via Discord, which maps naturally to the campaign's Discord server. JWT session handling after initial auth.

**Privacy contingency:** The auth module should be provider-agnostic behind a clean interface, allowing a swap to an alternative OAuth provider (Google, self-hosted OIDC) with minimal code changes if Discord's policies become hostile.

**Roles:**

- **Player** — browse missions, propose/back sessions, sign up characters, manage inventory, purchase from the store.
- **Admin (Game Master)** — all player abilities plus: manage all game content, configure the ship, log session results, generate AI adventures, manage the store and crew roster.
- **Co-GM (future)** — limited admin rights for assistant GMs.

**Campaign scoping:** Users are scoped to a campaign. Multi-tenancy is supported; users select their campaign after authenticating.

---

## 8. Data Model

### 8.1 Tables

- **Users** — Discord auth data, campaign role.
- **Campaigns** — campaign metadata and settings.
- **Ships** — ship state per campaign.
- **Characters** — player character profiles.
- **CharacterStats** — XP and Scrip balances.
- **Items** — item definitions.
- **InventoryItems** — character → item mapping.
- **StoreItems** — store availability, price, stock.
- **Missions** — mission definitions with rewards.
- **MissionRewards** — reward entries (XP, Scrip, items) per mission.
- **Sessions** — scheduled sessions with status and capacity.
- **SessionPlayers** — character sign-ups per session.
- **SessionProposals** — player-submitted mission proposals with backers.
- **SignUps** — join table linking characters to missions.
- **Ledger** — append-only immutable log of all state changes.
- **HexMaps** — campaign map definitions.
- **Hexes** — individual hex tiles with terrain, coordinates, notes, linked missions.
- **GeneratedAdventures** — AI-generated adventure data with LLM metadata.
- **Notes** (stretch) — player or shared campaign notes.
- **Tags** (stretch) — tags for missions, items, sessions.
- **AuditLog** (stretch) — system events for admin action tracking.

### 8.2 Key Relationships

- Character belongs to a Player (User).
- Character participates in Sessions via SignUps / SessionPlayers.
- Session is linked to one Mission.
- Ledger entries reference a Session (when applicable) and are append-only.
- Missions can be linked to Hexes on the campaign map.
- Proposals belong to a Session and reference a Mission.

### 8.3 Ledger Integrity

The ledger is the source of truth for all ship state. It is append-only and immutable. Ship resource values should be derivable from the ledger at any point in time.

---

## 9. Technical Requirements

### 9.1 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | SvelteKit + TailwindCSS (DaisyUI) |
| Backend | FastAPI (Python, async) |
| Database | SQLite (default), PostgreSQL (optional) |
| Authentication | Discord OAuth with JWT |
| Real-time updates | Server-Sent Events (SSE) for live board/status updates |
| LLM integration | OpenRouter (OpenAI-compatible API), configurable model |
| Containerization | Podman + Kube YAML manifests |
| State management | Svelte stores |

### 9.2 Deployment

- Single repository with frontend + backend.
- Podman Kube YAML for dev and production (separate containers for frontend, backend, database).
- Deployment-ready for minimal cloud hosting (Fly.io, Railway, or bare VPS).
- SystemD integration via Podman Quadlet for VPS auto-start.
- CI/CD pipeline (GitHub Actions) for linting, testing, and build.

### 9.3 Design Principles

- **Mobile-friendly.** Players will sign up for missions on their phones. All screens must be responsive.
- **Markdown everywhere.** Mission descriptions, session notes, announcements, and after-action reports support Markdown.
- **Real-time where it matters.** SSE for mission board sign-up counts, session proposal status, and store inventory. Not for simultaneous editing.
- **Accessible.** Screen reader compatibility, color contrast, and keyboard navigation.
- **Dark mode.** Supported via DaisyUI theme toggle.

---

## 10. Feature Prioritization

### MVP (Launch)

- Ship dashboard with current state, fuel/crystal/credit gauges, and status indicator.
- Mission board with full CRUD, sign-ups, and Markdown descriptions.
- Session scheduling with player sign-ups and GM session logging.
- Immutable ledger with filtering and export.
- Character creation and management with external sheet links.
- Crew roster view (all characters, sortable/filterable).
- Company store (browse and purchase with Scrip).
- Role-based access (Player vs. GM).
- Discord OAuth authentication.
- Session proposal and backing system.
- GM ship management and quick actions.
- Responsive / mobile-friendly layout.
- JSON data export/import for backups.

### Post-Launch (Near-Term)

- Campaign hex map with terrain, discovered hexes, and linked missions.
- Hex map editor for GMs (click-to-edit, terrain palette, pan/zoom).
- AI-assisted adventure generation with Foundry VTT export.
- Email or push notification reminders (sign-up deadline, session time).
- Character death notifications.
- In-app notifications panel.
- Audit logs for admin actions.
- Search and filtering across missions, items, and sessions.
- Dark mode toggle.

### Future (Stretch)

- Mission difficulty / risk calculator.
- Automated crew leveling votes.
- Attendance tracking and badges.
- Crew statistics (success rate by party composition, most dangerous hex, etc.).
- GM session prep checklist.
- Discord bot integration (post ledger updates to the server).
- Alternative OAuth providers (Google, OIDC).
- Enhanced AI tools (NPC dialogue, encounter balancing, loot tables).
- Foundry VTT plugin for bidirectional sync.
- Dice roller (lightweight command syntax).
- WebSocket support for richer real-time collaboration.
- Session notes / journals for players.
- Tags and advanced filtering.
- Offline-first PWA with service worker caching.
- Plugin system for house rules and custom modules.
- Test data seeder for demos.
- Error and health monitoring (Sentry, Prometheus).

---

## 11. UX Guidelines

### General Principles

- **Scannable at a glance.** The dashboard and mission board should communicate state through visual hierarchy—gauges, color-coded status badges, and progress indicators—not walls of text.
- **Progressive disclosure.** Show summaries by default; let users expand for detail. Mission cards show key stats up front; full descriptions and GM notes expand on click.
- **Guide new users.** The session proposal/backing system is unintuitive for newcomers. Use inline tooltips, a brief "How It Works" explainer on first visit, and clear visual states for proposal progress (proposed → backing → confirmed).
- **Minimize clicks for common actions.** Signing up for a mission should take two clicks from the dashboard. Logging a session result should be a single form.

### Specific UX Improvements Identified

- **Mission board:** needs strong visual hierarchy so rewards, sign-up status, and difficulty are scannable without reading descriptions.
- **Admin mission form:** the current modal with many fields is unwieldy. Consider a multi-step wizard or dedicated page.
- **Hex map editor:** should use a click-to-edit side panel, smooth pan/zoom, a terrain palette toolbar, and batch-edit for painting regions.
- **Session tools:** the relationship between sessions, proposals, missions, and backing needs to be visually obvious with clear state labels and progress bars.

---

## 12. Success Metrics

### Launch

- 5+ players signed up and active.
- First 3 missions run and logged.
- Ledger has 10+ entries with no data loss or corruption.
- Players can sign up for a mission end-to-end on mobile.

### Growth

- Session attendance rate above 75%.
- 2+ missions per week running.
- Players return for consecutive sessions.
- GM prep time reduced (qualitative feedback).
- Store and inventory system actively used.

---

## 13. Assumptions and Constraints

- User authentication infrastructure is provided (Discord OAuth).
- Character stats and combat mechanics are handled in Foundry VTT or D&D Beyond, not in the Hub.
- Fuel cost is flat per mission (not per character or per long rest).
- Ship-to-ship combat is out of scope; only mission logistics matter.
- The ledger is the canonical source of truth for all ship resource state.
- AI adventure generation requires an OpenRouter API key configured by the self-hoster.
- Initial deployment targets a single GM. Co-GM support is a future enhancement.

---

## 14. Open Questions

- Should the proposal backing threshold be configurable per campaign, or fixed (e.g., majority of active players)?
- How should crystal and fuel costs scale with ship level? Is this GM-configured or formulaic?
- Should dead characters' Scrip and inventory transfer to the player's next character, or reset?
- What is the minimum viable hex map experience for MVP, vs. deferring the map entirely to post-launch?
- Should the store support limited-time or mission-exclusive items?
