<script lang="ts">
	import { onDestroy } from 'svelte';
	import { API_BASE_URL } from '$lib/config';
	import { auth } from '$lib/auth';
	import { get } from 'svelte/store';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	export let missionTier: string = '';
	export let missionRegion: string = '';
	export let onOneshotGenerated: (oneshotId: number, description: string) => void;

	let generating = false;
	let error = '';
	let jobId: number | null = null;
	let pollInterval: number | null = null;
	let progress = '';
	let revelationLayer: 'early' | 'mid' | 'late' = 'early';
	let tone = 'heroic';
	let partySize = 4;
	let partyLevel = 3;
	let durationHours = 4.0;
	let hexRegion = missionRegion;

	const layerLabels = {
		early: 'Early — The Frame Shifts',
		mid: 'Mid — The Council Surfaces',
		late: 'Late — The Thing Speaks'
	};

	const toneOptions = [
		{ value: 'heroic', label: 'Heroic' },
		{ value: 'exploration', label: 'Exploration' },
		{ value: 'combat-heavy', label: 'Combat-Heavy' },
		{ value: 'social', label: 'Social / Intrigue' },
		{ value: 'mystery', label: 'Mystery' },
		{ value: 'grimdark', label: 'Grimdark' }
	];

	async function generateOneshot() {
		generating = true;
		error = '';
		progress = 'Initiating generation...';

		try {
			const res = await fetch(`${API_BASE_URL}/oneshot/generate`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${get(auth).token}`
				},
				body: JSON.stringify({
					party_size: partySize,
					party_level: partyLevel,
					duration_hours: durationHours,
					tone,
					hex_region: hexRegion || undefined,
					revelation_layer: revelationLayer
				})
			});

			if (!res.ok) {
				const data = await res.json();
				throw new Error(data.detail || 'Failed to start generation');
			}

			const data = await res.json();
			jobId = data.id;
			progress = 'Generation started...';

			startPolling();
		} catch (e: any) {
			error = e.message || 'Failed to generate one-shot';
			generating = false;
		}
	}

	function startPolling() {
		if (pollInterval) clearInterval(pollInterval);

		pollInterval = window.setInterval(async () => {
			if (!jobId) return;

			try {
				const res = await fetch(`${API_BASE_URL}/oneshot/${jobId}`, {
					headers: { Authorization: `Bearer ${get(auth).token}` }
				});

				if (!res.ok) throw new Error('Failed to check status');

				const data = await res.json();
				progress = `Status: ${data.status}`;

				if (data.status === 'completed') {
					stopPolling();
					generating = false;
					onOneshotGenerated(data.id, data.summary || 'Generated adventure');
				} else if (data.status === 'failed') {
					stopPolling();
					error = 'Generation failed';
					generating = false;
				}
			} catch (e: any) {
				error = e.message;
				stopPolling();
				generating = false;
			}
		}, 2000);
	}

	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
	}

	function cancel() {
		stopPolling();
		generating = false;
		jobId = null;
		progress = '';
	}

	onDestroy(stopPolling);
</script>

<div class="rounded-lg border border-base-300 bg-base-100 p-4">
	<div class="mb-3 flex items-center justify-between">
		<h4 class="text-sm font-bold">AI One-Shot Generator</h4>
		{#if generating}
			<button class="btn btn-xs btn-ghost" on:click={cancel}>Cancel</button>
		{/if}
	</div>

	<p class="mb-4 text-xs opacity-70">
		Generate an Aphtharton adventure framed as a question for the Inheritors. Grounded in the
		campaign's faction state and field reports.
	</p>

	{#if !generating}
		<div class="grid grid-cols-2 gap-3 mb-4">
			<div class="form-control col-span-2">
				<label class="label" for="revelation-layer">
					<span class="label-text text-xs">Campaign Layer</span>
				</label>
				<select
					id="revelation-layer"
					bind:value={revelationLayer}
					class="select select-bordered select-sm w-full"
				>
					{#each Object.entries(layerLabels) as [value, label]}
						<option {value}>{label}</option>
					{/each}
				</select>
			</div>

			<div class="form-control col-span-2">
				<label class="label" for="oneshot-tone">
					<span class="label-text text-xs">Tone / Threat</span>
				</label>
				<select
					id="oneshot-tone"
					bind:value={tone}
					class="select select-bordered select-sm w-full"
				>
					{#each toneOptions as opt}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>

			<div class="form-control">
				<label class="label" for="party-size">
					<span class="label-text text-xs">Party Size</span>
				</label>
				<input
					id="party-size"
					type="number"
					bind:value={partySize}
					min="2"
					max="8"
					class="input input-bordered input-sm w-full"
				/>
			</div>

			<div class="form-control">
				<label class="label" for="party-level">
					<span class="label-text text-xs">Party Level</span>
				</label>
				<input
					id="party-level"
					type="number"
					bind:value={partyLevel}
					min="1"
					max="20"
					class="input input-bordered input-sm w-full"
				/>
			</div>

			<div class="form-control">
				<label class="label" for="duration-hours">
					<span class="label-text text-xs">Duration (hrs)</span>
				</label>
				<input
					id="duration-hours"
					type="number"
					bind:value={durationHours}
					min="1"
					max="12"
					step="0.5"
					class="input input-bordered input-sm w-full"
				/>
			</div>

			<div class="form-control">
				<label class="label" for="hex-region">
					<span class="label-text text-xs">Region / District</span>
				</label>
				<input
					id="hex-region"
					type="text"
					bind:value={hexRegion}
					placeholder="e.g. The Ashen Quarter"
					class="input input-bordered input-sm w-full"
				/>
			</div>
		</div>
	{/if}

	{#if error}
		<div class="alert alert-error mb-4 text-xs">
			{error}
		</div>
	{/if}

	{#if generating}
		<div class="flex items-center gap-3">
			<LoadingSpinner size="sm" />
			<span class="text-xs opacity-70">{progress}</span>
		</div>
	{:else}
		<button class="btn btn-sm btn-primary w-full" on:click={generateOneshot}>
			Generate Adventure
		</button>
	{/if}
</div>
