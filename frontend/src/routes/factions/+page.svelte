<script lang="ts">
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import { WORLD_NAV } from '$lib/navigation';
	import SubNav from '$lib/components/SubNav.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	interface ReputationEvent {
		id: number;
		delta: number;
		description: string;
		session_id: number | null;
		created_at: string;
	}

	interface FactionReputation {
		id: number;
		faction_name: string;
		level: number;
		color: string | null;
		description: string | null;
		events: ReputationEvent[];
	}

	let reputations: FactionReputation[] = [];
	let loading = true;
	let isAdmin = false;

	// Create faction form
	let showCreateForm = false;
	let createName = '';
	let createColor = '#6b7280';
	let createDescription = '';
	let creating = false;
	let createError = '';

	// Adjust state
	let showAdjustFor: string | null = null;
	let adjustDelta = 1;
	let adjustDescription = '';
	let adjusting: string | null = null;

	// Delete confirm
	let confirmDeleteFor: string | null = null;
	let deleting: string | null = null;

	const MIN_LEVEL = -5;
	const MAX_LEVEL = 5;

	const LEVEL_LABELS: Record<number, string> = {
		5: 'Sworn Allies',
		4: 'Trusted',
		3: 'Friendly',
		2: 'Cooperative',
		1: 'Cautiously Warm',
		0: 'Neutral',
		'-1': 'Wary',
		'-2': 'Suspicious',
		'-3': 'Hostile',
		'-4': 'Enemies',
		'-5': 'Blood Feud'
	};

	auth.subscribe((v) => {
		isAdmin = v.user?.role === 'admin';
	});

	onMount(fetchReputations);

	async function fetchReputations() {
		loading = true;
		reputations = await api('GET', '/factions/').catch(() => []);
		loading = false;
	}

	async function submitCreate() {
		if (!createName.trim()) return;
		creating = true;
		createError = '';
		try {
			await api('POST', '/factions/', {
				faction_name: createName.trim(),
				color: createColor,
				description: createDescription.trim() || null
			});
			showCreateForm = false;
			createName = '';
			createColor = '#6b7280';
			createDescription = '';
			await fetchReputations();
		} catch (e) {
			createError = e instanceof Error ? e.message : 'Failed to create faction.';
		}
		creating = false;
	}

	async function submitAdjust(factionName: string) {
		if (!adjustDescription.trim()) return;
		adjusting = factionName;
		try {
			await api('POST', `/factions/${encodeURIComponent(factionName)}/adjust`, {
				delta: adjustDelta,
				description: adjustDescription.trim()
			});
			showAdjustFor = null;
			adjustDelta = 1;
			adjustDescription = '';
			await fetchReputations();
		} catch (e) {}
		adjusting = null;
	}

	async function confirmDelete(factionName: string) {
		deleting = factionName;
		try {
			await api('DELETE', `/factions/${encodeURIComponent(factionName)}`);
		} catch (e) {}
		confirmDeleteFor = null;
		deleting = null;
		await fetchReputations();
	}

	function barFill(level: number): number {
		return ((level - MIN_LEVEL) / (MAX_LEVEL - MIN_LEVEL)) * 100;
	}

	function barColorClass(level: number): string {
		if (level >= 3) return 'bg-success';
		if (level >= 1) return 'bg-info';
		if (level === 0) return 'bg-base-content/30';
		if (level >= -2) return 'bg-warning';
		return 'bg-error';
	}

	function factionColor(rep: FactionReputation): string {
		return rep.color ?? '#6b7280';
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString(undefined, {
			day: 'numeric',
			month: 'short',
			year: '2-digit'
		});
	}
</script>

