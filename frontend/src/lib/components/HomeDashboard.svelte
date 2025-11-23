<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { auth } from '$lib/auth';
  import type { GameSessionWithPlayers, Mission } from '$lib/types';
  import SectionHeader from '$lib/components/SectionHeader.svelte';
  import SessionList from '$lib/components/SessionList.svelte';
  import MissionList from '$lib/components/MissionList.svelte';
  import {
    fetchMissions,
    fetchSessions,
    updateSessionSignup,
    createSession as apiCreateSession,
  } from '$lib/api';

  let sessions: GameSessionWithPlayers[] = [];
  let missions: Mission[] = [];

  let sessionsLoading = true;
  let missionsLoading = true;
  let sessionError: string | null = null;
  let missionError: string | null = null;
  let myCharacterId: number | undefined = undefined;
  let pendingSessionId: string | null = null;
  let creatingSession = false;
  let creationFeedback: string | null = null;

  let sessionForm = {
    mission_id: '',
    title: '',
    session_date: '',
    gm_notes: '',
    route_data: '',
  };

  $: myCharacterId = $auth.user?.character?.id;
  $: openSessions = sessions.filter(session => session.status === 'open').length;
  $: nextSession =
    sessions.length > 0
      ? [...sessions].sort(
          (a, b) => new Date(a.session_date).getTime() - new Date(b.session_date).getTime(),
        )[0]
      : null;
  $: availableMissions = missions.filter(mission => mission.status !== 'retired').length;
  $: isGM = $auth.user?.role === 'admin';

  onMount(async () => {
    const currentAuth = get(auth);
    myCharacterId = currentAuth.user?.character?.id;
    await Promise.all([loadSessions(), loadMissions()]);
  });

  function isSignedUp(session: GameSessionWithPlayers): boolean {
    if (!myCharacterId) return false;
    return session.players.some(player => player.id === myCharacterId);
  }

  async function loadSessions() {
    sessionsLoading = true;
    sessionError = null;
    try {
      const token = get(auth).token ?? undefined;
      sessions = await fetchSessions(token);
    } catch (err) {
      sessionError = err instanceof Error ? err.message : 'Failed to fetch sessions';
    } finally {
      sessionsLoading = false;
    }
  }

  async function loadMissions() {
    missionsLoading = true;
    missionError = null;
    try {
      const token = get(auth).token ?? undefined;
      missions = await fetchMissions(token);
    } catch (err) {
      missionError = err instanceof Error ? err.message : 'Failed to fetch missions';
    } finally {
      missionsLoading = false;
    }
  }

  async function toggleSignup(session: GameSessionWithPlayers) {
    sessionError = null;

    if (!myCharacterId) {
      sessionError = 'Add or select a character before signing up.';
      return;
    }

    const token = get(auth).token;
    if (!token) {
      sessionError = 'Please log in to manage signups.';
      return;
    }

    pendingSessionId = session.id;
    try {
      const method = isSignedUp(session) ? 'DELETE' : 'POST';
      await updateSessionSignup(session.id, myCharacterId, token, method);
      await loadSessions();
    } catch (err) {
      sessionError = err instanceof Error ? err.message : 'Failed to update signup';
    } finally {
      pendingSessionId = null;
    }
  }

  async function createSession() {
    creationFeedback = null;

    if (!isGM) {
      creationFeedback = 'Only GMs can schedule sessions.';
      return;
    }

    if (!sessionForm.mission_id || !sessionForm.title || !sessionForm.session_date) {
      creationFeedback = 'Mission, title, and date are required.';
      return;
    }

    const token = get(auth).token;
    if (!token) {
      creationFeedback = 'Please log in to create a session.';
      return;
    }

    creatingSession = true;
    const routeData = sessionForm.route_data
      ? sessionForm.route_data.split(',').map(entry => entry.trim()).filter(Boolean)
      : [];

    try {
      await apiCreateSession(
        {
          mission_id: sessionForm.mission_id,
          title: sessionForm.title,
          gm_notes: sessionForm.gm_notes || null,
          session_date: new Date(sessionForm.session_date).toISOString(),
          route_data: routeData,
        },
        token,
      );
      creationFeedback = 'Session scheduled and posted to the ledger.';
      sessionForm = { mission_id: '', title: '', session_date: '', gm_notes: '', route_data: '' };
      await loadSessions();
    } catch (err) {
      creationFeedback = err instanceof Error ? err.message : 'Failed to create session';
    } finally {
      creatingSession = false;
    }
  }

  const formatDate = (value: string | undefined) => {
    if (!value) return 'Not scheduled';
    const date = new Date(value);
    return date.toLocaleString();
  };
