# Spelljammer Westmarches Hub — Product Requirements Document

## 1. Product Overview

Spelljammer Westmarches Hub is a web-based campaign management platform for running West Marches–style D&D 5e games set aboard a persistent sentient ship. It provides a centralized place for players and Game Masters to coordinate sessions, manage missions, track the ship's economy, and keep a transparent record of everything that happens in the campaign.

**Core value proposition:** Enable Westmarches play where attendance is optional but consequences are real, through a single pane of glass that keeps every player informed and every resource accounted for.

The application is designed for easy self-hosting using containers (Podman/Docker), with a SvelteKit frontend, FastAPI backend, and SQLite by default (PostgreSQL optional). Character stats and sheets are managed in external tools (Foundry VTT or D&D Beyond); the Hub handles campaign logistics, economy, and coordination.

**Initial scope:** 1 GM and 5–10 players per deployment. A single deployment can host multiple campaigns (multi-tenancy).

---

## 2. Goals and Objectives

- **Streamline campaign logistics.** Centralize session scheduling, mission management, ship resources, and the in-game economy so the GM spends less time bookkeeping and more time storytelling.
- **Enable player agency.** Give players a clear mission board, session proposal system, and item store — empowering them to drive the campaign's direction.
- **Make consequences transparent.** An immutable ledger tracks every resource change, death, and mission outcome. No ambiguity about ship state.
- **Complement external tools.** Integrate with Foundry VTT and D&D Beyond rather than replacing them. Character stats live where they're best managed.
- **Augment GM creativity with AI.** Provide AI-assisted adventure generation that exports directly to Foundry VTT, accelerating prep time.
- **Enable self-hosting.** Deliver a containerized application deployable with minimal setup.

---

## 3. Target Audience

- **Players** — browse missions, propose and sign up for sessions, manage their inventory, and track ship status.
- **Game Masters** — run and manage the campaign, create missions, log session outcomes, configure the ship, and use AI-assisted prep tools.
- **Self-hosters and hobbyists** — people who prefer running their own apps with Docker/Podman on a VPS or cloud host.

---

## 4. Core Entities

### 4.1 Ship

The ship is the persistent hub of the campaign. Its state is always visible and always current.

Essence is the ship's single resource — it functions simultaneously as fuel, as the leveling currency, and as the pool from which recovery costs are drawn. There is no separate fuel, crystal, credit, or XP counter.

| Field | Description |
|---|---|
| Name | Ship name |
| Level | Current crew level (1–20), unlocked when Essence reserves reach the next threshold |
| Essence reserve | Current stored Essence |
| Level threshold | Essence required to unlock the next level |
| Success rate | Missions succeeded / total missions (percentage) |
| Crew roster | All characters (active, dead, benched) |
| Status | Derived from Essence relative to threshold: Nominal / Low / Critical |
| Announcement / MOTD | GM-editable text for ship memos and news |
| Created date | When the campaign ship was established |

**Leveling:** The crew advances when stored Essence reaches the next threshold. An achieved level is never lost even if reserves drop — but advancement stalls until reserves recover.

**Starting level:** The campaign opens at level 3. The ship's Essence reserve starts at 10 (the level 3 threshold).

### 4.2 Character

Characters belong to players. A player may have multiple characters (one active at a time). Stats and detailed sheets are managed externally. There is no per-character currency — Essence is a shared ship resource.

| Field | Description |
|---|---|
| Name | Character name |
| Player | Owning player |
| Class / Level | D&D class and current level (always matches ship level) |
| Description | Optional flavor text or backstory |
| Image | Character portrait (optional) |
| External sheet link | URL to Foundry VTT or D&D Beyond sheet |
| Status | Active, Dead, or Benched |
| Inventory | Magic items carried (equipped to this character) |
| Missions completed | Count of completed missions |
| Joined date | When the character was created |
| Date of death | If applicable |

**New characters** enter at the ship's current level. Dead characters are replaced; the new character is a different person at the same level. The ledger remembers both.

### 4.3 Mission

Missions are the unit of adventure. They live on the mission board until completed or retired.

