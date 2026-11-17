<script lang="ts">
	import { api } from '$lib/api';
	import Modal from './Modal.svelte';
	import type { Mission } from '$lib/types';

	export let open = false;
	export let sessionId: number | null = null;
	export let missions: Mission[] = [];
	export let hexes: { id: number; q: number; r: number; terrain: string; linked_location_name?: string }[] = [];
	export let onSuccess: () => Promise<void> | void = () => {};
	export let onError: (msg: string) => void = () => {};

	let mode: 'mission' | 'hex' = 'mission';
	let selectedMissionId: number | null = null;
	let selectedHexId: number | null = null;
	let submitting = false;

	$: if (open) {
		if (missions.length > 0) {
			mode = 'mission';
			selectedMissionId = missions[0].id;
		} else if (hexes.length > 0) {
			mode = 'hex';
			selectedHexId = hexes[0].id;
		}
		if (hexes.length > 0 && !selectedHexId) selectedHexId = hexes[0].id;
	}

	async function submit() {
		if (!sessionId) return;
		const payload =
			mode === 'mission'
				? { session_id: sessionId, mission_id: selectedMissionId }
				: { session_id: sessionId, hex_id: selectedHexId };
		if ((mode === 'mission' && !selectedMissionId) || (mode === 'hex' && !selectedHexId)) return;

		submitting = true;
		try {
			await api('POST', '/sessions/proposals', payload);
			open = false;
			await onSuccess();
		} catch (e) {
			onError(e instanceof Error ? e.message : 'Failed to submit proposal.');
		} finally {
			submitting = false;
		}
	}
</script>

<Modal show={open} title="Propose Quest or Hex" onClose={() => (open = false)}>
	<div class="space-y-4">
		<div class="flex gap-2">
			<button
				type="button"
				class="btn btn-sm flex-1 {mode === 'mission' ? 'btn-primary' : 'btn-outline'}"
				on:click={() => (mode = 'mission')}
			>
				Posted Quest
			</button>
			<button
				type="button"
				class="btn btn-sm flex-1 {mode === 'hex' ? 'btn-primary' : 'btn-outline'}"
				on:click={() => (mode = 'hex')}
			>
				Discovered Hex
			</button>
		</div>

		{#if mode === 'mission'}
			{#if missions.length === 0}
				<p class="text-xs text-base-content/60">No posted quests available right now.</p>
			{:else}
				<div>
					<label for="propose-quest-select" class="mb-1 block text-xs font-medium text-base-content/75">
						Select Quest
					</label>
					<select id="propose-quest-select" class="select select-bordered w-full" bind:value={selectedMissionId}>
						{#each missions as m}
							<option value={m.id}>{m.name}{m.tier ? ` (${m.tier})` : ''}</option>
						{/each}
					</select>
				</div>
			{/if}
		{:else}
			{#if hexes.length === 0}
				<p class="text-xs text-base-content/60">No discovered hexes on the map yet.</p>
			{:else}
				<div>
					<label for="propose-hex-select" class="mb-1 block text-xs font-medium text-base-content/75">
						Select Discovered Hex
					</label>
					<select id="propose-hex-select" class="select select-bordered w-full" bind:value={selectedHexId}>
						{#each hexes as h}
							<option value={h.id}>
								Hex ({h.q}, {h.r}) — {h.linked_location_name || h.terrain}
							</option>
						{/each}
					</select>
				</div>
			{/if}
		{/if}
	</div>

	<div slot="action">
		<button type="button" class="btn btn-ghost btn-sm" on:click={() => (open = false)}>Cancel</button>
		<button
			type="button"
			class="btn btn-primary btn-sm"
			disabled={submitting || (mode === 'mission' ? !selectedMissionId : !selectedHexId)}
			on:click={submit}
		>
			{submitting ? 'Proposing...' : 'Propose'}
		</button>
	</div>
</Modal>