</script>

<div class="page-container space-y-10">
  <section class="grid items-start gap-6 lg:grid-cols-[1.1fr_0.9fr]">
    <div class="panel p-6 space-y-5 glow-border">
      <div class="pill w-fit">Command Deck</div>
      <h1 class="text-4xl sm:text-5xl font-bold leading-tight">Shattered Front Hub</h1>
      <p class="text-lg muted max-w-2xl">
        The source of truth for deployments: align on routes, roster your adventurers, and keep every dossier ready for
        the next push into the wilds.
      </p>
      <div class="flex flex-wrap gap-3">
        {#if $auth.isAuthenticated}
          <a href="/sessions" class="btn btn-primary">Open session board</a>
          <a href="/dashboard/admin/sessions" class="btn btn-ghost">Admin controls</a>
          {#if isGM}
            <a href="/missions" class="btn btn-muted">Mission dossiers</a>
          {/if}
        {:else}
          <a href="/register" class="btn btn-primary">Join the roster</a>
          <a href="/login" class="btn btn-ghost">I already have access</a>
        {/if}
      </div>
      <p class="muted text-sm max-w-3xl">
        Sessions lock their route once the Session Captain signs up. The calculator keeps your seven-day deployment
        honest by tracking each hex on the way out and back.
      </p>
    </div>

    <div class="panel p-6 space-y-4">
      <div class="stat-grid">
        <div class="stat-card">
          <p class="muted text-xs uppercase tracking-wide">Open sessions</p>
          <p class="text-3xl font-semibold">{openSessions}</p>
          <p class="muted text-xs">Ready for player signups</p>
        </div>
        <div class="stat-card">
          <p class="muted text-xs uppercase tracking-wide">Active missions</p>
          <p class="text-3xl font-semibold">{availableMissions}</p>
          <p class="muted text-xs">Dossiers prepped for scheduling</p>
        </div>
        <div class="stat-card">
          <p class="muted text-xs uppercase tracking-wide">Next table</p>
          <p class="text-lg font-semibold leading-tight">{formatDate(nextSession?.session_date)}</p>
          {#if nextSession}
            <p class="muted text-xs">{nextSession.title}</p>
          {/if}
        </div>
      </div>
      <div class="panel panel-strong p-4 rounded-xl">
        <p class="text-sm font-semibold">Admin/GM cheatsheet</p>
        <p class="muted text-sm">
          Use missions to track dossiers and target hexes. Schedule sessions against those missions, and the roster
          signup will lock the travel route and short-rest budget.
        </p>
      </div>
    </div>
  </section>

  <section class="split-grid">
    <div class="panel p-6 space-y-4">
      <SectionHeader
        eyebrow="Session Ledger"
        title="Upcoming and active sessions"
        description="Vote to join with your ready character, or scan the roster before committing."
      >
        <div slot="actions" class="flex flex-wrap gap-2">
          <a href="/sessions" class="btn btn-ghost">Full session board</a>
        </div>
      </SectionHeader>

      <SessionList
        sessions={sessions}
        isLoading={sessionsLoading}
        error={sessionError}
        myCharacterId={myCharacterId}
        pendingSessionId={pendingSessionId}
        onToggleSignup={toggleSignup}
        isSignedUp={isSignedUp}
      />
    </div>

    <div class="panel p-6 space-y-5">
      <SectionHeader
        eyebrow="Roster Tools"
        title={$auth.user ? `Welcome, ${$auth.user.username}` : 'Claim your seat at the table'}
        description={
          $auth.user
            ? 'Keep your ready character handy and align with your Session Captain before travel.'
            : 'Log in to track your characters, sign sessions, and follow GM notes.'
        }
      />

      {#if $auth.user}
        <div class="grid gap-3">
          <div class="panel panel-strong p-4 rounded-xl">
            <p class="muted text-xs uppercase tracking-wide">Role</p>
            <p class="text-xl font-semibold">{isGM ? 'GM / Admin' : 'Player'}</p>
            {#if myCharacterId}
              <p class="muted text-sm mt-1">Character ID: {myCharacterId}</p>
            {/if}
          </div>
          <div class="panel panel-strong p-4 rounded-xl">
            <p class="muted text-xs uppercase tracking-wide">Quick links</p>
            <div class="flex flex-wrap gap-2 mt-2">
              <a class="btn btn-ghost" href="/sessions">Session board</a>
              <a class="btn btn-ghost" href="/dashboard/roster">Roster</a>
              {#if isGM}
                <a class="btn btn-ghost" href="/dashboard/admin/sessions">Session admin</a>
              {/if}
              <a class="btn btn-ghost" href="/missions">Mission dossiers</a>
            </div>
          </div>
        </div>
      {:else}
        <div class="panel panel-strong p-4 rounded-xl">
          <p class="muted text-sm">You need to log in to manage signups or create sessions.</p>
          <div class="flex gap-2 mt-3">
            <a href="/login" class="btn btn-primary">Log in</a>
            <a href="/register" class="btn btn-ghost">Register</a>
          </div>
        </div>
      {/if}

      {#if isGM}
        <div class="faded-line"></div>
        <div class="space-y-3">
          <div class="flex items-center justify-between gap-2">
            <h3 class="text-lg font-semibold">Schedule a session</h3>
            <span class="pill">GM only</span>
          </div>
          <form class="space-y-3" on:submit|preventDefault={createSession}>
            <div class="space-y-1">
              <label class="label" for="mission">Mission</label>
              <select
                id="mission"
                class="input-field"
                bind:value={sessionForm.mission_id}
                required
              >
                <option value="" disabled>Select a mission</option>
                {#each missions as mission}
                  <option value={mission.id}>{mission.title}</option>
                {/each}
              </select>
            </div>
            <div class="space-y-1">
              <label class="label" for="title">Title</label>
              <input
                id="title"
                class="input-field"
                type="text"
                required
                placeholder="Scouting party to the Western Wilds"
                bind:value={sessionForm.title}
              />
            </div>
            <div class="space-y-1">
              <label class="label" for="date">Session date</label>
              <input
                id="date"
                class="input-field"
                type="datetime-local"
                required
                bind:value={sessionForm.session_date}
              />
            </div>
            <div class="space-y-1">
              <label class="label" for="gm_notes">GM notes</label>
              <textarea
                id="gm_notes"
                class="input-field min-h-[90px]"
                placeholder="Key prep, party needs, or risk notes."
                bind:value={sessionForm.gm_notes}
              ></textarea>
            </div>
            <div class="space-y-1">
              <label class="label" for="route">Route data (comma separated hexes)</label>
              <input
                id="route"
                class="input-field"
                type="text"
                placeholder="A1, B2, C3"
                bind:value={sessionForm.route_data}
              />
              <p class="muted text-xs">
                Locks the travel path once the Session Captain signs in. Each hex counts toward the 7-day deployment.
              </p>
            </div>
            {#if creationFeedback}
              <p class="text-sm text-amber-200">{creationFeedback}</p>
            {/if}
            <div class="flex gap-2">
              <button class="btn btn-primary" type="submit" disabled={creatingSession}>
                {creatingSession ? 'Scheduling...' : 'Create session'}
              </button>
              <a class="btn btn-muted" href="/dashboard/admin/sessions">Open session admin</a>
            </div>
          </form>
        </div>
      {/if}
    </div>
  </section>

  <section class="panel p-6 space-y-4">
    <SectionHeader
      eyebrow="Mission Dossiers"
      title="Available missions and prep"
      description="Every mission is anchored to a target hex and dossier. Keep them fresh so any GM can pick up and run."
    >
      <div slot="actions" class="flex flex-wrap gap-2">
        <a href="/missions" class="btn btn-ghost">Open missions</a>
      </div>
    </SectionHeader>

    <MissionList
      missions={missions}
      isLoading={missionsLoading}
      error={missionError}
      showEmptyState={true}
      limit={3}
    />
  </section>
</div>