| Field | Description |
|---|---|
| Title | Mission name |
| Hex location | Map reference |
| Difficulty | Routine / Standard / Hard / Extreme |
| Risk level | Flavor label: Low / Medium / High / Unknown |
| Essence payout (gross) | Total Essence posted on the board — transit is automatically deducted before reaching reserves |
| Expected crew size | Recommended party size |
| Item rewards | Specific items available as mission loot |
| Description | GM briefing (supports Markdown) |
| Status | Available → In Progress → Completed / Failed / Retired |
| Created by | GM who authored it |
| Scheduled date/time | When the session is planned |
| Sign-up deadline | Cutoff for player sign-ups |
| Cooldown | Optional cooldown before mission can repeat |
| Discoverable | Whether the mission appears on the board or must be found in play |

**Transit:** Essence consumed traveling to and from the hex is deducted from the gross payout automatically when the session is logged. The posted number is what the crew sees before transit. GMs factor hex distance into the gross bounty — a far hex gets a higher posted reward than a nearby one of equivalent difficulty.

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
| Results | Success/Failure, Essence earned (net after transit), loot recovered, casualties |
| Field report | Player-authored after-action summary (optional, submitted post-session) |
| After-action report | GM summary of what happened |

### 4.5 Ledger Entry (Immutable)

The ledger is an append-only log. It is the source of truth for all ship state changes. Nothing is ever edited or deleted — corrections are new entries explaining the correction.

| Field | Description |
|---|---|
| Date | When the event occurred |
| Session | Linked session (if applicable) |
| Event type | Mission Completed, Mission Failed, Long Rest, Level Up, Item Purchase, Item Attuned to Ship, Character Death, Sacrifice Draw, Manual Adjustment |
| Description | Human-readable summary |
| Essence delta | Essence added to or drawn from reserves (negative = spent) |
| Ship state snapshot | Ship level and Essence reserve after this entry |

**The ledger is sacred.** Players can always see the full history. Transparent economics make hard decisions feel earned.

### 4.6 Additional Entities

- **Item** — item definitions with name, rarity, description, and properties.
- **Inventory Item** — character → item mapping. An item equipped to a character travels with them.
- **Ship-Attuned Item** — items permanently integrated into the ship's hull for campaign-wide persistent benefits. Not tied to any individual character.
- **Store Item** — items available for purchase with Essence (price in Essence, stock).
- **Hex Map** — campaign map definition with hex tiles.
- **Hex** — individual hex tile with terrain type, coordinates, state (wilderness / claimed / friendly / contested / awakened), controlling faction, player notes, discovered status, and linked missions.
- **Generated Adventure** — AI-generated adventure data with structured acts, scenes, and LLM metadata.
- **Session Proposal** — a player-submitted mission suggestion for a session slot, with backer votes.
- **Faction Reputation** — ship-level standing with named factions, tracked by event log.

---

## 5. Key Screens

### 5.1 Dashboard (Home)

**Purpose:** Single pane of glass. See everything at a glance without navigating.

**Character identity banner** — the player's active character's name, class, level, and missions completed, shown prominently. New players without a character see an in-world onboarding prompt.

**Ship status panel** showing name, current Essence reserve, level threshold progress (reserve vs. next threshold), derived status (Nominal / Low / Critical), and the MOTD or latest GM announcement.

**Session board** — upcoming sessions with proposal progress bars and a "Back This" toggle. Confirmed sessions show the locked mission and party. Empty state for no upcoming sessions.

**Available contracts** — up to 6 discoverable missions displayed inline without leaving the page, with cooldown indicators.

**Actions available from this screen:** back a session proposal, view full mission board, sign up for a confirmed session, view full ledger.

### 5.2 Mission Board

**Purpose:** Browse all available and past missions. Sign up for upcoming ones. Propose missions for open session slots.

Each mission card shows title, hex, difficulty, Essence payout (gross), risk level, expected crew size, description excerpt, sign-up deadline, and current sign-up names with a count of how many more are needed. Expand a card for full description, GM notes (GM only), signed-up characters with player names, and post-mission summary (if complete).

**Sorting:** by date, Essence payout, difficulty. **Filtering:** upcoming / past, by difficulty, by risk level, by status (open / full / completed / failed / cancelled).

**Session proposals:** For open session slots, players can propose a mission and other players can "back" the proposal to vote on what to play. The board should clearly explain the proposal/backing flow with inline guidance for new users.

