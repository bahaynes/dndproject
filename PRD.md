# Spelljammer Westmarches Hub — Product Requirements Document

## 1. Product Overview

Spelljammer Westmarches Hub is a web-based campaign management platform for running West Marches–style D&D 5e games set aboard a persistent sentient ship. It provides a centralized place for players and Game Masters to coordinate sessions, manage missions, track the ship's economy, and keep a transparent record of everything that happens in the campaign.

**Core value proposition:** Enable Westmarches play where attendance is optional but consequences are real, through a single pane of glass that keeps every player informed and every resource accounted for.

The application is designed for easy self-hosting using containers (Podman/Docker), with a SvelteKit frontend, FastAPI backend, and SQLite by default (PostgreSQL optional). Character stats and sheets are managed in external tools (Foundry VTT or D&D Beyond); the Hub handles campaign logistics, economy, and coordination.

**Initial scope:** 1 GM and 5–10 players per deployment. A single deployment can host multiple campaigns (multi-tenancy).

---

## 2. Setting and Narrative Framework

### 2.1 The World

The campaign takes place in a Spelljammer-esque meteor belt known as the Limes — a lawless frontier far from the reach of the Collegium, the dominant political power in the core worlds. The Limes is not governed so much as it is tolerated. Its people are independent, dangerous, and poor by design.

The Collegium understands something that most people in the Limes have forgotten or never knew: classed individuals — people who have gained levels — are weapons of mass destruction in a world where everyone else is a level 1 commoner. A level 10 fighter is not just a skilled warrior. She is a one-person army. The Collegium's political survival depends on controlling who gains levels, and how many.

Rather than suppress the Limes outright, the Collegium has engineered a more elegant trap: an extractive economy that keeps the frontier perpetually destitute. Salvage crews collect Essence from the outer ring — a physical substance left behind by ancient cataclysms — and sell it to Collegium brokers at prices just high enough to survive, but never high enough to accumulate real power. The system is self-cleaning. Most crews die before they level high enough to matter. The few who survive long enough get recruited or disappear.

### 2.2 The Vincula

Interstellar travel in the Limes is made possible by the Vincula — ancient sentient beings, survivors of a cataclysm that predates recorded history, who have taken the form of ships. A Vincula does not simply carry a crew; it grants them class levels by channeling Essence through its hull, raising the crew's capabilities as its own reserves grow.

Every salvage crew in the Limes operates aboard a Vincula. Most crew members don't fully understand what their ship is. They know some ships are luckier than others, that Essence somehow makes you better at fighting or casting, and that the open market will pay well for the stuff. The deeper truth — that their ship is a centuries-old survivor quietly feeding them power in exchange for their labor — is not widely known.

The Vincula are individualistic. They have their own politics, their own memories of the cataclysm, their own opinions about the Collegium. Some have made their peace with the extractive economy. Others are quietly building toward something. None of them are fully free.

### 2.3 Meridian

The player characters serve aboard Meridian, a Vincula of significant age who remembers the cataclysm personally. Meridian is not powerful by choice — she is powerful by survival instinct. For centuries, she has sold Essence to stay afloat: paying protection, bribing brokers, keeping her reserve just high enough to maintain a skeleton crew and avoid drawing attention. Level 3 is not weakness. It is scar tissue.

Meridian is now taking a calculated risk. Rather than continuing to trickle Essence to Collegium brokers, she is investing in a crew with the goal of building enough reserves to actually level — to grow beyond the threshold where the extractive economy can threaten her survival. She does not frame this as rebellion. She frames it as business. But she remembers what the Collegium did the last time someone accumulated too much power.

The players don't need to know any of this at the start. They're salvagers who found a posting on a job board. The pay is decent, the ship feels right, and the captain — Meridian's voice through whatever interface she uses — seems to actually care whether they come home alive.

### 2.4 The Core Tension

The player incentives and Meridian's goals are naturally aligned:

- Meridian does not want to sell Essence, because selling Essence means staying weak.
- Players do not want to sell Essence, because selling Essence means losing levels.
- The Collegium's trap only closes when the crew runs out of gold — the operational currency that covers fuel, repairs, and consumables.
- A string of failed missions doesn't just feel bad. It threatens the choice between selling levels or grounding the ship.

