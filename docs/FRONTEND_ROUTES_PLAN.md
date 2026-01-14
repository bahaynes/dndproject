# Frontend Routes Implementation Plan

This document outlines the requirements for each missing frontend route. All pages should follow the existing design patterns from `/sessions/+page.svelte` and `/dashboard/+page.svelte`.

---

## 1. `/characters` - Character Sheet

### Purpose
Display and edit the current user's character information.

### API Endpoints Used
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/characters/{id}` | Get character details |
| PUT | `/api/characters/{id}` | Update character info |

### Data Model (`Character`)
```typescript
{
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  stats: {
    id: number;
    xp: number;
    scrip: number;
  };
  inventory: InventoryItem[];
  missions: Mission[];
  game_sessions: GameSession[];
  character_sheet_url?: string;
}
```

### UI Requirements
- **Header**: Character name as title
- **Profile Card**: Name, description (editable), avatar placeholder
- **Stats Card**: XP and Scrip display
- **Quick Links**: Links to Inventory, Missions, Sessions, Character Sheet
- **Edit Mode**: Toggle to enable inline editing of name/description
- **Save Button**: Submit changes via PUT

### Auth
- User must be logged in
- Can only view/edit their own character

---

## 2. `/characters/inventory` - Inventory Management

### Purpose
View and manage items in the character's inventory.

### API Endpoints Used
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/characters/{id}` | Get character with inventory |
| DELETE | `/api/characters/{id}/inventory/{inv_id}` | Remove item from inventory |

### Data Model (`InventoryItem`)
```typescript
{
  id: number;
  quantity: number;
  item: {
    id: number;
    name: string;
    description?: string;
  }
}
```

### UI Requirements
- **Header**: "Inventory" with character name subtitle
- **Item Grid/List**: Cards showing item name, description, quantity
- **Remove Button**: Decrease quantity or remove item (DELETE endpoint)
- **Empty State**: "Your inventory is empty. Visit the Store to acquire items."
- **Link to Store**: Button to navigate to `/store`

### Auth
- User must be logged in
- Can only view/manage their own inventory

---

## 3. `/missions` - Mission Board

### Purpose
Browse available missions, view details, and sign up.

### API Endpoints Used
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/missions/` | List all missions |
| GET | `/api/missions/{id}` | Get mission details |
| POST | `/api/missions/{id}/signup` | Sign up for mission |

### Data Model (`Mission`)
```typescript
{
  id: number;
  name: string;
  description?: string;
  status: "Available" | "In Progress" | "Completed";
  campaign_id: number;
  rewards: MissionReward[];
  players: Character[];
}
```

### UI Requirements
- **Header**: "Mission Board"
- **Filter Tabs**: All / Available / In Progress / Completed
- **Mission Cards**: 
  - Name, description (truncated)
  - Status badge
  - Reward preview (XP, Scrip, Item names)
  - Player count / signed up players
- **Sign Up Button**: POST to signup endpoint (if Available)
- **Expand/Detail View**: Modal or drawer with full details

### Auth
- User must be logged in
- Can sign up if status is "Available" and not already signed up

---

## 4. `/store` - Company Store

### Purpose
Browse and purchase items using Scrip.

### API Endpoints Used
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/store/items/` | List store items |
| POST | `/api/store/items/{id}/purchase` | Purchase item |

### Data Model (`StoreItem`)
```typescript
{
  id: number;
  price: number;
  quantity_available: number;
  item: {
    id: number;
    name: string;
    description?: string;
  }
}
```

### UI Requirements
- **Header**: "Company Store"
- **Scrip Balance**: Display current character's Scrip at top
- **Item Grid**: Cards with item name, description, price, stock
- **Purchase Button**: With quantity selector (default 1)
- **Out of Stock**: Disable purchase if quantity_available is 0
- **Confirmation Modal**: "Purchase X for Y Scrip?"
- **Success/Error Toast**: After purchase attempt

### Auth
- User must be logged in
- Must have a character with sufficient Scrip

---

## 5. `/admin/sessions` - Admin Session Management

### Purpose
Allow admins to create, edit, and manage game sessions.

