<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { auth } from '$lib/auth';
  import type { GameSessionWithPlayers } from '$lib/types';
  import SectionHeader from '$lib/components/SectionHeader.svelte';
  import SessionList from '$lib/components/SessionList.svelte';
  import { fetchSessions, updateSessionSignup } from '$lib/api';

  let sessions: GameSessionWithPlayers[] = [];
  let error: string | null = null;
  let loading = true;
  let myCharacterId: number | undefined = undefined;
  let pendingSessionId: string | null = null;

  $: myCharacterId = $auth.user?.character?.id;

  onMount(async () => {
    myCharacterId = get(auth).user?.character?.id;
    await loadSessions();
  });

  function isSignedUp(session: GameSessionWithPlayers): boolean {
    if (!myCharacterId) return false;
    return session.players.some(player => player.id === myCharacterId);
  }

  async function loadSessions() {
    loading = true;
    error = null;
    try {
      const token = get(auth).token ?? undefined;
      sessions = await fetchSessions(token);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load sessions';
    } finally {
      loading = false;
    }
  }

  async function toggleSignup(session: GameSessionWithPlayers) {
    error = null;

    if (!myCharacterId) {
      error = 'Add or select a character before signing up.';
      return;
    }

    const token = get(auth).token;
    if (!token) {
      error = 'You must be logged in to sign up.';
      return;
    }

    pendingSessionId = session.id;
    try {
      const method = isSignedUp(session) ? 'DELETE' : 'POST';
      await updateSessionSignup(session.id, myCharacterId, token, method);
      await loadSessions();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to update signup status';
    } finally {
      pendingSessionId = null;
    }
  }
</script>

<div class="page-container space-y-6">
  <SectionHeader
    eyebrow="Session Board"
    title="Game sessions"
    description="Sign up with your ready character, review party slots, and keep the frontier organized."
  >
    <div slot="actions" class="flex gap-2">
      <a class="btn btn-ghost" href="/">Back to hub</a>
    </div>
  </SectionHeader>

  <SessionList
    sessions={sessions}
    isLoading={loading}
    error={error}
    myCharacterId={myCharacterId}
    pendingSessionId={pendingSessionId}
    onToggleSignup={toggleSignup}
    isSignedUp={isSignedUp}
  />
</div>
