<script lang="ts">
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Modal from '$lib/components/Modal.svelte';
	import FactionReputationTracker from '$lib/components/FactionReputationTracker.svelte';
	import type { Ship, GameSessionWithPlayers, Mission, LedgerEntry } from '$lib/types';

	let bulletin: Ship | null = null;
	let upcomingSessions: GameSessionWithPlayers[] = [];
	let availableMissions: Mission[] = [];
	let recentLedger: LedgerEntry[] = [];
	let loading = true;
	let showOnboarding = false;
	let actionError: string | null = null;

	// Propose modal
	let showProposeModal = false;
	let selectedSessionId: number | null = null;
	let selectedMissionId: number | null = null;
	let dataLoaded = false;

	$: user = $auth.user;
	$: campaign = $auth.campaign;
	$: char = user?.active_character;
	$: myCharacterId = char?.id;

	$: xpCurrent = char?.stats?.xp ?? 0;
	$: xpNext = char?.stats?.next_level_xp ?? null;
	$: xpPct = xpNext ? Math.min(100, Math.round((xpCurrent / xpNext) * 100)) : 100;

	onMount(() => {
		if (!localStorage.getItem('accessToken')) {
			goto('/login');
		}
	});

	$: if ($auth.token && !dataLoaded) {
		dataLoaded = true;
		loadData();
	}

	$: if ($auth.isAuthenticated && !$auth.campaign) {
		goto('/campaigns');
	}

	function dismissOnboarding() {
		showOnboarding = false;
		localStorage.setItem('onboarding_dismissed', '1');
	}

	$: if (!loading && user && !user.active_character) {
		if (!localStorage.getItem('onboarding_dismissed')) {
			showOnboarding = true;
		}
	}

	async function loadData() {
		const [s, sessions, missions, ledger] = await Promise.all([
			api('GET', '/ship/').catch(() => null),
			api('GET', '/sessions/').catch(() => []),
			api('GET', '/missions/').catch(() => []),
			api('GET', '/ledger/?limit=5').catch(() => [])
		]);
		bulletin = s;
		const all: GameSessionWithPlayers[] = sessions ?? [];
		upcomingSessions = all
			.filter((s) => s.status !== 'Completed' && s.status !== 'Cancelled')
			.sort((a, b) => new Date(a.session_date).getTime() - new Date(b.session_date).getTime());
		availableMissions = (missions ?? []).filter((m: Mission) => !m.is_retired && m.is_discoverable);
		recentLedger = ledger ?? [];
		loading = false;
	}

	function isBacking(proposalId: number): boolean {
		if (!myCharacterId) return false;
		for (const session of upcomingSessions) {
			const proposal = session.proposals.find((p) => p.id === proposalId);
			if (proposal) return proposal.backers.some((b) => b.id === myCharacterId);
		}
		return false;
	}

	function isInSession(session: GameSessionWithPlayers): boolean {
		if (!myCharacterId) return false;
		return session.players.some((p) => p.id === myCharacterId);
	}

	async function toggleBacking(proposalId: number) {
		actionError = null;
		try {
			await api('POST', `/sessions/proposals/${proposalId}/toggle_back`);
			await loadData();
		} catch (e) {
			actionError = e instanceof Error ? e.message : 'Failed to update backing.';
		}
	}

	async function joinConfirmedSession(sessionId: number) {
		actionError = null;
		try {
			await api('POST', `/sessions/${sessionId}/signup`);
			await loadData();
		} catch (e) {
			actionError = e instanceof Error ? e.message : 'Failed to join session.';
		}
	}

	async function leaveConfirmedSession(sessionId: number) {
		actionError = null;
		try {
			await api('DELETE', `/sessions/${sessionId}/signup`);
			await loadData();
		} catch (e) {
			actionError = e instanceof Error ? e.message : 'Failed to leave session.';
		}
	}

	async function proposeMission() {
		if (!selectedSessionId || !selectedMissionId) return;
		actionError = null;
		try {
			await api('POST', '/sessions/proposals', {
				session_id: selectedSessionId,
				mission_id: selectedMissionId
			});
			showProposeModal = false;
			await loadData();
		} catch (e) {
			actionError = e instanceof Error ? e.message : 'Failed to propose quest.';
		}
	}

	function openProposeForMission(missionId: number) {
		const openSessions = upcomingSessions.filter((s) => s.status !== 'Confirmed');
		selectedMissionId = missionId;
		selectedSessionId = openSessions[0]?.id ?? null;
		showProposeModal = true;
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleDateString(undefined, {
			weekday: 'short',
			month: 'short',
			day: 'numeric'
		});
	}

	function inCooldown(m: Mission): boolean {
		if (!m.last_run_date) return false;
		return Date.now() - new Date(m.last_run_date).getTime() < m.cooldown_days * 86400000;
	}

	function missionGold(m: Mission): number {
		return m.rewards.reduce((sum, r) => sum + (r.gold ?? 0), 0);
	}

	function missionXp(m: Mission): number {
		return m.rewards.reduce((sum, r) => sum + (r.xp ?? 0), 0);
	}