### 5.3 Mission Detail / Sign-up

**Purpose:** View a single mission in full detail, sign up characters, or review results.

**For upcoming missions:** full description (Markdown rendered), schedule, GM name, sign-up deadline, current sign-ups with character details, and a character selector for signing up. Clear confirmation after sign-up.

**For completed missions:** result (succeeded/failed), Essence earned (net after transit), transit deducted, items recovered, casualties listed, full party roster with survival status, field reports submitted by players, GM after-action notes, and linked ledger entries from the session.

### 5.4 Ledger

**Purpose:** Immutable, transparent history of all Essence transactions.

Displayed as a table or timeline with columns for date, event type, description, Essence delta, and ship state snapshot (level + reserve) after the entry.

**Filtering:** by date range, by event type, by mission, by character. **Export:** CSV and JSON for record-keeping.

### 5.5 Ship Management (GM Only)

**Purpose:** Adjust ship state, manage missions, post updates.

**Ship editor** with fields for name, current Essence reserve (manual adjustment with required ledger note). **Quick actions:** create mission, log session result, record character death, post ship-wide announcement, manage crew roster, attune item to ship. **Announcement editor** for the MOTD / ship memo. **Crew roster management** with add, edit, mark dead, and archive actions. **Data tools** for JSON export/import backups.

### 5.6 Character Management

**Purpose:** Create, view, and manage your characters.

**My characters list** showing each character's name, class, level, status, mission count, last active date, and actions (view, edit, retire, delete). Dead characters show an obituary link and death date.

**Character detail page** with full profile: name, class, level, player, status, backstory/notes, external sheet link, inventory (items equipped to this character), and mission history (list of sessions with outcomes). Edit and archive actions.

**Create new character** flow with name, class, level, description, image upload, and external sheet URL.

### 5.7 Crew Roster

**Purpose:** See all characters across all players in one sortable, filterable table.

Columns: name, class, level, player, status, missions completed, last active. Sortable by any column. Filterable by status (active / dead / benched), level, class, player, and activity recency.

### 5.8 Item Store

**Purpose:** Browse and purchase items with Essence.

Displays available items with name, rarity, description, and Essence price. Players can purchase items (Essence drawn from ship reserves, item added to character inventory, ledger entry recorded). GMs manage the item catalog and pricing. Rare and above items recovered from derelicts are integrated separately via the Ship Management screen, not sold through the store.

### 5.9 Campaign Hex Map

**Purpose:** Visual exploration of the campaign world.

Interactive hex map showing discovered regions, terrain types, hex state (wilderness / claimed / friendly / contested / awakened), controlling faction, and mission locations. Clicking a hex shows its terrain, state, faction, player notes, and linked missions. Players can leave notes on discovered hexes. GMs can edit hexes (terrain, state, faction, notes, discovered status, linked missions) via a click-to-edit panel. The map supports smooth pan/zoom and includes a terrain legend.

### 5.10 AI Adventure Generator (GM Only)

**Purpose:** Scaffold adventure outlines quickly using an LLM.

Parameters: party size, level, tone, revelation layer (early / mid / late campaign), and context pulled from the campaign (faction reputations, discovered hexes, recent field reports). Generates a structured adventure outline. GMs can edit before linking to a mission. Generation runs asynchronously with status tracking (pending → processing → completed / failed).

---

## 6. User Flows

### 6.1 Player Sign-up Flow

1. Log in via Discord OAuth.
2. Browse the mission board or view upcoming sessions on the dashboard.
3. Back a session proposal or sign up for a confirmed session.
4. Select which character to send from an eligible list.
5. Receive confirmation: "You're signed up for [Mission] on [Date]."
6. Session launches (or is cancelled if minimum crew is not met).

### 6.2 Session Proposal Flow

1. GM creates an open session time slot.
2. Players propose a mission for that slot from the mission board.
3. Other players "back" a proposal to vote for it.
4. When a proposal reaches critical mass (or the GM force-confirms), it locks in.
5. The session is now scheduled with that mission. Players sign up characters.

### 6.3 GM Session Logging Flow