This tension does not need to be explained to players. It emerges from the incentive structure. The macro politics of the setting reveal themselves through the micro decisions of individual sessions.

---

## 3. Game Design Rules

### 3.1 The Essence Economy

**Essence** is a physical substance collected during missions in the outer ring. It is the ship's leveling currency and the most politically charged resource in the setting. It is never called XP in the UI or at the table.

**Gold** is the operational currency. It covers fuel, repairs, consumables, and anything else that keeps the ship flying between missions. Gold comes from mission loot, salvage, and trade. It does not directly affect leveling.

These are two separate economies with separate failure modes:

- Running out of Essence stalls leveling but doesn't ground the ship.
- Running out of gold threatens the ship's operation — and in extremis, forces the crew to consider selling Essence to the Collegium to cover costs.

The moment a table discusses selling Essence to pay for repairs is the moment the setting's politics become personal.

### 3.2 Ship Leveling

Meridian raises the entire crew to her current level simultaneously. There are no individual character levels — the ship's Essence reserve determines crew level. All characters are always the same level.

**Key rules:**

- Achieved levels are never lost, even if Essence reserves drop below a threshold.
- Advancement stalls if reserves cannot reach the next threshold.
- New characters join at the ship's current level. Dead characters are replaced at no level cost — a new person walks up the gangplank at the same power as everyone else.
- More crew means the same Essence is distributed thinner. This is a narrative truth, not a mechanical one — it explains why Meridian is selective about who she recruits.

**Starting level:** The campaign opens at level 3. Meridian's reserves start at 10 (the level 3 threshold). She has spent centuries selling down to this floor.

### 3.3 Ship-Flavored Abilities

The central mechanical conceit of the campaign is the ship-flavored ability system. Players are not required to learn a separate ship combat system. Instead, they are invited — and rewarded — for describing their existing class abilities as channeled through Meridian.

The canonical example: a wizard's Fireball. If the wizard describes it as Meridian firing her cannons, the ability is ship-flavored. If the wizard describes it as her own arcane power, it is not. The player chooses. The GM rewards the choice.

**This system has three rules:**

**Rule 1 — Damage abilities.** Ship-flavored abilities that deal damage use 1.5x the normal number of damage dice. A Fireball that normally rolls 8d6 rolls 12d6 when fired as ship artillery. This is intentionally powerful. It is meant to feel gamebreaking, because it carries real costs.

**Rule 2 — Non-damage abilities.** Ship-flavored abilities that do not deal damage gain a bonus equal to Meridian's proficiency bonus (which matches the crew's proficiency bonus at their current level). This scales naturally as the crew levels up. It stacks with Expertise, which can produce significant results at high levels — and that is by design.

**Rule 3 — Positioning.** Ship-flavored abilities only apply when Meridian is in range and line of effect. Underground, inside a structure, or in situations where the ship cannot plausibly provide support, the ability functions normally without the bonus. The player and GM negotiate this together. When in doubt, the flavor should drive the ruling.

### 3.4 The True Cost of Ship Support

Ship-flavored abilities are not free. Their costs are:

**Transit cost.** Essence is spent traveling to and from mission hexes. Farther missions cost more Essence to reach, reducing net payout. This is deducted automatically when a session is logged.

**Ship damage.** Positioning Meridian for artillery support exposes her to enemy fire, environmental hazards, and Collegium surveillance. A ship in firing position is a ship taking risks. Damage is repaired with gold — not Essence — preserving the separation between the leveling economy and the operational economy.

**Exposure.** Every time Meridian fires openly, she broadcasts her position and capabilities. In a setting where the Collegium is watching for Vincula that are accumulating too much power, repeated use of ship support in populated areas or on high-profile missions carries narrative consequences that the GM tracks over time.

These costs mean that calling in ship support is a genuine tactical and strategic decision. The 1.5x damage bonus is substantial by design — it needs to feel worth the risk.

### 3.5 Enemy Scaling

The campaign uses Fourth Edition minion rules layered over Fifth Edition. Many enemies have 1 HP and go down in a single hit, creating the feel of an overwhelming horde without the action economy collapse that would normally result. However, minions still act on their turn and can deal meaningful damage — the danger is real at the start of an encounter before the party has cleared the field.

