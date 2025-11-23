export interface User {
    id: number;
    username: string;
    email: string;
    role: 'player' | 'admin';
    is_active: boolean;
    character?: Character;
    characters?: Character[];
}

export type CharacterStatus = 'ready' | 'deployed' | 'fatigued' | 'medical_leave';

export interface Character {
    id: number;
    name: string;
    description?: string;
    image_url?: string;
    owner_id: number;
    status: CharacterStatus;
    stats?: CharacterStats;
    inventory?: InventoryItem[];
    missions?: Mission[];
    game_sessions?: GameSession[];
}

export interface CharacterStats {
    id: number;
    character_id: number;
    xp: number;
    commendations?: number;
    current_hp?: number;
    short_rest_available?: boolean;
    scrip?: number;
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
    id: string;
    title: string;
    summary?: string;
    status: string;
    target_hex?: string;
    dossier_data?: Record<string, any>;
    players: Character[];
}

export interface MissionReward {
    id: number;
    item_id?: number;
    xp?: number;
    scrip?: number;
    item?: Item;
}

export type SessionStatus = 'open' | 'confirmed' | 'completed' | 'cancelled';

export interface GameSession {
    id: string;
    mission_id: string;
    title: string;
    session_date: string; // ISO 8601 date string
    status: SessionStatus;
    route_data: string[];
    gm_notes?: string;
    aar_summary?: string;
    players: Character[];
}

export interface CharacterInGameSession {
    id: number;
    name: string;
    description?: string;
    image_url?: string;
    owner_id: number;
}


export interface GameSessionWithPlayers extends GameSession {
    players: CharacterInGameSession[];
}