1. GM starts the session.
2. During or after play, GM records: mission result (success/fail), Essence earned (gross), transit deducted (auto-calculated from tier), items recovered, casualties, and session notes.
3. System automatically: deducts transit from gross to compute net Essence, updates ship Essence reserve, checks if reserve has crossed a level threshold, logs immutable ledger entries, and marks dead characters.
4. Players receive notification: "Mission complete. Net Essence to reserves: [X]."

### 6.4 Long Rest Flow

1. GM records a long rest during or after a session.
2. System deducts the tier-appropriate Essence cost from reserves and logs the ledger entry.
3. If reserves drop below a level threshold, advancement stalls — the achieved level is not lost.
4. If reserves reach critically low levels, the sacrifice mechanic may trigger (GM records; Meridian covers costs from structural budget, degradation revealed next session).

### 6.5 Character Death Flow

1. Character dies during a session.
2. GM marks the character as Dead in the session log.
3. Player creates a new character (at the ship's current level).
4. New character is ready for the next mission. The ledger preserves the dead character's full history.

### 6.6 Magic Item Fate Flow

When an item is recovered from a mission, the crew decides its fate:

- **Equip to a character** — standard attunement. Item lives in the character's inventory. If the character dies or retires, the item fate must be decided again.
- **Attune to ship** — GM integrates the item into Meridian's hull via Ship Management. Essence cost logged to ledger. Benefit is permanent and campaign-wide. Item does not leave with any individual character.

---

## 7. Authentication and Roles

**Discord OAuth (default):** Users authenticate via Discord, which maps naturally to the campaign's Discord server. JWT session handling after initial auth.

**Privacy contingency:** The auth module should be provider-agnostic behind a clean interface, allowing a swap to an alternative OAuth provider (Google, self-hosted OIDC) with minimal code changes if Discord's policies become hostile.

**Roles:**

- **Player** — browse missions, propose/back sessions, sign up characters, manage inventory, purchase from the store.
- **Admin (Game Master)** — all player abilities plus: manage all game content, configure the ship, log session results, generate AI adventures, manage the store and crew roster, attune items to the ship.
- **Co-GM (future)** — limited admin rights for assistant GMs.

**Campaign scoping:** Users are scoped to a campaign. Multi-tenancy is supported; users select their campaign after authenticating.

---

## 8. Data Model

### 8.1 Tables

- **Users** — Discord auth data, campaign role.
- **Campaigns** — campaign metadata and settings.
- **Ships** — ship state per campaign (name, current Essence reserve, derived level).
- **Characters** — player character profiles (no per-character currency or XP).
- **Items** — item definitions with name, rarity, description, properties.
- **InventoryItems** — character → item mapping (items equipped to a character).
- **ShipAttunemements** — items permanently integrated into the ship's hull, with GM-defined persistent benefit.
- **StoreItems** — items available for purchase with Essence (price, stock).
- **Missions** — mission definitions with gross Essence payout and item rewards.
- **Sessions** — scheduled sessions with status and capacity.
- **SessionPlayers** — character sign-ups per session.
- **SessionProposals** — player-submitted mission proposals with backers.
- **Ledger** — append-only immutable log of all state changes; each entry has an Essence delta and ship state snapshot.
- **HexMaps** — campaign map definitions.
- **Hexes** — individual hex tiles with terrain, coordinates, state, controlling faction, player notes, discovered status, linked missions.
- **FactionReputations** — ship-level standing per faction, backed by an event log.
- **GeneratedAdventures** — AI-generated adventure data with LLM metadata.
- **Notes** (stretch) — player or shared campaign notes.
- **Tags** (stretch) — tags for missions, items, sessions.
- **AuditLog** (stretch) — system events for admin action tracking.

### 8.2 Key Relationships

- Character belongs to a Player (User).
- Character participates in Sessions via SessionPlayers.
- Session is linked to one Mission.
- Ledger entries reference a Session (when applicable) and are append-only.
- Missions can be linked to Hexes on the campaign map.
- Proposals belong to a Session and reference a Mission.
- ShipAttunements belong to the Ship, not any Character.

### 8.3 Ledger Integrity

The ledger is the source of truth for all ship state. It is append-only and immutable. The ship's current Essence reserve is derivable from summing all ledger Essence deltas. Leveling is recorded as a ledger event when the threshold is crossed — it has no Essence cost.

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
- **Markdown everywhere.** Mission descriptions, session notes, announcements, field reports, and after-action reports support Markdown.
- **Real-time where it matters.** SSE for mission board sign-up counts, session proposal status, and store inventory. Not for simultaneous editing.
- **Accessible.** Screen reader compatibility, color contrast, and keyboard navigation.
- **Dark mode.** Supported via DaisyUI theme toggle.

---

## 10. Feature Prioritization

### MVP (Launch)

- Ship dashboard with character identity banner, Essence reserve / level threshold display, session board, and available contracts.
- Mission board with full CRUD, sign-ups, Markdown descriptions, and Essence payout display.
- Session scheduling with player sign-ups and GM session logging (including transit auto-deduction).
- Immutable Essence ledger with filtering and export.
- Character creation and management with external sheet links and inventory.
- Crew roster view (all characters, sortable/filterable).
- Item store (browse and purchase with Essence; ledger entry auto-created).
- Role-based access (Player vs. GM).
- Discord OAuth authentication.
- Session proposal and backing system.
- GM ship management and quick actions.
- Responsive / mobile-friendly layout.
- JSON data export/import for backups.

### Post-Launch (Near-Term)

- Campaign hex map with terrain, hex state, faction control, player notes, and linked missions.
- Hex map editor for GMs (click-to-edit, terrain palette, pan/zoom).
- Ship item attunement flow with GM-defined persistent benefit and ledger entry.
- AI-assisted adventure generation with campaign context (factions, hexes, field reports).
- Field reports (player-authored post-session summaries, surfaced in mission detail and AI context).
- Email or push notification reminders (sign-up deadline, session time).
- Character death notifications.
- In-app notifications panel.
- Audit logs for admin actions.
- Search and filtering across missions, items, and sessions.

### Future (Stretch)

- Mission difficulty / risk calculator.
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

- **Scannable at a glance.** The dashboard and mission board should communicate state through visual hierarchy — Essence gauge, level threshold progress, color-coded status badges — not walls of text.
- **Progressive disclosure.** Show summaries by default; let users expand for detail. Mission cards show key stats up front; full descriptions and GM notes expand on click.
- **Guide new users.** The session proposal/backing system is unintuitive for newcomers. Use inline tooltips, a brief "How It Works" explainer on first visit, and clear visual states for proposal progress (proposed → backing → confirmed).
- **Minimize clicks for common actions.** Signing up for a mission should take two clicks from the dashboard. Logging a session result should be a single form.
- **Essence is never called XP in the UI.** Always "Essence." The leveling system is D&D 5e underneath but the fiction is Essence and the UI reflects the fiction.

### Specific UX Improvements Identified

- **Mission board:** needs strong visual hierarchy so Essence payout, sign-up status, and difficulty are scannable without reading descriptions.
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
- Store and item attunement system actively used.

---

## 13. Assumptions and Constraints

- User authentication infrastructure is provided (Discord OAuth).
- Character stats and combat mechanics are handled in Foundry VTT or D&D Beyond, not in the Hub.
- Essence is the only in-game resource. There is no separate fuel, crystal, credit, or XP counter.
- Transit (travel cost) is automatically deducted from gross Essence payout when the GM logs a session result. It is not a separate input field — the system calculates it from mission tier.
- Long rest costs are drawn from the ship's shared Essence reserve, not from individual characters.
- Ship-to-ship combat is out of scope; only mission logistics matter.
- The ledger is the canonical source of truth for all ship resource state.
- AI adventure generation requires an OpenRouter API key configured by the self-hoster.
- Initial deployment targets a single GM. Co-GM support is a future enhancement.

---

## 14. Open Questions

- Should the proposal backing threshold be configurable per campaign, or fixed (e.g., majority of active players)?
- How should transit cost scale with hex distance — fixed per tier, or GM-input per mission?
- When a character dies, do equipped items return to the ship's pool for redistribution, or does the player's next character inherit them?
- What is the minimum viable hex map experience for MVP, vs. deferring the map entirely to post-launch?
- Should the store support limited-time or mission-exclusive items?
- Should ship-attuned items be visible to all players, or GM-only until the benefit is announced?