Ship support shines against minion swarms. A ship-flavored Fireball clearing a wave of one-HP enemies feels exactly like calling in an orbital strike in Helldivers. This is intentional.

Elite and boss enemies are scaled to account for the possibility of ship support. Encounters designed in open terrain where the ship can participate are built assuming it will. Encounters inside structures or underground are built without that assumption. The GM designs around which tool set the party actually has available, not the maximum possible.

### 3.6 The Helldivers and Firefly Duality

Ship support expresses itself in two distinct modes, both valid:

**Artillery mode (Helldivers).** The ship provides direct offensive support — cannon fire, laser targeting, orbital strikes. This amplifies damage abilities and is the primary use of ship-flavored offensive spells and attacks. The ship is visibly present and actively engaged.

**Presence mode (Firefly).** The ship's silhouette, reputation, or proximity changes the social dynamic of an encounter. A standoff that might end in violence ends differently when Meridian rises over the tree line. This is primarily expressed through ship-flavored social abilities — Intimidation, Persuasion, Deception — gaining the proficiency bonus benefit when the crew can credibly invoke the ship's presence.

Both modes require the same thing: the crew has to set it up. The artillery has to be in range. The ship has to be visible. Good positioning gets rewarded. Poor planning means falling back on personal abilities alone.

---

## 4. Goals and Objectives

- **Streamline campaign logistics.** Centralize session scheduling, mission management, ship resources, and the in-game economy so the GM spends less time bookkeeping and more time storytelling.
- **Enable player agency.** Give players a clear mission board, session proposal system, and item store — empowering them to drive the campaign's direction.
- **Make consequences transparent.** An immutable ledger tracks every resource change, death, and mission outcome. No ambiguity about ship state.
- **Complement external tools.** Integrate with Foundry VTT and D&D Beyond rather than replacing them. Character stats live where they're best managed.
- **Augment GM creativity with AI.** Provide AI-assisted adventure generation that exports directly to Foundry VTT, accelerating prep time.
- **Enable self-hosting.** Deliver a containerized application deployable with minimal setup.

---

## 5. Target Audience

- **Players** — browse missions, propose and sign up for sessions, manage their inventory, and track ship status.
- **Game Masters** — run and manage the campaign, create missions, log session outcomes, configure the ship, and use AI-assisted prep tools.
- **Self-hosters and hobbyists** — people who prefer running their own apps with Docker/Podman on a VPS or cloud host.

---

## 6. Core Entities

### 6.1 Ship

The ship is the persistent hub of the campaign. Its state is always visible and always current.

Essence is the ship's leveling currency — a physical substance collected in the outer ring. Gold is the operational currency covering fuel, repairs, and consumables. These are tracked separately and serve different functions.

| Field | Description |
|---|---|
| Name | Ship name (Meridian by default) |
| Level | Current crew level (1–20), unlocked when Essence reserves reach the next threshold |
| Essence reserve | Current stored Essence |
| Gold | Current party gold for operational expenses |
| Hull integrity | Current ship health as a percentage; reduced by damage during ship-support positioning |
| Level threshold | Essence required to unlock the next level |
| Success rate | Missions succeeded / total missions (percentage) |
| Crew roster | All characters (active, dead, benched) |
| Status | Derived from Essence relative to threshold: Nominal / Low / Critical |
| Announcement / MOTD | GM-editable text for ship memos and news |
| Created date | When the campaign ship was established |

**Leveling:** The crew advances when stored Essence reaches the next threshold. An achieved level is never lost even if reserves drop — but advancement stalls until reserves recover.

**Starting level:** The campaign opens at level 3. The ship's Essence reserve starts at 10 (the level 3 threshold).

**Hull integrity:** Damage is logged as a percentage reduction. Repairs cost gold and restore hull integrity. At 0% hull integrity, the ship is grounded and cannot depart on missions until repaired. Hull integrity is tracked in the ledger like any other ship state change.

### 6.2 Character

Characters belong to players. A player may have multiple characters (one active at a time). Stats and detailed sheets are managed externally. There is no per-character currency — Essence and gold are shared ship resources.

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
| Ship-flavored abilities | Player-noted list of abilities they've declared as ship-channeled |
| Missions completed | Count of completed missions |
| Joined date | When the character was created |
| Date of death | If applicable |

