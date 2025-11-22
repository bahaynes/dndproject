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
    status: 'Scheduled' | 'Completed';
    after_action_report?: string;
    players: Character[];
}

export interface CharacterInGameSession {
    id: number;
    name: string;
    description?: string;
    image_url?: string;
    owner_id: number;
}


export interface GameSessionWithPlayers {
    id: number;
    name: string;
    description?: string;
    session_date: string; // ISO 8601 date string
    status: 'Scheduled' | 'Completed';
    after_action_report?: string;
    players: CharacterInGameSession[];
    target_tile_id?: number;
}

export interface MapTile {
    id: number;
    q: number;
    r: number;
    terrain: string;
    is_revealed: boolean;
    description?: string;
    notes?: string;
}
