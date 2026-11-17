<script lang="ts">
	import { auth, login } from '$lib/auth';
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Modal from '$lib/components/Modal.svelte';
	import SessionCard from '$lib/components/SessionCard.svelte';
	import ProposeModal from '$lib/components/ProposeModal.svelte';
	import type { Ship, GameSessionWithPlayers, Mission, Character } from '$lib/types';

	let bulletin: Ship | null = null;
	let upcomingSessions: GameSessionWithPlayers[] = [];
	let pendingRecapSession: GameSessionWithPlayers | null = null;
	let availableMissions: Mission[] = [];
	let discoveredHexes: { id: number; q: number; r: number; terrain: string; linked_location_name?: string }[] = [];
	let myCharacters: Character[] = [];
	let loading = true;
	let actionError: string | null = null;

	// First-run character creation modal
	let showCreateCharModal = false;
	let newName = '';
	let newClass = '';
	let newSheetUrl = '';
	let creatingChar = false;

	// Propose modal
	let showProposeModal = false;
	let proposeSessionId: number | null = null;
	let dataLoaded = false;

	$: user = $auth.user;
	$: campaign = $auth.campaign;
	$: char = user?.active_character;
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

	$: if (!loading && user && !user.active_character && myCharacters.length === 0) {
		showCreateCharModal = true;
	}

	async function loadData() {
		const [s, sessions, missions, chars, maps] = await Promise.all([
			api('GET', '/ship/').catch(() => null),
			api('GET', '/sessions/').catch(() => []),
			api('GET', '/missions/').catch(() => []),
			api('GET', '/characters/').catch(() => []),
			api('GET', '/maps/').catch(() => [])
		]);
		bulletin = s;
		myCharacters = chars ?? [];
		const all: GameSessionWithPlayers[] = sessions ?? [];
		upcomingSessions = all
			.filter((sess) => sess.status !== 'Completed' && sess.status !== 'Cancelled')
			.sort((a, b) => new Date(a.session_date).getTime() - new Date(b.session_date).getTime());

		const completedMine = all
			.filter(
				(sess) =>
					sess.status === 'Completed' &&
					!sess.field_report &&
					sess.players.some((p) => p.owner_id === $auth.user?.id)
			)
			.sort((a, b) => new Date(b.session_date).getTime() - new Date(a.session_date).getTime());
		pendingRecapSession = completedMine[0] ?? null;

		availableMissions = (missions ?? []).filter((m: Mission) => !m.is_retired && m.is_discoverable);
		discoveredHexes = (maps ?? []).flatMap((m: any) => (m.hexes ?? []).filter((h: any) => h.is_discovered));
		loading = false;
	}

	async function handleCreateFirstCharacter() {
		if (!newName.trim()) return;
		creatingChar = true;
		actionError = null;
		try {
			const created = await api('POST', '/characters/', {
				name: newName.trim(),
				class_name: newClass.trim() || null,
				character_sheet_url: newSheetUrl.trim() || null,
				description: 'Ready for adventure.'
			});
			const updatedUser = await api('POST', `/characters/${created.id}/activate`);
			if ($auth.token) {
				login(updatedUser, $auth.token, $auth.campaign ?? undefined);
			}
			showCreateCharModal = false;
			newName = '';
			newClass = '';
			newSheetUrl = '';
			await loadData();
		} catch (e) {
			actionError = e instanceof Error ? e.message : 'Failed to create character.';
		} finally {
			creatingChar = false;
		}
	}

	function openPropose(sessionId: number) {
		proposeSessionId = sessionId;
		showProposeModal = true;
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

						<div class="mt-3 flex flex-wrap items-center gap-6">
							<div class="w-40">
								<div class="mb-1 flex justify-between text-xs text-base-content/65 stat-num">
									<span>{xpCurrent.toLocaleString()} XP</span>
									<span>{xpNext ? xpNext.toLocaleString() : 'MAX'}</span>
								</div>
								<progress class="progress progress-primary h-1.5 w-full" value={xpPct} max="100"></progress>
							</div>
							<div class="text-sm">
								<span class="text-base-content/55">Gold:</span>
								<span class="ml-1 font-semibold text-primary stat-num">{char.stats?.gold ?? 0} GP</span>
							</div>
							<a href="/docs" class="text-xs font-medium text-primary hover:underline">
								How West Marches Works →
							</a>
						</div>
					</div>
				{:else}
					<div>
						<p class="section-label mb-1">Campaign Board</p>
						<h1 class="text-2xl font-semibold text-base-content sm:text-3xl">
							{campaign?.name ?? 'West Marches'}
						</h1>
						<p class="mt-1 text-sm text-base-content/65">Create or activate a character to claim a seat.</p>
						<div class="mt-3 flex items-center gap-3">
							<button class="btn btn-primary btn-sm" on:click={() => (showCreateCharModal = true)}>
								Create Character
							</button>
							<a href="/docs" class="text-xs font-medium text-primary hover:underline">
								How West Marches Works →
							</a>
						</div>
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

	<div class="page-container space-y-8">
		{#if actionError}
			<div class="alert alert-error text-sm">{actionError}</div>
		{/if}

		{#if pendingRecapSession}
			<div class="panel flex flex-wrap items-center justify-between gap-4 border-primary/30 bg-primary/5 px-5 py-3.5">
				<div>
					<p class="section-label text-primary">Last Session Recap</p>
					<p class="text-sm text-base-content/85">
						<strong>{pendingRecapSession.name}</strong> wrapped up — add your party's field report!
					</p>
				</div>
				<a href="/sessions" class="btn btn-primary btn-xs">Write Field Report</a>
			</div>
		{/if}

		<!-- Upcoming Sessions ("I'm Playing This Week") -->
		<section>
			<div class="mb-4 flex items-baseline justify-between">
				<div>
					<h2 class="text-lg font-semibold text-base-content">Play This Week</h2>
					<p class="mt-0.5 text-xs text-base-content/60">
						Claim a seat for an upcoming session, then vote on a quest or hex—or decide night-of.
					</p>
				</div>
				<a href="/sessions" class="text-xs font-medium text-primary hover:underline">Full schedule →</a>
			</div>

			{#if upcomingSessions.length === 0}
				<div class="panel p-10 text-center">
					<p class="text-sm text-base-content/65">No upcoming sessions posted yet.</p>
					<p class="mt-1 text-xs text-base-content/45">Check back soon or browse <a href="/missions" class="text-primary hover:underline">Available Quests</a>.</p>
				</div>
			{:else}
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					{#each upcomingSessions as session}
						<SessionCard
							{session}
							userId={user.id}
							activeCharacterId={char?.id}
							{myCharacters}
							onRefresh={loadData}
							onOpenPropose={openPropose}
							onError={(msg) => (actionError = msg)}
						/>
					{/each}
				</div>
			{/if}
		</section>
	</div>
{/if}

<!-- First-Run Character Onboarding Modal -->
<Modal show={showCreateCharModal} title="Create Your Adventurer" onClose={() => (showCreateCharModal = false)}>
	<form on:submit|preventDefault={handleCreateFirstCharacter} class="space-y-4">
		<p class="text-xs text-base-content/70">
			Welcome to {campaign?.name ?? 'the campaign'}! Create your character to claim a seat at the table.
		</p>
		<div>
			<label for="onboard-name" class="mb-1 block text-xs font-medium text-base-content/75">Character Name *</label>
			<input id="onboard-name" type="text" class="input input-bordered w-full" placeholder="e.g. Lyra Vance" bind:value={newName} required />
		</div>
		<div>
			<label for="onboard-class" class="mb-1 block text-xs font-medium text-base-content/75">Class</label>
			<input id="onboard-class" type="text" class="input input-bordered w-full" placeholder="e.g. Rogue, Cleric" bind:value={newClass} />
		</div>
		<div>
			<label for="onboard-sheet" class="mb-1 block text-xs font-medium text-base-content/75">Character Sheet URL</label>
			<input id="onboard-sheet" type="url" class="input input-bordered w-full" placeholder="D&D Beyond or Foundry link" bind:value={newSheetUrl} />
		</div>
		<div class="flex justify-end gap-2 pt-2">
			<button type="button" class="btn btn-ghost btn-sm" on:click={() => (showCreateCharModal = false)}>Later</button>
			<button type="submit" class="btn btn-primary btn-sm" disabled={creatingChar || !newName.trim()}>
				{creatingChar ? 'Creating...' : 'Join Campaign'}
			</button>
		</div>
	</form>
</Modal>

<ProposeModal
	bind:open={showProposeModal}
	sessionId={proposeSessionId}
	missions={availableMissions}
	hexes={discoveredHexes}
	onSuccess={loadData}
	onError={(msg) => (actionError = msg)}
/>
