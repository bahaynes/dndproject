# Product Requirements Document: The Shattered Front (Campaign Manager)

## 1. Introduction

**The Shattered Front Hub** is a specialized campaign management tool designed for a "War-Game" style West Marches DnD 5e campaign. Unlike standard tools, this application enforces strict resource scarcity, time tracking, and roster management mechanics.

The application is built with **SvelteKit (frontend)** and **FastAPI (backend)**. It is designed for **self-hosting** via **Podman** to serve a private group of 5–10 players managing a larger roster of characters.

## 2. Goals and Objectives

* **Enforce "Iron Attrition" Mechanics**: Automate the tracking of Gritty Realism rests, spell slot persistence between sessions, and medical leave.
* **Enable Roster Play**: Allow players to manage a "stable" of characters, switching between them based on fatigue and mission requirements.
* **Centralize the "Fog of War"**: Provide a Hex-based map where territory control (Alliance vs. Hegemony) dictates mission difficulty and travel costs.
* **Gamify Logistics**: Track the 7-Day Deployment clock and Short Rest budgets automatically.

## 3. Target Audience

* **The Strategic Player**: Players managing 2–3 characters who need to decide which one is "fresh" enough for a mission.
* **The Tactician GM**: An admin who needs to update the war front, managing which map hexes are safe and which are hostile.

## 4. Features and Functionality

### 4.1. User & Roster Management (Core Change)

* **User Profile (The Commander)**: The User account represents the Player.
    * **Banked XP**: XP is awarded to the *User*, not the Character. The User interface allows distributing this XP to specific characters in their roster.
* **The Roster (Barracks)**: Users can create and manage multiple characters.
* **Character States**: Characters must have a status flag:
    * 🟢 **Ready**: Full HP, fresh spell slots.
    * 🟡 **Fatigued**: Returned from mission. Only recovered via "Tactical Rest" (Short Rest benefits). Missing high-level slots.
    * 🔴 **Deployed**: Currently assigned to an active mission.
    * 🏥 **Medical Leave**: Player explicitly benches character for 1 week to trigger a "True Long Rest."

### 4.2. Player Features

* **Barracks Dashboard**: View all characters, assign Banked XP to level them up, and toggle "Medical Leave."
* **Deployment View (Character Sheet)**:
    * **Resource persistence**: Manually track current HP and Spell Slots remaining at the end of a session.
    * **Tactical Medkit**: A toggle to "use" the single-use item per mission.
* **The Job Board**:
    * View missions categorized by type (Scramble, Infiltration, Logistics).
    * **Deployment Calculator**: Selecting a mission automatically displays the **Travel Cost** and resulting **Short Rest Budget** based on the current map state.
* **Requisition Store**: Buy items, but also **buy HP** (Medical attention) using Gold.

### 4.3. Admin (GM) Features

* **War Map Manager (Hex Grid)**:
    * Manage a visual Hex grid.
    * Toggle Hex status: **Blue** (Alliance/Safe), **Red** (Hegemony/Hostile), **Grey** (Neutral).
    * *Logic:* Changing a Hex color automatically updates the Travel Cost for missions passing through it.
* **Mission Control**:
    * Create missions with specific "Duration" parameters.
    * **After Action Report (AAR)**:
        * Mark mission as Success/Fail.
        * Input total XP earned (deposited to User Banks).
        * Input Gold earned.
        * **Territory Control**: Option to convert a Grey Hex to Blue upon success.
* **Session "Soft" Reset**: A button to apply "Tactical Rest" to all characters who just finished a session (Heal to full, reset Short Rest abilities, do *not* reset Long Rest slots).

### 4.4. Shared Features

* **The Deployment Clock**: A visual widget showing the 7-Day limit for active sessions.
* **Server-Sent Events (SSE)**: Real-time updates when the GM flips a Hex color or posts a new mission.
* **Markdown Support**: For mission briefings and AARs.

## 5. Technical Requirements

### 5.1. Technology Stack

* **Frontend**: SvelteKit + TailwindCSS (DaisyUI for military/tactical theme).
* **Backend**: FastAPI (Python).
* **Database**: SQLite (default).
* **Containerization**: Podman Compose.

### 5.2. Database Schema Refinement

* `User`:
    * `banked_xp`: Integer (Pool of XP available to spend).
* `Character`:
    * `status`: Enum (Ready, Deployed, Fatigued, LongResting).
    * `current_hp`: Integer.
    * `current_xp`: Integer.
    * `slots_level_1`: Integer (remaining).
    * `slots_level_2`: Integer (remaining)... etc.
    * `last_played_date`: Timestamp (to calculate Long Rest eligibility).
* `MapHex`:
    * `grid_id`: String (e.g., "B4").
    * `owner`: Enum (Alliance, Hegemony, Neutral).
    * `has_fort`: Boolean (Allows Long Rests if true).
* `Mission`:
    * `mission_type`: Enum (Scramble, Infiltration, Logistics).
    * `travel_days_outbound`: Integer.
    * `travel_days_inbound`: Integer.
    * `short_rest_budget`: Integer (Computed field).

### 5.3. Business Logic (The Iron Attrition)

* **The Rest Calculator**:
    * Logic to calculate `Available Short Rests = 7 - (Outbound + Inbound Travel)`.
* **The XP Distributor**:
    * Transaction logic to move XP from `User.banked_xp` to `Character.xp`.
* **The Long Rest Trigger**:
    * A cron job or manual trigger that checks: `If Character.status == LongResting AND (CurrentDate - StartDate) >= 7 Days -> Set Status = Ready`.

## 6. Future Enhancements

* **Discord Bot Integration**: Post new missions to a Discord channel automatically.
* **Asset Management**: Upload maps for specific dungeons (Sector maps).
* **Casualty Log**: A "Graveyard" page for characters who didn't extract.
* **Fort Builder**: A UI for players to pool Gold to upgrade a "Blue Hex" with specific buildings (e.g., "Build Hospital" = Cheaper healing).