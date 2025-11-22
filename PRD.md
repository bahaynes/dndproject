# **Product Requirements Document: The Shattered Front Hub**

## **1\. Introduction**

**The Shattered Front Hub** is a specialized campaign management platform designed for a high-attrition, "War-Game" style West Marches D\&D 5e campaign.

Unlike generic campaign managers, this application enforces specific mechanical constraints regarding time, travel, and resource scarcity. It acts as the "Source of Truth" for the campaign's logistical layer, while leaving character build specifics to external tools (e.g., D\&D Beyond, paper sheets).

## **2\. Goals and Philosophy**

### **2.1. The "Source of Truth" Scope**

The application manages **State**, not **Rules**.

* **Managed Here**: Character Roster status (Ready/Fatigued), XP/Level, Current HP, Short Rest Availability, Magic Item Inventory, Campaign Map, and Mission History.  
* **Managed Elsewhere**: Attribute scores, Skills, Feats, Spells Prepared, and Attack Rolls.

### **2.2. The "Iron Attrition" Gameplay Loop**

The software is designed to enforce the campaign's unique resting economy:

* **7-Day Deployment**: Missions have a hard time limit.  
* **Travel Costs**: Choosing a route through the map directly subtracts from the party's "Short Rest Budget."  
* **Roster Play**: Players must manage a stable of characters, cycling them between "Deployed," "Fatigued," and "Medical Leave" (Long Rest).

### **2.3. Shared GM Knowledge**

The system allows GMs to structure encounter data (monsters, loot, tactics) directly into Hexes and Missions, allowing any Admin to run a session with minimal prep by relying on the stored "Dossier."

## **3\. Core Mechanics & Features**

### **3.1. Map & Navigation Logic**

#### **The Hex Grid**

The map is a logical grid where every Hex contains:

* **Coordinates**: Unique ID (e.g., A1, B2).  
* **Terrain**: References a global **Terrain Definition** (e.g., "Forest", "Ruins", "High Road").  
  * This defines the visual style (Icon/Color) and mechanical impact (Travel Cost Multiplier).  
* **Ownership**: (Alliance \[Safe\], Hegemony \[Hostile\], Neutral).  
* **Fog of War**:  
  * ⬛ **Black (Unexplored)**: Terrain/Owner unknown. High travel risk.  
  * ⬜ **Grey (Explored)**: Static terrain known, dynamic enemy movements hidden.  
  * 🟦 **Blue (Active Intel)**: Fully visible.  
* **Hex Dossier**: A list of potential "Random Encounters" native to this hex (e.g., "Swamp Patrols").

#### **Player Routing & The Calculator**

* **Mission Targeting**: GMs create Missions anchored to a specific **Target Hex**.  
* **The "Session Captain" Rule**: The **first player** to sign up for a specific time slot creates the **Game Session**. They define the route on the map.  
  * This route is locked and persisted.  
  * Subsequent players signing up for this session accept the pre-defined route and Short Rest Budget.  
* The Calculator: The system computes the Short Rest Budget automatically:  
  $$\\text{Budget} \= 7 \\text{ Days} \- (\\text{Outbound Cost} \+ \\text{Inbound Cost})$$

### **3.2. Roster Management**

#### **The Barracks**

* **User \= Player**: A User account represents the human player.  
* **Unlimited Roster**: Users can create any number of Characters.  
* **Character States**:  
  * 🟢 **Ready**: Full HP, full Hit Dice, fresh Spell Slots.  
  * 🔴 **Deployed**: Currently assigned to an active Mission.  
  * 🟡 **Fatigued**: Returned from a mission. HP restored, but Long Rest resources (Spell Slots \> Lvl 2\) are **not** recovered.  
  * 🏥 **Medical Leave**: Character is locked for 1 real-world week (skips a session) to trigger a "True Long Rest" reset.

### **3.3. Economy & Inventory**

#### **Magic Item Database**

