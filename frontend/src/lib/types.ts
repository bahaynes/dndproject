export interface User {
    id: number;
    username: string;
    email: string;
    role: 'player' | 'admin';
    is_active: boolean;
    character?: Character;
}

export interface Character {
    id: number;
    name: string;
    description?: string;
    image_url?: string;
    character_sheet_url?: string;
    owner_id: number;
    stats: CharacterStats;
    inventory: InventoryItem[];
    missions: Mission[];
    game_sessions: GameSession[];
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
    min_players: number;
    max_players: number;
    players: CharacterInGameSession[];
    proposals: SessionProposal[];
    confirmed_mission?: Mission;
}
