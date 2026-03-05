<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { get } from 'svelte/store';
	import { API_BASE_URL } from '$lib/config';

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
		events: ReputationEvent[];
	}

	export let isAdmin: boolean = false;

	let reputations: FactionReputation[] = [];
	let loading = true;
	let adjusting: string | null = null;
	let adjustDelta = 1;
	let adjustDescription = '';
	let showAdjustFor: string | null = null;

	const MIN_LEVEL = -5;
	const MAX_LEVEL = 5;

	const FACTION_CONFIG: Record<string, { label: string; color: string; accentColor: string }> = {
		Kathedral: {
			label: 'The Kathedral League',
			color: 'bg-blue-900/40',
			accentColor: 'bg-blue-500'
		},
		Vastarei: {
			label: 'The Vastarei',
			color: 'bg-amber-900/40',
			accentColor: 'bg-amber-500'
		}
	};

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

	onMount(async () => {
		await fetchReputations();
	});

	async function fetchReputations() {
		loading = true;
		try {
			const { token } = get(auth);
			const res = await fetch(`${API_BASE_URL}/factions/`, {
				headers: { Authorization: `Bearer ${token}` }
			});
			if (res.ok) {
				reputations = await res.json();
			}
		} finally {
			loading = false;
		}
	}

	async function submitAdjustment(factionName: string) {
		if (!adjustDescription.trim()) return;
		adjusting = factionName;
		try {
			const { token } = get(auth);
			const res = await fetch(`${API_BASE_URL}/factions/${factionName}/adjust`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${token}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ delta: adjustDelta, description: adjustDescription.trim() })
			});
			if (res.ok) {
				showAdjustFor = null;
				adjustDelta = 1;
				adjustDescription = '';
				await fetchReputations();
			}
		} finally {
			adjusting = null;
		}
	}

	function barFill(level: number): number {
		// Map -5..+5 to 0..100%
		return ((level - MIN_LEVEL) / (MAX_LEVEL - MIN_LEVEL)) * 100;
	}

	function barColor(level: number): string {
		if (level >= 3) return 'bg-success';
		if (level >= 1) return 'bg-info';
		if (level === 0) return 'bg-base-content/30';
		if (level >= -2) return 'bg-warning';
		return 'bg-error';
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
	}
</script>

<div class="space-y-4">
	<h2 class="text-lg font-bold font-[var(--font-cinzel)] text-primary tracking-wide uppercase opacity-80">
		Faction Standing
	</h2>

	{#if loading}
		<div class="flex items-center gap-2 opacity-50 text-sm">
			<span class="loading loading-spinner loading-xs"></span>
			Loading...
		</div>
	{:else}
		{#each reputations as rep}
			{@const config = FACTION_CONFIG[rep.faction_name] ?? { label: rep.faction_name, color: 'bg-base-200', accentColor: 'bg-primary' }}
			{@const levelLabel = LEVEL_LABELS[rep.level] ?? 'Unknown'}
			<div class="rounded-lg border border-base-content/10 {config.color} p-4">
				<div class="flex items-center justify-between mb-2">
					<div>
						<p class="font-semibold text-sm">{config.label}</p>
						<p class="text-xs opacity-60">{levelLabel}</p>
					</div>
					<div class="flex items-center gap-2">
						<span class="font-mono font-bold text-sm {rep.level > 0 ? 'text-success' : rep.level < 0 ? 'text-error' : 'opacity-50'}">
							{rep.level > 0 ? '+' : ''}{rep.level}
						</span>
						{#if isAdmin}
							<button
								class="btn btn-xs btn-ghost"
								on:click={() => { showAdjustFor = showAdjustFor === rep.faction_name ? null : rep.faction_name; }}
							>
								Adjust
							</button>
						{/if}
					</div>
				</div>

				<!-- Reputation bar -->
				<div class="w-full bg-base-300 rounded-full h-2 mb-3">
					<div
						class="h-2 rounded-full transition-all duration-500 {barColor(rep.level)}"
						style="width: {barFill(rep.level)}%"
					></div>
				</div>

				<!-- Admin adjust panel -->
				{#if isAdmin && showAdjustFor === rep.faction_name}
					<div class="mt-3 flex flex-col gap-2 border-t border-base-content/10 pt-3">
						<div class="flex items-center gap-2">
							<label class="text-xs opacity-60 w-12">Change</label>
							<input
								type="number"
								min="-10"
								max="10"
								bind:value={adjustDelta}
								class="input input-xs input-bordered w-20 font-mono"
							/>
						</div>
						<div class="flex items-center gap-2">
							<label class="text-xs opacity-60 w-12">Reason</label>
							<input
								type="text"
								bind:value={adjustDescription}
								placeholder="e.g. Assisted Kathedral patrol"
								class="input input-xs input-bordered flex-1"
							/>
						</div>
						<button
							class="btn btn-xs btn-primary self-end"
							disabled={!!adjusting || !adjustDescription.trim()}
							on:click={() => submitAdjustment(rep.faction_name)}
						>
							{adjusting === rep.faction_name ? 'Saving...' : 'Save'}
						</button>
					</div>
				{/if}

				<!-- Recent events log -->
				{#if rep.events.length > 0}
					<div class="mt-2 space-y-1">
						{#each rep.events.slice(0, 3) as event}
							<div class="flex items-baseline gap-2 text-xs opacity-60">
								<span class="font-mono font-bold {event.delta > 0 ? 'text-success' : 'text-error'}">
									{event.delta > 0 ? '+' : ''}{event.delta}
								</span>
								<span class="truncate">{event.description}</span>
								<span class="ml-auto shrink-0">{formatDate(event.created_at)}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	{/if}
</div>