* **Seeded Data**: Pre-loaded with SRD Magic Items.  
* **Custom Items**: GM tools to create "War Relics."  
* **Inventory Slots**: Characters have a distinct inventory for Magic Items. Attunement is tracked (e.g., 2/3 slots).

#### **The Commendation Store**

* **Currency**: **Commendations** (Non-Gold currency earned via objectives).  
* **The Store**: A UI to purchase Magic Items using Commendations.  
* **Gating**: Items can be restricted by Character Level or Faction Reputation.

### **3.4. GM Tools: The Dossier System**

#### **Structured Encounters**

Both **Missions** and **Hexes** contain a dossier object. This is a structured list of potential encounters.

* **Aggregation**: The system sums XP, Gold, and Loot from all encounters in a dossier to show "Total Potential Rewards."  
* **Run View**: During a session, the GM sees a sequential list of encounters.  
* **Monster Links**: Monsters are defined by Name, URL (e.g., DnDBeyond link), and CR.

## **4\. Features and Functionality**

### **4.1. User & Roster Management**

*(See Section 3.2)*

### **4.2. Player Features**

*(See Section 5.1)*

### **4.3. Admin (GM) Features**

* **Global Terrain Manager**:  
  * **Custom Definitions**: GMs can create terrain types specific to their setting (e.g., "Mournland Waste", "High Road", "Deep Jungle").  
  * **Attributes**:  
    * Travel Cost Multiplier (e.g., 0.5x for Roads, 2.0x for Swamps).  
    * Visuals: Hex Color Code and Icon class (using a built-in library like FontAwesome or RPG-Awesome).  
* **Mission & Hex Editors**: Tools to populate the Dossier and Map data.  
* **Session Manager**: Tools to confirm sessions, run encounters, and finalize AARs.

## **5\. Technical Specifications**

### **5.1. Tech Stack**

* **Frontend**: SvelteKit \+ TailwindCSS (DaisyUI theme) \+ D3.js (Hex Map Visualization).  
* **Backend**: FastAPI (Python, Async).  
* **Database**: SQLite (default) with SQLAlchemy.  
* **Deployment**: Podman Compose (Containerized).

### **5.2. Database Schema**

#### **Core Tables**

* **User**: id, username, is\_admin.  
* **Character**: id, user\_id, name, status (Enum), xp, commendations, current\_hp.  
* **Item**: id, name, rarity, attunement (Bool), description (Markdown).  
* **CharacterInventory**: character\_id, item\_id, is\_attuned.

#### **Map & Mission Tables**

* **TerrainDef**:  
  * id: UUID (PK).  
  * name: String (e.g., "Ancient Road").  
  * travel\_cost\_mult: Float (e.g., 0.5).  
  * color\_hex: String (e.g., "\#3b82f6").  
  * icon\_ref: String (e.g., "fa-road").  
* **HexDef**:  
  * coordinate: String (PK).  
  * terrain\_id: FK (TerrainDef).  
  * owner: Enum.  
  * fog\_level: Enum.  
  * dossier\_data: JSON (Hex-specific encounters).  
* **Mission**:  
  * id: UUID.  
  * target\_hex: FK (HexDef).  
  * title: String.  
  * dossier\_data: JSON (Mission-specific encounters).  
* **GameSession**:  
  * id: UUID.  
  * mission\_id: FK.  
  * date\_scheduled: Timestamp.  
  * status: Enum (Open, Confirmed, Completed, Cancelled).  
  * route\_data: JSON (List of coordinates traveled).  
  * gm\_notes: Text (Private notes for other GMs).  
  * aar\_summary: Text (Public markdown for players).

### **5.3. Data Structures (JSON)**

#### **The Dossier Object**

Stored in Mission.dossier\_data and HexDef.dossier\_data.