**New characters** enter at the ship's current level. Dead characters are replaced; the new character is a different person at the same level. The ledger remembers both.

**Ship-flavored ability tracking:** Players can optionally note which of their abilities they have declared as ship-flavored. This is flavor and reference only — it does not restrict them from flavoring additional abilities at the table. The GM is the final arbiter of whether a given ability qualifies in a given situation.

### 6.3 Mission

Missions are the unit of adventure. They live on the mission board until completed or retired.

| Field | Description |
|---|---|
| Title | Mission name |
| Hex location | Map reference |
| Difficulty | Routine / Standard / Hard / Extreme |
| Risk level | Flavor label: Low / Medium / High / Unknown |
| Essence payout (gross) | Total Essence posted on the board — transit is automatically deducted before reaching reserves |
| Gold payout | Gold available as operational loot from the mission |
| Ship support viability | GM assessment: Open (ship can assist) / Restricted (partial) / None (ship cannot assist) |
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

**Ship support viability** is a GM-set field that signals to players whether positioning the ship for support is even possible on this mission. It is a planning tool, not a hard lock — the GM may rule differently at the table based on how events unfold.

### 6.4 Session

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
| Ship damage taken | Hull integrity lost during this session (logged to ledger) |
| Results | Success/Failure, Essence earned (net after transit), gold earned, loot recovered, casualties, ship damage |
| Field report | Player-authored after-action summary (optional, submitted post-session) |
| After-action report | GM summary of what happened |

### 6.5 Ledger Entry (Immutable)

The ledger is an append-only log. It is the source of truth for all ship state changes. Nothing is ever edited or deleted — corrections are new entries explaining the correction.

| Field | Description |
|---|---|
| Date | When the event occurred |
| Session | Linked session (if applicable) |
| Event type | Mission Completed, Mission Failed, Long Rest, Level Up, Item Purchase, Item Attuned to Ship, Character Death, Essence Sold, Ship Damage, Ship Repair, Manual Adjustment |
| Description | Human-readable summary |
| Essence delta | Essence added to or drawn from reserves (negative = spent) |
| Gold delta | Gold added to or spent from reserves (negative = spent) |
| Hull delta | Hull integrity change (negative = damage, positive = repair) |
| Ship state snapshot | Ship level, Essence reserve, gold, and hull integrity after this entry |

**The ledger is sacred.** Players can always see the full history. Transparent economics make hard decisions feel earned.

**Essence Sold** is a distinct event type. When the crew sells Essence to Collegium brokers, it is logged separately from mission payouts — a visible record of every concession made to the extractive economy.

### 6.6 Additional Entities

- **Item** — item definitions with name, rarity, description, and properties.
- **Inventory Item** — character → item mapping. An item equipped to a character travels with them.
- **Ship-Attuned Item** — items permanently integrated into the ship's hull for campaign-wide persistent benefits. Not tied to any individual character.
- **Store Item** — items available for purchase with gold (not Essence).
- **Hex Map** — campaign map definition with hex tiles.
- **Hex** — individual hex tile with terrain type, coordinates, state (wilderness / claimed / friendly / contested / awakened), controlling faction, ship support viability, player notes, discovered status, and linked missions.
- **Generated Adventure** — AI-generated adventure data with structured acts, scenes, and LLM metadata.
- **Session Proposal** — a player-submitted mission suggestion for a session slot, with backer votes.
- **Faction Reputation** — ship-level standing with named factions, tracked by event log.

---

## 7. Key Screens

### 7.1 Dashboard (Home)

**Purpose:** Single pane of glass. See everything at a glance without navigating.

**Character identity banner** — the player's active character's name, class, level, and missions completed, shown prominently. New players without a character see an in-world onboarding prompt.

**Ship status panel** showing name, current Essence reserve, level threshold progress (reserve vs. next threshold), hull integrity, gold reserves, derived status (Nominal / Low / Critical), and the MOTD or latest GM announcement.

**Session board** — upcoming sessions with proposal progress bars and a "Back This" toggle. Confirmed sessions show the locked mission, ship support viability, and party. Empty state for no upcoming sessions.

