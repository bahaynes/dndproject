<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { GameSessionWithPlayers, Mission } from '$lib/types';
	import { MISSIONS_NAV } from '$lib/navigation';
	import SubNav from '$lib/components/SubNav.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
	import Modal from '$lib/components/Modal.svelte';

	let missions: Mission[] = [];
	let openSessions: GameSessionWithPlayers[] = [];
	let loading = true;
	let error = '';
	let successMessage = '';

	let tierFilter = '';
	let statusFilter = 'Available';

	let showProposeModal = false;
	let selectedMission: Mission | null = null;
	let selectedSessionId: number | null = null;

	$: myCharacterId = $auth.user?.active_character?.id;

	onMount(loadData);

	async function loadData() {
		loading = true;
		error = '';
		try {
			const [m, s] = await Promise.all([
				api('GET', '/missions/'),
				api('GET', '/sessions/').catch(() => [])
			]);
			missions = m ?? [];
			openSessions = (s ?? []).filter(
				(sess: GameSessionWithPlayers) =>
					sess.status !== 'Completed' &&
					sess.status !== 'Cancelled' &&
					sess.players.some((p) => p.owner_id === $auth.user?.id)
			);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load quests.';
		} finally {
			loading = false;
		}
	}

	function openPropose(mission: Mission) {
		selectedMission = mission;
		selectedSessionId = openSessions[0]?.id ?? null;
		showProposeModal = true;
	}

	async function submitProposal() {
		if (!selectedMission || !selectedSessionId) return;
		error = '';
		try {
			await api('POST', '/sessions/proposals', {
				session_id: selectedSessionId,
				mission_id: selectedMission.id
			});
			showProposeModal = false;
			successMessage = `Proposed "${selectedMission.name}" for the selected session.`;
			setTimeout(() => (successMessage = ''), 4000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to propose quest.';
		}
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

	function missionItems(m: Mission): string[] {
		return m.rewards.filter((r) => r.item).map((r) => r.item!.name);
	}

	$: tiers = Array.from(new Set(missions.map((m) => m.tier).filter(Boolean))) as string[];
	$: filteredMissions = missions.filter((m) => {
		if (statusFilter && m.status !== statusFilter) return false;
		if (tierFilter && m.tier !== tierFilter) return false;
		return true;
	});
</script>

<div class="page-container">
	<SubNav items={MISSIONS_NAV} />

	<PageHeader
		title="Available Quests"
		subtitle="Browse active contracts and propose them for an upcoming session slot."
	>
		<div slot="actions" class="flex flex-wrap items-center gap-2">
			<select class="select select-bordered select-sm" bind:value={statusFilter} aria-label="Filter by status">
				<option value="">All Statuses</option>
				<option value="Available">Available</option>
				<option value="In Progress">In Progress</option>
				<option value="Completed">Completed</option>
			</select>
			{#if tiers.length > 0}
				<select class="select select-bordered select-sm" bind:value={tierFilter} aria-label="Filter by tier">
					<option value="">All Tiers</option>
					{#each tiers as t}
						<option value={t}>{t}</option>
					{/each}
				</select>
			{/if}
			<button class="btn btn-ghost btn-sm" on:click={loadData}>Refresh</button>
		</div>
	</PageHeader>

	{#if error}
		<div class="alert alert-error mb-6 text-sm">{error}</div>
	{/if}
	{#if successMessage}
		<div class="alert alert-success mb-6 text-sm">{successMessage}</div>
	{/if}

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else if filteredMissions.length === 0}
		<div class="panel p-12 text-center">
			<p class="text-base font-medium text-base-content/75">No quests match your current filters.</p>
			<p class="mt-1 text-sm text-base-content/50">Check back after the DM posts new bounties.</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
			{#each filteredMissions as mission}
				{@const gp = missionGold(mission)}
				{@const xp = missionXp(mission)}
				{@const items = missionItems(mission)}
				{@const cooling = inCooldown(mission)}
				<article class="panel panel-interactive flex flex-col p-5 {cooling ? 'opacity-60' : ''}">
					<div class="mb-3 flex items-start justify-between gap-2">
						<h2 class="text-base font-semibold text-base-content">{mission.name}</h2>
						<span
							class="badge badge-sm shrink-0 {mission.status === 'Available'
								? 'badge-success'
								: mission.status === 'Completed'
									? 'badge-ghost'
									: 'badge-warning'}"
						>
							{mission.status}
						</span>
					</div>

					<div class="mb-3 flex flex-wrap gap-1.5 text-xs">
						{#if mission.tier}
							<span class="rounded bg-base-300 px-2 py-0.5 text-base-content/80">{mission.tier}</span>
						{/if}
						{#if mission.region}
							<span class="rounded bg-base-300 px-2 py-0.5 text-base-content/65">{mission.region}</span>
						{/if}
						{#if cooling}
							<span class="rounded bg-warning/15 px-2 py-0.5 text-warning">Cooldown</span>
						{/if}
					</div>

					<div class="prose prose-sm mb-4 line-clamp-4 flex-1 max-w-none text-xs text-base-content/75">
						<MarkdownRenderer content={mission.description || 'No briefing provided.'} />
					</div>

					<div class="mt-auto border-t border-base-content/10 pt-3">
						<div class="mb-3 flex flex-wrap items-center gap-2 text-xs">
							<span class="section-label">Rewards:</span>
							{#if gp > 0}
								<span class="rounded bg-primary/15 px-2 py-0.5 font-medium text-primary stat-num">
									{gp} GP
								</span>
							{/if}
							{#if xp > 0}
								<span class="rounded bg-secondary/15 px-2 py-0.5 font-medium text-secondary stat-num">
									{xp} XP
								</span>
							{/if}
							{#each items as itemName}
								<span class="rounded bg-base-300 px-2 py-0.5 text-base-content/80">{itemName}</span>
							{/each}
							{#if gp === 0 && xp === 0 && items.length === 0}
								<span class="text-base-content/45">Unspecified</span>
							{/if}
						</div>

						{#if mission.status === 'Available'}
							{#if myCharacterId && !cooling && openSessions.length === 0}
								<a href="/dashboard" class="btn btn-outline btn-sm w-full">
									Join a Session to Propose →
								</a>
							{:else}
								<button
									class="btn btn-primary btn-sm w-full"
									disabled={!myCharacterId || cooling}
									on:click={() => openPropose(mission)}
								>
									{#if !myCharacterId}
										Activate Character to Propose
									{:else if cooling}
										On Cooldown
									{:else}
										Propose for Session
									{/if}
								</button>
							{/if}
						{/if}
					</div>
				</article>
			{/each}
		</div>
	{/if}
</div>

<Modal
	show={showProposeModal}
	title="Propose Quest for Session"
	onClose={() => (showProposeModal = false)}
>
	{#if selectedMission}
		<div class="space-y-4">
			<p class="text-sm text-base-content/80">
				Propose <strong class="text-primary">{selectedMission.name}</strong> for an upcoming session slot:
			</p>
			<div>
				<label for="mission-session-select" class="mb-1 block text-xs font-medium text-base-content/70">
					Open Session Slot
				</label>
				<select
					id="mission-session-select"
					bind:value={selectedSessionId}
					class="select select-bordered select-sm w-full"
				>
					{#each openSessions as sess}
						<option value={sess.id}>
							{sess.name} ({new Date(sess.session_date).toLocaleDateString()})
						</option>
					{/each}
				</select>
			</div>
		</div>
	{/if}
	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={() => (showProposeModal = false)}>Cancel</button>
		<button
			class="btn btn-primary btn-sm"
			disabled={!selectedSessionId}
			on:click={submitProposal}
		>
			Submit Proposal
		</button>
	</div>
</Modal>
