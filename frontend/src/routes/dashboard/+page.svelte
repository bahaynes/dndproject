<script lang="ts">
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Modal from '$lib/components/Modal.svelte';
	import type { Ship, GameSessionWithPlayers, Mission } from '$lib/types';

	let ship: Ship | null = null;
	let upcomingSessions: GameSessionWithPlayers[] = [];
	let availableMissions: Mission[] = [];
	let loading = true;
	let showOnboarding = false;
	let backingError: string | null = null;

	// Propose modal
	let showProposeModal = false;
	let selectedSessionId: number | null = null;
	let selectedMissionId: number | null = null;
	let dataLoaded = false;

	$: user = $auth.user;
	$: campaign = $auth.campaign;
	$: char = user?.active_character;
	$: myCharacterId = char?.id;

	onMount(() => {
		if (!localStorage.getItem('accessToken')) {
			goto('/login');
		} else if ($auth.token && !dataLoaded) {
			dataLoaded = true;
			loadData();
		}
	});

	// Fires when auth hydrates (may be before or after onMount)
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
		try {
			const [s, sessions, missions] = await Promise.all([
				api('GET', '/ship/').catch(() => null),
				api('GET', '/sessions/').catch(() => []),
				api('GET', '/missions/').catch(() => [])
			]);
			ship = s;
			const all: GameSessionWithPlayers[] = sessions ?? [];
			upcomingSessions = all
				.filter((s) => s.status !== 'Completed' && s.status !== 'Cancelled')
				.sort((a, b) => new Date(a.session_date).getTime() - new Date(b.session_date).getTime());
			availableMissions = (missions ?? []).filter((m: Mission) => !m.is_retired && m.is_discoverable);
		} catch (e) {
			console.error('Error loading dashboard data', e);
		} finally {
			loading = false;
		}
	}

	function isBacking(proposalId: number): boolean {
		if (!myCharacterId) return false;
		for (const session of upcomingSessions) {
			const proposal = session.proposals.find((p) => p.id === proposalId);
			if (proposal) return proposal.backers.some((b) => b.id === myCharacterId);
		}
		return false;
	}

	async function toggleBacking(proposalId: number) {
		backingError = null;
		try {
			await api('POST', `/sessions/proposals/${proposalId}/toggle_back`);
			await loadData();
		} catch (e) {
			backingError = e instanceof Error ? e.message : 'Failed to update backing.';
		}
	}

	async function proposeMission() {
		if (!selectedSessionId || !selectedMissionId) return;
		try {
			await api('POST', '/sessions/proposals', {
				session_id: selectedSessionId,
				mission_id: selectedMissionId
			});
			showProposeModal = false;
			await loadData();
		} catch (e) {
			backingError = e instanceof Error ? e.message : 'Failed to propose mission.';
		}
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleDateString(undefined, {
			weekday: 'long',
			month: 'short',
			day: 'numeric'
		});
	}

	function inCooldown(m: Mission): boolean {
		if (!m.last_run_date) return false;
		return Date.now() - new Date(m.last_run_date).getTime() < m.cooldown_days * 86400000;
	}

	$: statusColor =
		ship?.status === 'critical' ? 'error' : ship?.status === 'low' ? 'warning' : 'success';
	$: levelPct = ship && ship.next_threshold && ship.next_threshold > 0
			? Math.round((ship.essence / ship.next_threshold) * 100)
			: 100;
	$: hpPct = ship && ship.max_hp && ship.max_hp > 0 
        ? Math.round((ship.current_hp / ship.max_hp) * 100) 
        : 100;
	$: hpColor = hpPct < 25 ? 'error' : hpPct < 50 ? 'warning' : 'success';
</script>