**Available contracts** — up to 6 discoverable missions displayed inline without leaving the page, with cooldown indicators and ship support viability badges.

**Actions available from this screen:** back a session proposal, view full mission board, sign up for a confirmed session, view full ledger.

### 7.2 Mission Board

**Purpose:** Browse all available and past missions. Sign up for upcoming ones. Propose missions for open session slots.

Each mission card shows title, hex, difficulty, Essence payout (gross), gold payout, risk level, ship support viability, expected crew size, description excerpt, sign-up deadline, and current sign-up names with a count of how many more are needed. Expand a card for full description, GM notes (GM only), signed-up characters with player names, and post-mission summary (if complete).

**Sorting:** by date, Essence payout, gold payout, difficulty. **Filtering:** upcoming / past, by difficulty, by risk level, by status (open / full / completed / failed / cancelled), by ship support viability.

**Session proposals:** For open session slots, players can propose a mission and other players can "back" the proposal to vote on what to play.

### 7.3 Mission Detail / Sign-up

**Purpose:** View a single mission in full detail, sign up characters, or review results.

**For upcoming missions:** full description (Markdown rendered), schedule, GM name, ship support viability with terrain notes, sign-up deadline, current sign-ups with character details, and a character selector for signing up.

**For completed missions:** result (succeeded/failed), Essence earned (net after transit), transit deducted, gold earned, ship damage taken, items recovered, casualties listed, full party roster with survival status, field reports submitted by players, GM after-action notes, and linked ledger entries from the session.

### 7.4 Ledger

**Purpose:** Immutable, transparent history of all resource transactions.

Displayed as a table or timeline with columns for date, event type, description, Essence delta, gold delta, hull delta, and ship state snapshot (level, reserve, gold, hull) after the entry.

**Filtering:** by date range, by event type (including filtering specifically for Essence Sold events), by mission, by character. **Export:** CSV and JSON for record-keeping.

### 7.5 Ship Management (GM Only)

**Purpose:** Adjust ship state, manage missions, post updates.

**Ship editor** with fields for name, current Essence reserve (manual adjustment with required ledger note), gold (manual adjustment with required ledger note), and hull integrity. **Quick actions:** create mission, log session result, record character death, record ship damage, record repair, post ship-wide announcement, manage crew roster, attune item to ship, log Essence sale. **Announcement editor** for the MOTD / ship memo. **Crew roster management** with add, edit, mark dead, and archive actions. **Data tools** for JSON export/import backups.

### 7.6 Character Management

**Purpose:** Create, view, and manage your characters.

**My characters list** showing each character's name, class, level, status, mission count, last active date, and actions (view, edit, retire, delete). Dead characters show an obituary link and death date.

**Character detail page** with full profile: name, class, level, player, status, backstory/notes, external sheet link, ship-flavored ability notes, inventory (items equipped to this character), and mission history (list of sessions with outcomes).

**Create new character** flow with name, class, level, description, image upload, external sheet URL, and optional ship-flavored ability notes.

### 7.7 Crew Roster

**Purpose:** See all characters across all players in one sortable, filterable table.

Columns: name, class, level, player, status, missions completed, last active. Sortable by any column. Filterable by status (active / dead / benched), level, class, player, and activity recency.

### 7.8 Item Store

**Purpose:** Browse and purchase items with gold.

Displays available items with name, rarity, description, and gold price. Players can purchase items (gold drawn from ship reserves, item added to character inventory, ledger entry recorded). GMs manage the item catalog and pricing. Rare and above items recovered from missions are integrated separately via the Ship Management screen.

### 7.9 Campaign Hex Map

**Purpose:** Visual exploration of the campaign world.

Interactive hex map showing discovered regions, terrain types, hex state, controlling faction, ship support viability by hex, and mission locations. Clicking a hex shows its terrain, state, faction, support viability, player notes, and linked missions. Players can leave notes on discovered hexes. GMs can edit hexes via a click-to-edit panel.

### 7.10 Campaign Wiki (Player-Facing)

**Purpose:** Living reference for setting lore, house rules, and game design documentation.