### API Endpoints Used
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/` | List all sessions |
| POST | `/api/sessions/` | Create new session |
| PUT | `/api/sessions/{id}` | Update session |

### Data Model (`GameSessionCreate`)
```typescript
{
  name: string;
  description?: string;
  session_date: datetime;
  status: "Scheduled" | "In Progress" | "Completed" | "Cancelled";
  after_action_report?: string;
}
```

### UI Requirements
- **Header**: "Manage Sessions" (admin badge)
- **Create Button**: Opens form modal/drawer
- **Session List**: Table or cards with:
  - Name, Date, Status
  - Player count
  - Edit/Delete actions
- **Edit Form**: Name, description, date picker, status dropdown
- **After Action Report**: Text area for completed sessions
- **Player List**: Read-only view of signed up characters

### Auth
- User must be admin (`role === "admin"`)

---

## 6. `/admin/missions` - Admin Mission Management

### Purpose
Allow admins to create, edit, and manage missions.

### API Endpoints Used
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/missions/` | List all missions |
| POST | `/api/missions/` | Create new mission |
| PUT | `/api/missions/{id}/status` | Update mission status |
| POST | `/api/missions/{id}/distribute_rewards` | Distribute rewards |

### Data Model (`MissionCreate`)
```typescript
{
  name: string;
  description?: string;
  status: "Available" | "In Progress" | "Completed";
  rewards: MissionRewardCreate[];
}

MissionRewardCreate: {
  item_id?: number;
  xp?: number;
  scrip?: number;
}
```

### UI Requirements
- **Header**: "Manage Missions" (admin badge)
- **Create Button**: Opens form modal/drawer
- **Mission List**: Table or cards with:
  - Name, Status, Player count
  - Edit/Delete actions
- **Create/Edit Form**:
  - Name, description
  - Status dropdown
  - Rewards section: Add XP, Scrip, or Item rewards
- **Distribute Rewards Button**: For completed missions
- **Player List**: View signed up characters

### Auth
- User must be admin

---

## 7. `/admin/items` - Admin Item Management

### Purpose
Allow admins to manage the master item list and store inventory.

### API Endpoints Used
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/items/` | List all items |
| POST | `/api/items/` | Create new item |
| GET | `/api/store/items/` | List store items |
| POST | `/api/store/items/` | Add item to store |

### Data Model
```typescript
ItemCreate: {
  name: string;
  description?: string;
}

StoreItemCreate: {
  item_id: number;
  price: number;
  quantity_available: number;
}
```

### UI Requirements
- **Header**: "Manage Items" (admin badge)
- **Two Sections**:
  1. **Item Catalog**: All defined items
  2. **Store Inventory**: Items available for purchase
- **Create Item Button**: Name + description form
- **Add to Store Button**: Select item, set price + quantity
- **Item List**: Table with name, description, "Add to Store" action
- **Store List**: Table with item name, price, quantity, edit/remove

### Auth
- User must be admin

---

## Implementation Order (Recommended)

1. **`/characters`** - Core player feature, simple CRUD
2. **`/characters/inventory`** - Extends characters, simple list
3. **`/missions`** - Core player feature, signup flow
4. **`/store`** - Player feature, purchase flow
5. **`/admin/items`** - Required before other admin features
6. **`/admin/missions`** - Admin CRUD + rewards
7. **`/admin/sessions`** - Admin CRUD (similar pattern to existing sessions page)

---

## Shared Components to Create

| Component | Purpose |
|-----------|---------|
| `Modal.svelte` | Reusable modal dialog |
| `Toast.svelte` | Success/error notifications |
| `AdminBadge.svelte` | Visual indicator for admin pages |
| `LoadingSpinner.svelte` | Loading state indicator |
| `EmptyState.svelte` | "No items" placeholder |

---

## Design Notes

- Follow existing DaisyUI patterns from `sessions/+page.svelte`
- Use `$auth` store for token and user info
- Use `API_BASE_URL` from `$lib/config`
- All admin routes should check `$auth.user?.role === "admin"`
- Consider adding `+layout.ts` guards for admin routes