<div class="page-container">
	<SubNav items={WORLD_NAV} />

	<PageHeader
		title="Faction Standing"
		subtitle="Your party's reputation with each active faction across the campaign."
	>
		<div slot="actions">
			{#if isAdmin}
				<button
					class="btn btn-primary btn-sm"
					on:click={() => {
						showCreateForm = !showCreateForm;
						createError = '';
					}}
				>
					{showCreateForm ? 'Cancel' : '+ Add Faction'}
				</button>
			{/if}
		</div>
	</PageHeader>

	{#if isAdmin && showCreateForm}
		<div class="panel border-primary/35 mb-6 p-5">
			<h2 class="section-label mb-3">New Faction</h2>
			<div class="grid grid-cols-1 gap-3 md:grid-cols-2">
				<div>
					<label for="faction-name" class="mb-1 block text-xs text-base-content/70">Name</label>
					<input
						id="faction-name"
						type="text"
						bind:value={createName}
						placeholder="e.g. The Guildhall"
						class="input input-sm input-bordered w-full"
					/>
				</div>
				<div>
					<label for="faction-color" class="mb-1 block text-xs text-base-content/70">Color</label>
					<div class="flex items-center gap-2">
						<input
							type="color"
							bind:value={createColor}
							class="h-8 w-10 cursor-pointer rounded border border-base-content/20 bg-transparent"
						/>
						<input
							id="faction-color"
							type="text"
							bind:value={createColor}
							class="input input-sm input-bordered flex-1 font-mono"
							placeholder="#6b7280"
						/>
					</div>
				</div>
				<div class="md:col-span-2">
					<label for="faction-desc" class="mb-1 block text-xs text-base-content/70">
						Description (optional)
					</label>
					<input
						id="faction-desc"
						type="text"
						bind:value={createDescription}
						placeholder="One-line summary"
						class="input input-sm input-bordered w-full"
					/>
				</div>
			</div>
			{#if createError}
				<p class="mt-2 text-xs text-error">{createError}</p>
			{/if}
			<div class="mt-3 flex justify-end">
				<button
					class="btn btn-primary btn-sm"
					disabled={creating || !createName.trim()}
					on:click={submitCreate}
				>
					{creating ? 'Creating...' : 'Create Faction'}
				</button>
			</div>
		</div>
	{/if}

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else if reputations.length === 0}
		<div class="panel p-12 text-center text-sm text-base-content/60">
			No factions recorded yet.
		</div>
	{:else}
		<div class="space-y-4">
			{#each reputations as rep (rep.id)}
				{@const levelLabel = LEVEL_LABELS[rep.level] ?? 'Unknown'}
				<article
					class="panel overflow-hidden p-5"
					style="border-left: 3px solid {factionColor(rep)}"
				>
					<div class="flex items-start justify-between gap-3">
						<div class="min-w-0 flex-1">
							<div class="flex flex-wrap items-center gap-2">
								<h2 class="text-base font-semibold text-base-content">{rep.faction_name}</h2>
								<span class="badge badge-outline badge-xs">{levelLabel}</span>
							</div>
							{#if rep.description}
								<p class="mt-1 text-xs text-base-content/65">{rep.description}</p>
							{/if}
						</div>

						<div class="flex shrink-0 items-center gap-2">
							<span
								class="stat-num text-base font-semibold {rep.level > 0
									? 'text-success'
									: rep.level < 0
										? 'text-error'
										: 'text-base-content/45'}"
							>
								{rep.level > 0 ? '+' : ''}{rep.level}
							</span>
							{#if isAdmin}
								<button
									class="btn btn-ghost btn-xs"
									on:click={() => {
										showAdjustFor = showAdjustFor === rep.faction_name ? null : rep.faction_name;
										adjustDelta = 1;
										adjustDescription = '';
									}}
								>
									Adjust
								</button>
								<button
									class="btn btn-ghost btn-xs text-error"
									aria-label="Delete {rep.faction_name}"
									on:click={() => {
										confirmDeleteFor = rep.faction_name;
									}}
								>
									×
								</button>
							{/if}
						</div>
					</div>

					<div class="mt-3 h-1.5 w-full rounded-full bg-base-300">
						<div
							class="h-1.5 rounded-full transition-all duration-300 {barColorClass(rep.level)}"
							style="width: {barFill(rep.level)}%"
						></div>
					</div>

					{#if isAdmin && showAdjustFor === rep.faction_name}
						<div class="mt-3 grid grid-cols-1 gap-2 border-t border-base-content/10 pt-3 sm:grid-cols-3">
							<div class="flex items-center gap-2">
								<label for="adj-delta-{rep.id}" class="w-14 shrink-0 text-xs text-base-content/65">
									Delta
								</label>
								<input
									id="adj-delta-{rep.id}"
									type="number"
									min="-10"
									max="10"
									bind:value={adjustDelta}
									class="input input-xs input-bordered w-20 stat-num"
								/>
							</div>
							<div class="flex items-center gap-2 sm:col-span-2">
								<label for="adj-reason-{rep.id}" class="w-14 shrink-0 text-xs text-base-content/65">
									Reason
								</label>
								<input
									id="adj-reason-{rep.id}"
									type="text"
									bind:value={adjustDescription}
									placeholder="What happened?"
									class="input input-xs input-bordered flex-1"
								/>
								<button
									class="btn btn-primary btn-xs shrink-0"
									disabled={!!adjusting || !adjustDescription.trim()}
									on:click={() => submitAdjust(rep.faction_name)}
								>
									{adjusting === rep.faction_name ? '...' : 'Save'}
								</button>
							</div>
						</div>
					{/if}

					{#if isAdmin && confirmDeleteFor === rep.faction_name}
						<div class="mt-3 flex items-center gap-3 border-t border-error/25 pt-3">
							<p class="flex-1 text-xs text-error">
								Remove <strong>{rep.faction_name}</strong> and its history?
							</p>
							<button
								class="btn btn-error btn-xs"
								disabled={deleting === rep.faction_name}
								on:click={() => confirmDelete(rep.faction_name)}
							>
								{deleting === rep.faction_name ? '...' : 'Delete'}
							</button>
							<button class="btn btn-ghost btn-xs" on:click={() => (confirmDeleteFor = null)}>
								Cancel
							</button>
						</div>
					{/if}

					{#if rep.events.length > 0}
						<div class="mt-3 space-y-1 border-t border-base-content/10 pt-3">
							<p class="section-label mb-1.5">History</p>
							{#each rep.events as event}
								<div class="flex items-baseline gap-2 text-xs">
									<span
										class="w-7 shrink-0 text-right font-semibold stat-num {event.delta > 0
											? 'text-success'
											: 'text-error'}"
									>
										{event.delta > 0 ? '+' : ''}{event.delta}
									</span>
									<span class="flex-1 text-base-content/75">{event.description}</span>
									<span class="shrink-0 text-base-content/45 stat-num">
										{formatDate(event.created_at)}
									</span>
								</div>
							{/each}
						</div>
					{/if}
				</article>
			{/each}
		</div>
	{/if}
</div>