</script>

{#if loading}
	<div class="flex justify-center py-32">
		<span class="loading loading-spinner loading-lg text-primary"></span>
	</div>
{:else if user}
	<!-- Campaign & Character Status Header -->
	<div class="border-b border-base-content/10 bg-base-200/70">
		<div class="page-container py-6">
			<div class="flex flex-col justify-between gap-6 md:flex-row md:items-center">
				{#if char}
					<div class="min-w-0 flex-1">
						<p class="section-label mb-1">Active Adventurer · {campaign?.name ?? 'Campaign'}</p>
						<div class="flex flex-wrap items-baseline gap-3">
							<h1 class="text-2xl font-semibold text-base-content sm:text-3xl">{char.name}</h1>
							<span class="badge badge-outline badge-sm border-primary/40 text-primary stat-num">
								Level {char.level}
							</span>
							{#if char.class_name}
								<span class="text-sm text-base-content/70">{char.class_name}</span>
							{/if}
						</div>

						<!-- 5e XP & Gold Strip -->
						<div class="mt-3 flex flex-wrap items-center gap-6">
							<div class="flex items-center gap-3">
								<div class="w-40">
									<div class="mb-1 flex justify-between text-xs text-base-content/65 stat-num">
										<span>{xpCurrent.toLocaleString()} XP</span>
										{#if xpNext}
											<span>{xpNext.toLocaleString()}</span>
										{:else}
											<span>MAX</span>
										{/if}
									</div>
									<progress class="progress progress-primary h-1.5 w-full" value={xpPct} max="100"></progress>
								</div>
							</div>
							<div class="text-sm">
								<span class="text-base-content/55">Gold:</span>
								<span class="ml-1 font-semibold text-primary stat-num">{char.stats?.gold ?? 0} GP</span>
							</div>
							<div class="text-sm text-base-content/65">
								<span class="stat-num">{char.missions_completed}</span> completed
							</div>
						</div>
					</div>
				{:else}
					<div>
						<p class="section-label mb-1">Campaign Board</p>
						<h1 class="text-2xl font-semibold text-base-content sm:text-3xl">
							{campaign?.name ?? 'West Marches'}
						</h1>
						<p class="mt-1 text-sm text-base-content/65">Create or activate a character to join sessions.</p>
						<a href="/characters" class="btn btn-primary btn-sm mt-3">Create Character</a>
					</div>
				{/if}

				{#if bulletin?.motd}
					<div class="panel max-w-sm px-4 py-3">
						<p class="section-label mb-1">Campaign Bulletin</p>
						<p class="text-sm text-base-content/85">{bulletin.motd}</p>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<div class="page-container space-y-10">
		{#if actionError}
			<div class="alert alert-error text-sm">{actionError}</div>
		{/if}

		<!-- Upcoming Sessions -->
		<section>
			<div class="mb-4 flex items-baseline justify-between">
				<div>
					<h2 class="text-lg font-semibold text-base-content">Upcoming Sessions</h2>
					<p class="mt-0.5 text-xs text-base-content/60">
						Back a proposed quest to confirm a session, or join an open seat on a confirmed party.
					</p>
				</div>
				<a href="/sessions" class="text-xs font-medium text-primary hover:underline">Full schedule →</a>
			</div>

			{#if upcomingSessions.length === 0}
				<div class="panel p-8 text-center">
					<p class="text-sm text-base-content/60">No upcoming sessions scheduled yet.</p>
				</div>
			{:else}
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					{#each upcomingSessions as session}
						<div class="panel flex flex-col p-5">
							<div class="mb-3 flex items-start justify-between gap-3">
								<div>
									<h3 class="text-base font-semibold text-base-content">{session.name}</h3>
									<p class="mt-0.5 text-xs text-base-content/65 stat-num">
										{formatDate(session.session_date)} · {session.players.length}/{session.max_players} seats
									</p>
								</div>
								<span
									class="badge badge-sm {session.status === 'Confirmed'
										? 'badge-success'
										: 'badge-outline border-warning/40 text-warning'}"
								>
									{session.status}
								</span>
							</div>

							{#if session.status === 'Confirmed' && session.confirmed_mission}
								<div class="mt-1 flex-1 rounded-md border border-success/25 bg-success/5 p-3.5">
									<div class="flex items-start justify-between gap-2">
										<div>
											<p class="section-label text-success">Confirmed Quest</p>
											<p class="mt-0.5 text-sm font-semibold text-base-content">
												{session.confirmed_mission.name}
											</p>
										</div>
										{#if session.confirmed_mission.tier}
											<span class="badge badge-outline badge-xs">{session.confirmed_mission.tier}</span>
										{/if}
									</div>

									<div class="mt-3 flex flex-wrap gap-1.5">
										{#each session.players as player}
											<span class="rounded bg-base-300 px-2 py-0.5 text-xs text-base-content/85">
												{player.name}
											</span>
										{/each}
									</div>
								</div>

								<div class="mt-3 flex items-center justify-end gap-2">
									{#if isInSession(session)}
										<button
											class="btn btn-outline btn-error btn-xs"
											on:click={() => leaveConfirmedSession(session.id)}
										>
											Leave Party
										</button>
									{:else if session.players.length < session.max_players}
										<button
											class="btn btn-primary btn-xs"
											disabled={!myCharacterId}
											on:click={() => joinConfirmedSession(session.id)}
										>
											Join Party ({session.players.length}/{session.max_players})
										</button>
									{:else}
										<span class="text-xs text-base-content/50">Party Full</span>
									{/if}
								</div>
							{:else}
								<div class="flex-1 space-y-2.5">
									{#each session.proposals as proposal}
										<div class="rounded-md border border-base-content/10 bg-base-300/50 p-3">
											<div class="flex items-start justify-between gap-2">
												<div class="min-w-0">
													<p class="truncate text-sm font-medium text-base-content">
														{proposal.mission.name}
													</p>
													{#if proposal.mission.tier}
														<span class="text-xs text-base-content/55">{proposal.mission.tier}</span>
													{/if}
												</div>
												<button
													class="btn btn-xs shrink-0 {isBacking(proposal.id)
														? 'btn-primary'
														: 'btn-outline border-base-content/20'}"
													on:click={() => toggleBacking(proposal.id)}
													disabled={!myCharacterId}
												>
													{isBacking(proposal.id) ? 'Backing' : 'Back'}
												</button>
											</div>
											<div class="mt-2 flex items-center gap-2">
												<progress
													class="progress progress-primary h-1.5 flex-1"
													value={proposal.backers.length}
													max={session.min_players}
												></progress>
												<span class="text-xs text-base-content/65 stat-num">
													{proposal.backers.length}/{session.min_players}
												</span>
											</div>
										</div>
									{/each}

									{#if session.proposals.length === 0}
										<p class="py-3 text-center text-xs text-base-content/50">
											No quest proposals yet.
										</p>
									{/if}
								</div>

								<button
									class="btn btn-ghost btn-xs mt-3 w-full border border-base-content/10"
									disabled={!myCharacterId || availableMissions.length === 0}
									on:click={() => {
										selectedSessionId = session.id;
										selectedMissionId = availableMissions[0]?.id ?? null;
										showProposeModal = true;
									}}
								>
									+ Propose a Quest
								</button>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</section>

		<!-- Available Quests -->
		{#if availableMissions.length > 0}
			<section>
				<div class="mb-4 flex items-baseline justify-between">
					<div>
						<h2 class="text-lg font-semibold text-base-content">Available Quests</h2>
						<p class="mt-0.5 text-xs text-base-content/60">
							Active bounties and expeditions ready to propose for an upcoming session.
						</p>
					</div>
					<a href="/missions" class="text-xs font-medium text-primary hover:underline">All quests →</a>
				</div>

				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each availableMissions.slice(0, 6) as mission}
						{@const gp = missionGold(mission)}
						{@const xp = missionXp(mission)}
						{@const cooling = inCooldown(mission)}
						<div class="panel panel-interactive flex flex-col p-4 {cooling ? 'opacity-55' : ''}">
							<div class="flex items-start justify-between gap-2">
								<h3 class="text-sm font-semibold text-base-content">{mission.name}</h3>
								{#if cooling}
									<span class="badge badge-ghost badge-xs shrink-0">Cooldown</span>
								{/if}
							</div>

							<div class="mt-2 flex flex-wrap gap-1.5 text-xs">
								{#if mission.tier}
									<span class="rounded bg-base-300 px-2 py-0.5 text-base-content/80">{mission.tier}</span>
								{/if}
								{#if mission.region}
									<span class="rounded bg-base-300 px-2 py-0.5 text-base-content/65">{mission.region}</span>
								{/if}
								{#if gp > 0}
									<span class="rounded bg-primary/15 px-2 py-0.5 text-primary stat-num">{gp} GP</span>
								{/if}
								{#if xp > 0}
									<span class="rounded bg-secondary/15 px-2 py-0.5 text-secondary stat-num">{xp} XP</span>
								{/if}
							</div>

							{#if mission.description}
								<p class="mt-2.5 line-clamp-2 flex-1 text-xs text-base-content/65">
									{mission.description}
								</p>
							{/if}

							<div class="mt-3 pt-2 border-t border-base-content/10 flex justify-end">
								<button
									class="btn btn-ghost btn-xs text-primary"
									disabled={!myCharacterId || cooling || upcomingSessions.every((s) => s.status === 'Confirmed')}
									on:click={() => openProposeForMission(mission.id)}
								>
									Propose →
								</button>
							</div>
						</div>
					{/each}
				</div>
			</section>
		{/if}

		<!-- Bottom Summary: Faction Standing + Recent Ledger -->
		<section class="grid grid-cols-1 gap-6 md:grid-cols-2">
			<div class="panel p-5">
				<FactionReputationTracker />
			</div>

			<div class="panel p-5">
				<div class="mb-3 flex items-center justify-between">
					<h2 class="section-label">Recent Ledger Activity</h2>
					<a href="/ledger" class="text-xs font-medium text-primary hover:underline">View ledger →</a>
				</div>
				{#if recentLedger.length === 0}
					<p class="text-xs text-base-content/50">No ledger entries recorded yet.</p>
				{:else}
					<ul class="divide-y divide-base-content/10 text-xs">
						{#each recentLedger as entry}
							<li class="flex items-center justify-between gap-3 py-2">
								<span class="truncate text-base-content/80">{entry.description}</span>
								<span class="shrink-0 text-base-content/45 stat-num">
									{new Date(entry.created_at).toLocaleDateString()}
								</span>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</section>
	</div>
{/if}

<!-- Propose Quest Modal -->
<Modal show={showProposeModal} title="Propose a Quest" onClose={() => (showProposeModal = false)}>
	<div class="space-y-4">
		<div>
			<label for="propose-session" class="mb-1 block text-xs font-medium text-base-content/75">
				Session Slot
			</label>
			<select
				id="propose-session"
				bind:value={selectedSessionId}
				class="select select-bordered select-sm w-full"
			>
				{#each upcomingSessions.filter((s) => s.status !== 'Confirmed') as s}
					<option value={s.id}>{s.name} ({formatDate(s.session_date)})</option>
				{/each}
			</select>
		</div>

		<div>
			<label for="propose-mission" class="mb-1 block text-xs font-medium text-base-content/75">
				Select Quest
			</label>
			<select
				id="propose-mission"
				bind:value={selectedMissionId}
				class="select select-bordered select-sm w-full"
			>
				{#each availableMissions.filter((m) => !inCooldown(m)) as m}
					<option value={m.id}>{m.name} {m.tier ? `(${m.tier})` : ''}</option>
				{/each}
			</select>
		</div>
	</div>
	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={() => (showProposeModal = false)}>Cancel</button>
		<button
			class="btn btn-primary btn-sm"
			disabled={!selectedSessionId || !selectedMissionId}
			on:click={proposeMission}
		>
			Submit Proposal
		</button>
	</div>
</Modal>

<!-- First-Run Onboarding Modal -->
<Modal show={showOnboarding} title="Welcome to the Campaign" onClose={dismissOnboarding}>
	<div class="space-y-3 text-sm text-base-content/80">
		<p>Create your adventurer to join upcoming sessions, earn Gold and XP, and track your inventory.</p>
	</div>
	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={dismissOnboarding}>Later</button>
		<a href="/characters" class="btn btn-primary btn-sm" on:click={dismissOnboarding}>
			Create Character
		</a>
	</div>
</Modal>