<div class="min-h-screen">
	{#if loading}
		<div class="flex justify-center py-32">
			<span class="loading loading-lg loading-spinner text-primary"></span>
		</div>
	{:else if user}
		<!-- Character Identity Banner -->
		<div class="border-b border-base-content/10 bg-base-200/60 px-4 py-8">
			<div class="container mx-auto max-w-5xl xl:max-w-screen-xl 2xl:max-w-screen-2xl">
				{#if char}
					<div class="flex flex-wrap items-center justify-between gap-4">
						<div>
							<p class="mb-1 text-xs tracking-widest text-base-content/55 uppercase">
								Active Crew Member
							</p>
							<h1 class="text-3xl font-[var(--font-cinzel)] font-bold tracking-tight text-primary">
								{char.name}
							</h1>
							<div class="mt-1 flex items-center gap-3 text-sm text-base-content/75">
								{#if char.class_name}<span>{char.class_name}</span><span
										class="text-base-content/30">·</span
									>{/if}
								<span>Level {char.level}</span>
								<span class="text-base-content/30">·</span>
								<span class="text-secondary font-bold">💰 {char.stats.gold} GP</span>
							</div>
						</div>
						<div class="flex flex-col items-end gap-2">
							{#if ship}
								<div class="flex items-center gap-4">
									<div class="flex flex-col items-end">
										<div class="flex items-center gap-2">
											<span class="text-[10px] text-base-content/60 uppercase tracking-tighter">Ship Essence</span>
											<span class="badge badge-{statusColor} badge-sm">⚡ {ship.essence}</span>
										</div>
										{#if ship.next_threshold}
											<progress
												class="progress h-1 w-24 progress-primary mt-1"
												value={levelPct}
												max="100"
											></progress>
										{/if}
									</div>
									<div class="flex flex-col items-end">
										<div class="flex items-center gap-2">
											<span class="text-[10px] text-base-content/60 uppercase tracking-tighter">Ship Gold</span>
											<span class="badge badge-secondary badge-sm">🪙 {ship.gold}</span>
										</div>
									</div>
									<div class="flex flex-col items-end">
										<div class="flex items-center gap-2">
											<span class="text-[10px] text-base-content/60 uppercase tracking-tighter">Ship Hull</span>
											<span class="badge badge-{hpColor} badge-sm">❤️ {ship.current_hp}/{ship.max_hp}</span>
										</div>
										<progress
											class="progress h-1 w-24 progress-{hpColor} mt-1"
											value={hpPct}
											max="100"
										></progress>
									</div>
								</div>
							{/if}
							{#if ship?.motd}
								<p class="max-w-xs text-right text-xs text-base-content/60 italic mt-1">"{ship.motd}"</p>
							{/if}
						</div>
					</div>
				{:else}
					<div class="flex flex-wrap items-center justify-between gap-4">
						<div>
							<h1 class="text-3xl font-[var(--font-cinzel)] font-bold tracking-tight text-primary">
								{campaign?.name ?? 'West Marches'}
							</h1>
							<p class="mt-1 text-sm text-base-content/70">You haven't joined the crew yet.</p>
						</div>
						<a href="/characters" class="btn btn-sm btn-primary">Create Your Character →</a>
					</div>
				{/if}
			</div>
		</div>

		<div
			class="container mx-auto max-w-5xl space-y-12 px-4 py-10 xl:max-w-screen-xl 2xl:max-w-screen-2xl"
		>
			<!-- Session Board — Visual Centerpiece -->
			<section>
				<div class="mb-5 flex items-baseline justify-between">
					<div>
						<h2 class="text-2xl font-[var(--font-cinzel)] font-bold text-primary">Mission Board</h2>
						<p class="mt-1 text-xs text-base-content/60">
							Back a proposal to put it on the slate. Needs {upcomingSessions[0]?.min_players ?? 4} crew
							minimum.
						</p>
					</div>
					<a href="/sessions" class="text-xs text-primary transition-colors hover:underline"
						>All sessions →</a
					>
				</div>

				{#if backingError}
					<div class="mb-4 alert text-sm alert-error">{backingError}</div>
				{/if}

				{#if upcomingSessions.length === 0}
					<div class="rounded-xl border border-base-content/10 bg-base-200/40 p-8 text-center">
						<p class="text-sm text-base-content/60 italic">
							No sessions on the board. The DM will post one soon.
						</p>
					</div>
				{:else}
					<div class="grid grid-cols-1 gap-5 md:grid-cols-2">
						{#each upcomingSessions as session}
							<div class="card border border-base-content/10 bg-base-100 shadow-sm">
								<div class="card-body p-5">
									<!-- Session header -->
									<div class="mb-3 flex items-start justify-between">
										<div>
											<h3 class="text-base leading-tight font-[var(--font-cinzel)] font-bold">
												{session.name}
											</h3>
											<p class="mt-1 text-xs text-base-content/65">
												📅 {formatDate(session.session_date)}
											</p>
										</div>
										<span class="badge shrink-0 badge-outline badge-sm capitalize"
											>{session.status}</span
										>
									</div>

									{#if session.status === 'Confirmed' && session.confirmed_mission}
										<!-- Confirmed session -->
										<div class="rounded-lg border border-success/20 bg-success/10 p-3">
											<p class="mb-1 text-xs font-bold tracking-widest text-success/70 uppercase">
												Confirmed
											</p>
											<p class="font-[var(--font-cinzel)] font-bold">
												{session.confirmed_mission.name}
											</p>
											{#if session.confirmed_mission.tier}
												<span class="mt-1 badge badge-outline badge-xs"
													>{session.confirmed_mission.tier}</span
												>
											{/if}
											<div class="mt-2 flex flex-wrap gap-1">
												{#each session.players as player}
													<span class="badge badge-ghost badge-xs">{player.name}</span>
												{/each}
											</div>
										</div>
									{:else}
										<!-- Proposals -->
										<div class="space-y-3">
											{#each session.proposals as proposal}
												<div class="rounded-lg border border-base-content/5 bg-base-200/50 p-3">
													<div class="mb-1 flex items-start justify-between">
														<span class="text-sm font-semibold">{proposal.mission.name}</span>
														<button
															class="btn ml-2 shrink-0 btn-xs {isBacking(proposal.id)
																? 'btn-secondary'
																: 'btn-outline btn-primary'}"
															on:click={() => toggleBacking(proposal.id)}
															disabled={!myCharacterId}
														>
															{isBacking(proposal.id) ? '✓ Backing' : 'Back This'}
														</button>
													</div>
													{#if proposal.mission.tier}
														<span class="badge badge-outline badge-xs text-base-content/70"
															>{proposal.mission.tier}</span
														>
													{/if}
													<div class="mt-2">
														<progress
															class="progress h-1.5 w-full progress-primary"
															value={proposal.backers.length}
															max={session.min_players}
														></progress>
														<p class="mt-1 text-xs text-base-content/65">
															{proposal.backers.length} / {session.min_players} crew
														</p>
													</div>
												</div>
											{/each}

											{#if session.proposals.length === 0}
												<p class="py-2 text-center text-xs text-base-content/50 italic">
													No proposals yet.
												</p>
											{/if}
										</div>

										<div class="mt-3">
											<button
												class="btn w-full border border-base-content/10 btn-ghost btn-xs"
												disabled={!myCharacterId}
												on:click={() => {
													selectedSessionId = session.id;
													showProposeModal = true;
												}}
											>
												+ Propose a Mission
											</button>
										</div>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</section>

			<!-- Available Missions -->
			{#if availableMissions.length > 0}
				<section>
					<div class="mb-5 flex items-baseline justify-between">
						<div>
							<h2 class="text-2xl font-[var(--font-cinzel)] font-bold text-primary">
								Available Contracts
							</h2>
							<p class="mt-1 text-xs text-base-content/60">
								Cleared for dispatch — sign up before the slate fills.
							</p>
						</div>
						<a href="/missions" class="text-xs text-primary transition-colors hover:underline"
							>Full board →</a
						>
					</div>
					<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
						{#each availableMissions.slice(0, 6) as mission}
							<div
								class="rounded-lg border border-base-content/10 bg-base-100 p-4 {inCooldown(mission)
									? 'opacity-50'
									: ''}"
							>
								<div class="flex items-start justify-between gap-2">
									<p class="text-sm leading-tight font-semibold">{mission.name}</p>
									{#if inCooldown(mission)}
										<span class="badge shrink-0 badge-ghost badge-xs">❄️ Cooldown</span>
									{/if}
								</div>
								<div class="mt-2 flex flex-wrap gap-1">
									{#if mission.tier}<span class="badge badge-outline badge-xs">{mission.tier}</span
										>{/if}
									{#if mission.region}<span class="badge badge-ghost badge-xs text-base-content/65"
											>{mission.region}</span
										>{/if}
								</div>
								{#if mission.description}
									<p class="mt-2 line-clamp-2 text-xs text-base-content/65">
										{mission.description}
									</p>
								{/if}
							</div>
						{/each}
					</div>
				</section>
			{/if}

			<!-- Bottom row: Ship + Quick Nav + Admin -->
			<section class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
				<!-- Ship compact -->
				{#if ship}
					<div class="card border border-base-content/10 bg-base-100 shadow-sm">
						<div class="card-body p-5">
							<h3 class="mb-3 text-sm font-[var(--font-cinzel)] font-bold">🚀 {ship.name}</h3>
							
							<div class="space-y-3">
								<div>
									<div class="mb-1 flex items-center justify-between text-xs">
										<span class="text-base-content/65">⚡ Essence Reserve</span>
										<span class="badge badge-{statusColor} badge-xs">{ship.essence}</span>
									</div>
									{#if ship.next_threshold}
										<progress class="progress h-1.5 w-full progress-primary" value={levelPct} max="100"
										></progress>
										<p class="mt-1 text-[10px] text-base-content/60">
											Level {ship.level} → {ship.level + 1} · {ship.essence_to_next_level} to go
										</p>
									{/if}
								</div>

								<div>
									<div class="mb-1 flex items-center justify-between text-xs">
										<span class="text-base-content/65">🪙 Ship Gold</span>
										<span class="badge badge-secondary badge-xs">{ship.gold} GP</span>
									</div>
								</div>

								<div>
									<div class="mb-1 flex items-center justify-between text-xs">
										<span class="text-base-content/65">❤️ Hull Integrity</span>
										<span class="badge badge-{hpColor} badge-xs">{ship.current_hp}/{ship.max_hp}</span>
									</div>
									<progress class="progress h-1.5 w-full progress-{hpColor}" value={hpPct} max="100"
									></progress>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<!-- Quick Nav -->
				<div class="card border border-base-content/10 bg-base-100 shadow-sm">
					<div class="card-body p-5">
						<h3 class="mb-3 text-sm font-[var(--font-cinzel)] font-bold">Navigation</h3>
						<div class="grid grid-cols-2 gap-1 text-xs">
							<a
								href="/characters"
								class="rounded p-2 font-medium text-primary transition-colors duration-150 hover:bg-base-200 focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none"
								>⚔️ Character</a
							>
							<a
								href="/sessions"
								class="rounded p-2 font-medium text-primary transition-colors duration-150 hover:bg-base-200 focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none"
								>📅 Sessions</a
							>
							<a
								href="/missions"
								class="rounded p-2 font-medium text-primary transition-colors duration-150 hover:bg-base-200 focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none"
								>📋 Missions</a
							>
							<a
								href="/store"
								class="rounded p-2 font-medium text-primary transition-colors duration-150 hover:bg-base-200 focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none"
								>🛒 Store</a
							>
							<a
								href="/maps"
								class="rounded p-2 font-medium text-primary transition-colors duration-150 hover:bg-base-200 focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none"
								>🗺️ Maps</a
							>
							<a
								href="/factions"
								class="rounded p-2 font-medium text-primary transition-colors duration-150 hover:bg-base-200 focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none"
								>⚖️ Factions</a
							>
							<a
								href="/ledger"
								class="rounded p-2 font-medium text-primary transition-colors duration-150 hover:bg-base-200 focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none"
								>📖 Ledger</a
							>
							<a
								href="/roster"
								class="rounded p-2 font-medium text-primary transition-colors duration-150 hover:bg-base-200 focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none"
								>👥 Roster</a
							>
							<a
								href="https://github.com/bahaynes/dndproject/wiki"
								target="_blank"
								class="rounded p-2 font-medium text-secondary transition-colors duration-150 hover:bg-base-200 focus-visible:ring-2 focus-visible:ring-secondary/50 focus-visible:outline-none"
								>📖 Wiki</a
							>
						</div>
					</div>
				</div>

				<!-- Admin Tools — neutral, not danger red -->
				{#if user.role === 'admin'}
					<div class="card border border-base-content/10 bg-base-200/50 shadow-sm">
						<div class="card-body p-5">
							<h3 class="mb-3 text-sm font-[var(--font-cinzel)] font-bold text-base-content/65">
								⚙️ DM Tools
							</h3>
							<div class="space-y-1">
								<a
									href="/admin/sessions"
									class="btn w-full justify-start btn-ghost transition-colors btn-xs hover:bg-base-300"
									>Sessions</a
								>
								<a
									href="/admin/missions"
									class="btn w-full justify-start btn-ghost transition-colors btn-xs hover:bg-base-300"
									>Missions</a
								>
								<a
									href="/admin/items"
									class="btn w-full justify-start btn-ghost transition-colors btn-xs hover:bg-base-300"
									>Items</a
								>
								<a
									href="/admin/ship"
									class="btn w-full justify-start btn-ghost transition-colors btn-xs hover:bg-base-300"
									>Ship Config</a
								>
								<a
									href="/admin/stats"
									class="btn w-full justify-start btn-ghost transition-colors btn-xs hover:bg-base-300"
									>Campaign Stats</a
								>
								<a
									href="/admin/maps"
									class="btn w-full justify-start btn-ghost transition-colors btn-xs hover:bg-base-300"
									>Maps</a
								>
							</div>
						</div>
					</div>
				{/if}
			</section>
		</div>
	{:else}
		<p class="p-8 text-base-content/60">Loading...</p>
	{/if}
</div>

<!-- Propose Mission Modal -->
<Modal show={showProposeModal} title="Propose a Mission" onClose={() => (showProposeModal = false)}>
	<div class="form-control w-full">
		<label class="label" for="mission-select">
			<span class="label-text">Select a Mission</span>
		</label>
		<select
			id="mission-select"
			bind:value={selectedMissionId}
			class="select-bordered select w-full"
		>
			<option value={null}>— Pick a Mission —</option>
			{#each availableMissions as mission}
				<option value={mission.id} disabled={inCooldown(mission)}>
					{mission.name}
					{mission.tier ? `(${mission.tier})` : ''}{inCooldown(mission) ? ' — ❄️ Cooldown' : ''}
				</option>
			{/each}
		</select>
		<p class="mt-3 text-sm text-base-content/65 italic">Proposing adds you as the first backer.</p>
	</div>
	<div slot="action">
		<button class="btn w-full btn-primary" on:click={proposeMission} disabled={!selectedMissionId}>
			Propose Now
		</button>
	</div>
</Modal>

<!-- Onboarding modal -->
{#if showOnboarding}
	<div class="modal-open modal">
		<div class="modal-box max-w-lg">
			<h3 class="mb-1 text-2xl font-[var(--font-cinzel)] font-bold text-primary">
				Welcome aboard.
			</h3>
			<p class="mb-4 text-sm text-base-content/65">— {ship?.name ?? 'Your Captain'}</p>
			<div class="prose prose-sm mb-6 max-w-none text-base-content/80">
				<p>
					"New crew. Good. I'll keep this brief. What we earn goes into the reserves. What we spend
					comes out of them. The ledger doesn't lie."
				</p>
				<p>
					"First thing: make yourself a character record. After that, check the mission board. Vote
					on what runs. Show up when the session starts."
				</p>
				<p class="text-xs text-base-content/60">"Questions? Ask your crewmates first."</p>
			</div>
			<div class="flex flex-col gap-3">
				<a href="/characters" class="btn w-full btn-primary" on:click={dismissOnboarding}>
					Create Your Character
				</a>
				<a href="/missions" class="btn w-full btn-outline" on:click={dismissOnboarding}>
					📋 View Mission Board
				</a>
				<button class="btn mt-2 text-base-content/55 btn-ghost btn-xs" on:click={dismissOnboarding}>
					Dismiss — I know what I'm doing
				</button>
			</div>
		</div>
		<button class="modal-backdrop" aria-label="Close" on:click={dismissOnboarding}></button>
	</div>
{/if}
