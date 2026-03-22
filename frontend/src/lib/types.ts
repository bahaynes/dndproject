export interface GlobalUser {
    username: string;
    discord_id: string;
    avatar_url?: string;
}

export interface User {
    id: number;
    username: string;
    discord_id: string; // From backend
    email: string;
    role: 'player' | 'admin';
    is_active: boolean;
    active_character?: Character;
    characters: Character[];
    avatar_url?: string; // Add this too since backend returns it
}

export interface Character {
    id: number;
    name: string;
    description?: string;
    image_url?: string;
    character_sheet_url?: string;
    class_name?: string;
    level: number;
    status: 'Active' | 'Dead' | 'Benched';
    date_of_death?: string;
    missions_completed: number;
    owner_id: number;
    stats: CharacterStats;
    inventory: InventoryItem[];
    missions: Mission[];
    game_sessions: GameSession[];
}

export interface CharacterRosterEntry {
    id: number;
    name: string;
    class_name?: string;
    level: number;
    status: 'Active' | 'Dead' | 'Benched';
    date_of_death?: string;
    missions_completed: number;
    owner_id: number;
    owner_username?: string;
}

export interface Ship {
    id: number;
    campaign_id: number;
    name: string;
    level: number;
    essence: number;
    motd?: string;
    status: 'nominal' | 'low' | 'critical';
    long_rest_cost: number;
    next_threshold: number | null;
    essence_to_next_level: number;
    created_at: string;
}

export interface LedgerEntry {
    id: number;
    campaign_id: number;
    session_id?: number;
    event_type: string;
    description: string;
    essence_delta: number;
    ship_snapshot?: Record<string, number>;
    created_at: string;
}

export interface CharacterStats {
    id: number;
    character_id: number;
    xp: number;
    scrip: number;
}

export interface Item {
    id: number;
    name: string;
    description?: string;
}

export interface InventoryItem {
    id: number;
    quantity: number;
    item: Item;
}

export interface StoreItem {
    id: number;
    item_id: number;
    item: Item;
    price: number;
    quantity_available: number;
}

export interface Mission {
    id: number;
    name: string;
    description?: string;
    status: string;
    tier?: string;
    region?: string;
    last_run_date?: string;
    cooldown_days: number;
    is_retired: boolean;
    is_discoverable: boolean;
    prerequisite_id?: number;
    rewards: MissionReward[];
    players: Character[];
}

export interface MissionReward {
    id: number;
    item_id?: number;
    xp?: number;
    scrip?: number;
    item?: Item;
}

export interface GameSession {
    id: number;
    name: string;
    description?: string;
    session_date: string; // ISO 8601 date string
    status: 'Open' | 'Contested' | 'Confirmed' | 'Completed' | 'Cancelled';
    after_action_report?: string;
    min_players: number;
    max_players: number;
    players: Character[];
    confirmed_mission_id?: number;
}

export interface CharacterInGameSession {
    id: number;
    name: string;
    description?: string;
    image_url?: string;
    owner_id: number;
}


export interface SessionProposal {
    id: number;
    session_id: number;
    mission_id: number;
    proposed_by_id: number;
    status: 'proposed' | 'confirmed' | 'dismissed' | 'vetoed';
    mission: Mission;
    backers: CharacterInGameSession[];
}

export interface GameSessionWithPlayers {
    id: number;
    name: string;
    description?: string;
    session_date: string;
    status: string;
    after_action_report?: string;
    field_report?: string;
    result?: string;
    essence_earned?: number;
    min_players: number;
    max_players: number;
    players: CharacterInGameSession[];
    proposals: SessionProposal[];
    confirmed_mission?: Mission;
}
