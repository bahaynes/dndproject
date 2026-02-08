<script lang="ts">
	import { API_BASE_URL } from '$lib/config';
	import { auth } from '$lib/auth';
	import { get } from 'svelte/store';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	export let missionTier: string = '';
	export let missionRegion: string = '';
	export let onOneshotGenerated: (oneshotId: number, description: string) => void;

	let generating = false;
	let error = '';
	let generationId: string | null = null;
	let pollInterval: number | null = null;
	let progress = '';

	async function generateOneshot() {
		generating = true;
		error = '';
		progress = 'Initializing generation...';

		try {
			const res = await fetch(`${API_BASE_URL}/oneshot/generate`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${get(auth).token}`
				},
				body: JSON.stringify({
					tier: missionTier || 'Tier 1',
					region: missionRegion || 'Unknown Region',
					theme: 'adventure'
				})
			});

			if (!res.ok) {
				const data = await res.json();
				throw new Error(data.detail || 'Failed to start generation');
			}

			const data = await res.json();
			generationId = data.generation_id;
			progress = 'Generation started...';

			// Start polling for status
			startPolling();
		} catch (e: any) {
			error = e.message || 'Failed to generate one-shot';
			generating = false;
		}
	}

	function startPolling() {
		if (pollInterval) clearInterval(pollInterval);

		pollInterval = window.setInterval(async () => {
			if (!generationId) return;

			try {
				const res = await fetch(`${API_BASE_URL}/oneshot/status/${generationId}`, {
					headers: { Authorization: `Bearer ${get(auth).token}` }
				});

				if (!res.ok) throw new Error('Failed to check status');

				const data = await res.json();
				progress = `Status: ${data.status}`;

				if (data.status === 'completed') {
					stopPolling();
					generating = false;
					onOneshotGenerated(data.oneshot_id, data.narrative || 'Generated adventure');
				} else if (data.status === 'failed') {
					stopPolling();
					error = data.error || 'Generation failed';
					generating = false;
				}
			} catch (e: any) {
				error = e.message;
				stopPolling();
				generating = false;
			}
		}, 2000); // Poll every 2 seconds
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
		generationId = null;
		progress = '';
	}
</script>

<div class="rounded-lg border border-base-300 bg-base-100 p-4">
	<div class="mb-3 flex items-center justify-between">
		<h4 class="text-sm font-bold">🎲 AI One-Shot Generator</h4>
		{#if generating}
			<button class="btn btn-xs btn-ghost" on:click={cancel}>Cancel</button>
		{/if}
	</div>

	<p class="mb-4 text-xs opacity-70">
		Generate an AI-powered adventure narrative based on the mission tier and region. This will create
		a detailed one-shot adventure that can be exported to FoundryVTT.
	</p>

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