Markdown-rendered pages covering the setting (the Limes, the Collegium, the Vincula, Meridian's background as players discover it), the economy (Essence, gold, how leveling works), and the ship-flavored ability system (the three rules, examples by class, how to negotiate with the GM). GMs can edit wiki pages. Players can read them. This is the primary onboarding document for new players joining mid-campaign.

### 7.11 AI Adventure Generator (GM Only)

**Purpose:** Scaffold adventure outlines quickly using an LLM.

Parameters: party size, level, tone, revelation layer (early / mid / late campaign), ship support viability for the planned hex, and context pulled from the campaign (faction reputations, discovered hexes, recent field reports, hull integrity). Generates a structured adventure outline. GMs can edit before linking to a mission.

---

## 8. User Flows

### 8.1 Player Sign-up Flow

1. Log in via Discord OAuth.
2. Browse the mission board or view upcoming sessions on the dashboard.
3. Back a session proposal or sign up for a confirmed session.
4. Select which character to send from an eligible list.
5. Receive confirmation: "You're signed up for [Mission] on [Date]."
6. Session launches (or is cancelled if minimum crew is not met).

### 8.2 Session Proposal Flow

1. GM creates an open session time slot.
2. Players propose a mission for that slot from the mission board.
3. Other players "back" a proposal to vote for it.
4. When a proposal reaches critical mass (or the GM force-confirms), it locks in.
5. The session is now scheduled with that mission. Players sign up characters.

### 8.3 GM Session Logging Flow

1. GM starts the session.
2. During or after play, GM records: mission result (success/fail), Essence earned (gross), transit deducted (auto-calculated from hex distance), gold earned, ship damage taken (as hull integrity percentage), items recovered, casualties, and session notes.
3. System automatically: deducts transit from gross to compute net Essence, updates ship Essence reserve and gold, updates hull integrity, checks if reserve has crossed a level threshold, logs immutable ledger entries, and marks dead characters.
4. Players receive notification: "Mission complete. Net Essence to reserves: [X]. Gold earned: [Y]. Hull integrity: [Z]%."

### 8.4 Ship Damage and Repair Flow

1. GM logs ship damage during or after a session (hull integrity percentage lost).
2. Ledger records the hull delta and new ship state snapshot.
3. If hull integrity reaches 0%, ship status changes to Grounded — no missions can depart until repairs are made.
4. GM logs a repair (gold spent, hull integrity restored).
5. Ledger records the repair as a gold delta and hull delta entry.

### 8.5 Essence Sale Flow (Emergency Economy)

1. GM opens the Essence Sale log in Ship Management.
2. GM records the amount of Essence sold and gold received.
3. System deducts Essence from reserves (which may drop the ship below a level threshold, stalling advancement), adds gold to reserves, and logs a distinct "Essence Sold" ledger entry.
4. The ledger entry is permanently visible to all players — a record of every concession made to the Collegium.

### 8.6 Long Rest Flow

1. GM records a long rest during or after a session.
2. System deducts the tier-appropriate gold cost from reserves and logs the ledger entry.
3. If gold reserves are insufficient, the GM must record a manual adjustment explaining how the cost was covered (sold goods, borrowed, or deferred).

### 8.7 Character Death Flow

1. Character dies during a session.
2. GM marks the character as Dead in the session log.
3. Player creates a new character (at the ship's current level).
4. New character is ready for the next mission. The ledger preserves the dead character's full history.

### 8.8 Magic Item Fate Flow

When an item is recovered from a mission, the crew decides its fate:

- **Equip to a character** — standard attunement. Item lives in the character's inventory.
- **Attune to ship** — GM integrates the item into Meridian's hull via Ship Management. Gold cost logged to ledger. Benefit is permanent and campaign-wide.

---

## 9. Authentication and Roles

**Discord OAuth (default):** Users authenticate via Discord. JWT session handling after initial auth.

**Roles:**

- **Player** — browse missions, propose/back sessions, sign up characters, manage inventory, purchase from the store, read the wiki.
- **Admin (Game Master)** — all player abilities plus: manage all game content, configure the ship, log session results, generate AI adventures, manage the store and crew roster, attune items to the ship, edit wiki pages.
- **Co-GM (future)** — limited admin rights for assistant GMs.

**Campaign scoping:** Users are scoped to a campaign. Multi-tenancy is supported; users select their campaign after authenticating.

---

## 10. Data Model

### 10.1 Tables

- **Users** — Discord auth data, campaign role.
- **Campaigns** — campaign metadata and settings.
- **Ships** — ship state per campaign (name, current Essence reserve, gold, hull integrity, derived level).
- **Characters** — player character profiles including optional ship-flavored ability notes.
- **Items** — item definitions with name, rarity, description, properties.
- **InventoryItems** — character → item mapping.
- **ShipAttunements** — items permanently integrated into the ship's hull.
- **StoreItems** — items available for purchase with gold (price in gold, stock).
- **Missions** — mission definitions with gross Essence payout, gold payout, and ship support viability.
- **Sessions** — scheduled sessions with status, capacity, and ship damage taken.
- **SessionPlayers** — character sign-ups per session.
- **SessionProposals** — player-submitted mission proposals with backers.
- **Ledger** — append-only immutable log; each entry has Essence delta, gold delta, hull delta, and ship state snapshot.
- **HexMaps** — campaign map definitions.
- **Hexes** — individual hex tiles with terrain, coordinates, state, faction, ship support viability, player notes, discovered status, linked missions.
- **FactionReputations** — ship-level standing per faction.
- **GeneratedAdventures** — AI-generated adventure data.
- **WikiPages** — GM-authored campaign wiki pages (Markdown content, title, slug, last edited).
- **Notes** (stretch) — player or shared campaign notes.
- **Tags** (stretch) — tags for missions, items, sessions.
- **AuditLog** (stretch) — system events for admin action tracking.

### 10.2 Key Relationships

- Character belongs to a Player (User).
- Character participates in Sessions via SessionPlayers.
- Session is linked to one Mission.
- Ledger entries reference a Session (when applicable) and are append-only.
- Missions can be linked to Hexes on the campaign map.
- Proposals belong to a Session and reference a Mission.
- ShipAttunements belong to the Ship, not any Character.
- WikiPages belong to a Campaign.

### 10.3 Ledger Integrity

The ledger is the source of truth for all ship state. It is append-only and immutable. The ship's current Essence reserve, gold, and hull integrity are all derivable from summing ledger deltas. Leveling is recorded as a ledger event when the threshold is crossed — it has no Essence cost.

---

## 11. Technical Requirements

### 11.1 Technology Stack

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

### 11.2 Deployment

- Single repository with frontend + backend.
- Podman Kube YAML for dev and production.
- Deployment-ready for minimal cloud hosting (Fly.io, Railway, or bare VPS).
- SystemD integration via Podman Quadlet for VPS auto-start.
- CI/CD pipeline (GitHub Actions) for linting, testing, and build.

### 11.3 Design Principles

- **Mobile-friendly.** Players will sign up for missions on their phones.
- **Markdown everywhere.** Mission descriptions, session notes, announcements, field reports, after-action reports, and wiki pages support Markdown.
- **Real-time where it matters.** SSE for mission board sign-up counts, session proposal status, and store inventory.
- **Accessible.** Screen reader compatibility, color contrast, and keyboard navigation.
- **Dark mode.** Supported via DaisyUI theme toggle.

---

## 12. Feature Prioritization

### MVP (Launch)

- Ship dashboard with character identity banner, Essence reserve / level threshold display, hull integrity, gold reserves, session board, and available contracts.
- Mission board with full CRUD, sign-ups, Markdown descriptions, Essence payout, gold payout, and ship support viability display.
- Session scheduling with player sign-ups and GM session logging (including transit auto-deduction and ship damage logging).
- Immutable ledger with Essence, gold, and hull deltas; filtering and export.
- Character creation and management with external sheet links, inventory, and ship-flavored ability notes.
- Crew roster view (all characters, sortable/filterable).
- Item store (browse and purchase with gold; ledger entry auto-created).
- Role-based access (Player vs. GM).
- Discord OAuth authentication.
- Session proposal and backing system.
- GM ship management and quick actions including ship damage, repair, and Essence sale logging.
- Campaign wiki with GM editing and player read access.
- Responsive / mobile-friendly layout.
- JSON data export/import for backups.

### Post-Launch (Near-Term)

- Campaign hex map with terrain, hex state, ship support viability, faction control, player notes, and linked missions.
- Hex map editor for GMs.
- Ship item attunement flow.
- AI-assisted adventure generation with campaign context including hull integrity and ship support viability.
- Field reports (player-authored post-session summaries).
- Email or push notification reminders.
- Character death notifications.
- In-app notifications panel.
- Audit logs for admin actions.
- Search and filtering across missions, items, and sessions.

### Future (Stretch)

- Collegium threat tracker (narrative consequence system for repeated open ship support use).
- Faction reputation integration with AI adventure generation.
- Discord bot integration (post ledger updates to the server, including Essence Sold events).
- Foundry VTT plugin for bidirectional sync.
- Alternative OAuth providers.
- Enhanced AI tools (NPC dialogue, encounter balancing with ship support viability context).
- WebSocket support for richer real-time collaboration.
- Offline-first PWA.
- Plugin system for house rules.
- Error and health monitoring.

---

## 13. UX Guidelines

### General Principles

- **Scannable at a glance.** The dashboard and mission board communicate state through visual hierarchy — Essence gauge, hull integrity bar, gold counter, ship support viability badges — not walls of text.
- **Progressive disclosure.** Show summaries by default; let users expand for detail.
- **Guide new users.** The session proposal/backing system is unintuitive for newcomers. Use inline tooltips, a brief "How It Works" explainer on first visit, and clear visual states for proposal progress. New players should be directed to the wiki for setting and rules context.
- **Minimize clicks for common actions.** Signing up for a mission should take two clicks from the dashboard.
- **Essence is never called XP in the UI.** Always "Essence."
- **Gold is never called GP in the UI.** Always "Gold" or the in-world equivalent.
- **Hull integrity is a ship health bar, not a number.** Display as a percentage with a visual bar that shifts color (green / yellow / red) as it drops. Grounded state should be visually unmistakable.

### Specific UX Notes

- **Mission board:** ship support viability should be a prominent badge (Open / Restricted / None) on each card, because it affects planning decisions.
- **Ledger:** Essence Sold entries should be visually distinct — a different color or icon — because they represent a meaningful narrative event, not routine accounting.
- **Dashboard:** when hull integrity is below 50%, display a persistent warning that the ship needs repairs before it can safely position for artillery support.

---

## 14. Assumptions and Constraints

- User authentication infrastructure is provided (Discord OAuth).
- Character stats and combat mechanics are handled in Foundry VTT or D&D Beyond, not in the Hub.
- Essence is the leveling currency. Gold is the operational currency. They are tracked separately and serve different purposes.
- The item store uses gold, not Essence.
- Long rest costs are drawn from gold reserves, not Essence.
- Transit (travel cost) is automatically deducted from gross Essence payout when the GM logs a session result.
- Ship-to-ship combat is out of scope; only mission logistics and ship damage from positioning matter.
- The ledger is the canonical source of truth for all ship resource state.
- AI adventure generation requires an OpenRouter API key configured by the self-hoster.
- Initial deployment targets a single GM. Co-GM support is a future enhancement.
- Ship-flavored ability rulings are made at the table by the GM. The Hub tracks player-declared ship-flavored abilities as reference only, not as enforced mechanical restrictions.

---

## 15. Open Questions

- Should the proposal backing threshold be configurable per campaign, or fixed (e.g., majority of active players)?
- How should transit cost scale with hex distance — fixed per tier, or GM-input per mission?
- When a character dies, do equipped items return to the ship's pool for redistribution, or does the player's next character inherit them?
- What is the minimum viable hex map experience for MVP, vs. deferring the map entirely to post-launch?
- Should the store support limited-time or mission-exclusive items?
- Should ship-attuned items be visible to all players, or GM-only until the benefit is announced?
- Should the Collegium threat level be a tracked numeric value in the Hub, or purely a narrative tool managed by the GM outside the app?
- Should the wiki support player-submitted lore notes (with GM approval), or remain GM-only?
- How granular should ship damage logging be — per-encounter during a session, or a single end-of-session total?
- Should hull integrity affect mission availability (e.g., damaged ships cannot take Hard or Extreme missions), or remain a purely narrative/economic concern?
