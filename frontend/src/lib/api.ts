import type { GameSessionWithPlayers, Mission, Character } from '$lib/types';

async function handleJsonResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
  if (!response.ok) {
    let detail = fallbackMessage;
    try {
      const data = await response.json();
      detail = data.detail ?? fallbackMessage;
    } catch {
      // Use fallback when response is not JSON
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export async function fetchSessions(token?: string): Promise<GameSessionWithPlayers[]> {
  const response = await fetch('/api/sessions/', {
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : undefined,
  });

  return handleJsonResponse<GameSessionWithPlayers[]>(response, 'Failed to fetch sessions');
}

export async function fetchMissions(token?: string): Promise<Mission[]> {
  const response = await fetch('/api/missions/', {
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : undefined,
  });

  return handleJsonResponse<Mission[]>(response, 'Failed to fetch missions');
}

export async function fetchMission(id: string, token?: string): Promise<Mission> {
  const response = await fetch(`/api/missions/${id}`, {
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : undefined,
  });

  return handleJsonResponse<Mission>(response, 'Failed to load mission');
}

export async function updateSessionSignup(
  sessionId: string,
  characterId: number,
  token: string,
  method: 'POST' | 'DELETE',
): Promise<void> {
  const response = await fetch(`/api/sessions/${sessionId}/signup`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ character_id: characterId }),
  });

  await handleJsonResponse(response, 'Failed to update signup');
}

interface SessionPayload {
  mission_id: string;
  title: string;
  session_date: string;
  gm_notes?: string | null;
  route_data?: string[];
}

export async function createSession(payload: SessionPayload, token: string): Promise<GameSessionWithPlayers> {
  const response = await fetch('/api/sessions/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  return handleJsonResponse<GameSessionWithPlayers>(response, 'Failed to create session');
}

interface MissionPayload {
  title: string;
  summary?: string | null;
  status?: string;
  target_hex?: string | null;
  dossier_data?: Record<string, unknown> | null;
}

export async function createMission(payload: MissionPayload, token: string): Promise<Mission> {
  const response = await fetch('/api/missions/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  return handleJsonResponse<Mission>(response, 'Failed to create mission');
}

export async function updateMission(id: string, payload: MissionPayload, token: string): Promise<Mission> {
  const response = await fetch(`/api/missions/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  return handleJsonResponse<Mission>(response, 'Failed to update mission');
}

export async function fetchMyCharacters(token: string): Promise<Character[]> {
  const response = await fetch('/api/characters/', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return handleJsonResponse<Character[]>(response, 'Failed to fetch roster');
}

interface CharacterPayload {
  name: string;
  description?: string | null;
  image_url?: string | null;
  status?: string;
  stats?: {
    xp?: number;
    commendations?: number;
    current_hp?: number;
    short_rest_available?: boolean;
  };
}

export async function createCharacter(payload: CharacterPayload, token: string): Promise<Character> {
  const response = await fetch('/api/characters/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  return handleJsonResponse<Character>(response, 'Failed to create character');
}

export async function updateCharacter(id: number, payload: CharacterPayload, token: string): Promise<Character> {
  const response = await fetch(`/api/characters/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  return handleJsonResponse<Character>(response, 'Failed to update character');
}