{  
  "gm\_notes": "Markdown string. Tactical advice, terrain features, DC for traps.",  
  "encounters": \[  
    {  
      "id": "uuid",  
      "name": "The Gatekeepers",  
      "type": "Combat",  
      "cr\_estimate": 4,  
      "description": "Two Ogres guarding the bridge.",  
      "monsters": \[  
        { "name": "Ogre", "url": "https://...", "cr": 2, "count": 2 },  
        { "name": "Goblin Archer", "url": "https://...", "cr": 0.25, "count": 4 }  
      \],  
      "loot": {  
        "gold": 50,  
        "items": \[ 102, 405 \] // References Item IDs  
      },  
      "xp\_reward": 1100  
    }  
  \],  
  "completion\_reward": {  
    "xp": 1000,  
    "gold": 500,  
    "commendations": 1  
  }  
}

### **5.4. Business Logic**

* **Travel Calculation**: Short Rest Budget \= 7 \- (Route Cost).  
* **Utility Spells**: Buff duration logic (1 hr \-\> 24 hr) is handled via tooltips/rules reference on the site.  
* **Encounter Difficulty Calculator**:  
  * The system implements 5e SRD Difficulty calculations.  
  * **Inputs**:  
    * Party Size & Average Party Level (APL) (derived from confirmed session signups).  
    * Monster CR & Count (derived from Dossier JSON).  
  * **Logic**:  
    1. Calculate Party XP Thresholds (Easy, Medium, Hard, Deadly).  
    2. Calculate Encounter XP (Sum of Monster XP \* Multiplier for group size).  
    3. Compare Encounter XP against Party Thresholds.  
  * **Output**: A "Difficulty Badge" (e.g., 💀 Deadly) displayed in the GM's Session Run View.

## **6\. User Flows**

### **6.1. Session Setup & Signup**

1. **Creation (Session Captain)**:  
   * First player selects a Mission and "Creates Session."  
   * Player inputs Date/Time.  
   * Player **draws the route**. This sets the route\_data and locks the Short Rest Budget.  
   * Session state: Open.  
2. **Recruitment**:  
   * Other players view the Open session. They see the route and budget pre-decided.  
   * They select a Ready character to sign up.  
3. **Confirmation (GM)**:  
   * GM reviews signups.  
   * GM clicks "Confirm Session". State: Confirmed.  
   * Characters are locked to Deployed status.

### **6.2. Session Execution (GM)**

1. **Load Session**: GM opens the active session.  
2. **View Dossier**: GM sees the Mission Encounters *and* the Hex Encounters for the traversed route.  
3. **Run Encounters**: GM logs which encounters were cleared.  
4. **Loot Bag**: Cleared encounters dump their loot into a "Session Loot Bag."

### **6.3. Session Finalization (AAR Phase)**

1. **Mark Complete**: GM marks session as Completed.  
2. **Loot & XP**:  
   * System presents the "Loot Bag."  
   * GM assigns items to specific characters.  
   * XP and Gold are distributed.  
3. **The AAR (After Action Report)**:  
   * **GM Private Notes**: GM writes notes about the Hexes (e.g., "Hex B4 has a new trap now") visible only to other GMs.  
   * **Public Log**: Players and GM collaboratively write a summary for the public Campaign Log.  
4. **Close**:  
   * Updates applied to Database.  
   * Character status set to Fatigued.  
   * Notification sent to Discord/Feed.

## **7\. Future Roadmap & Stretch Goals**

### **7.1. Community Features**

* **Discord Webhooks**: Auto-post AARs and New Missions.  
* **Casualty Graveyard**: A memorial page for deceased characters.

### **7.2. AI & LLM Integration (Stretch Goals)**

* **World Bible Integration**: Allow GMs to upload a "Campaign Bible" (Markdown/PDF) containing world lore, factions, and tone.  
* **Generative Hex Content**:  
  * Button: "Generate Encounters for this Hex."  
  * Logic: LLM uses the Hex Terrain type (e.g., "Ruins") and the Campaign Bible to generate 3 thematic encounters (Combat, Social, Puzzle) formatted into the dossier\_data JSON structure.  
* **Co-Pilot Session Design**:  
  * Chat interface where GMs collaborate with the LLM to brainstorm Mission objectives that fit the current territory control map (e.g., "The Hegemony just took Sector 4, generate a counter-offensive mission").