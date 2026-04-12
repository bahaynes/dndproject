<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { Mission, Item } from '$lib/types';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import OneshotGenerator from '$lib/components/OneshotGenerator.svelte';
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
	import { goto } from '$app/navigation';

	let missions: Mission[] = [];
	let availableItems: Item[] = [];
	let loading = true;
	let error = '';
	let success = '';

	// Mission form state
	let showCreateMission = false;
	let editingMissionId: number | null = null;
	let mName = '';
	let mDescription = '';
	let mDescriptionTab: 'write' | 'preview' = 'write';
	let mStatus = 'Available';
	let mTier = '';
	let mRegion = '';
	let mCooldown = 7;
	let mIsRetired = false;
	let mIsDiscoverable = true;
	let mPrerequisiteId: number | undefined = undefined;
	let mOneshotId: number | null = null;
	let showOneshotGenerator = false;
	let showAdvanced = false;

	// Simplified reward state
	let mEssencePayout = 4;
	let mDifficulty = 'Standard';
	let mItemRewardId: number | undefined = undefined;

	// Payout table from world bible (net Essence after transit)
	const PAYOUTS: Record<string, Record<string, number>> = {
		'Tier 1': { Routine: 2, Standard: 4, Hard: 6, Extreme: 10 },
		'Tier 2': { Routine: 4, Standard: 8, Hard: 12, Extreme: 20 },
		'Tier 3': { Routine: 6, Standard: 12, Hard: 18, Extreme: 30 },
		'Tier 4': { Routine: 8, Standard: 16, Hard: 24, Extreme: 40 },
	};

	$: suggestedPayout = (mTier && PAYOUTS[mTier]?.[mDifficulty]) ?? null;

	function applyPayout() {
		if (suggestedPayout !== null) mEssencePayout = suggestedPayout;
	}

	const STATUS_LABELS: Record<string, string> = {
		Available: 'On the Board',
		'In Progress': 'Underway',
		Completed: 'Completed',
		Cancelled: 'Cancelled',
	};

	function displayStatus(s: string) {
		return STATUS_LABELS[s] ?? s;
	}

	function openCreate() {
		editingMissionId = null;
		mName = '';
		mDescription = '';
		mStatus = 'Available';
		mTier = '';
		mRegion = '';
		mCooldown = 7;
		mIsRetired = false;
		mIsDiscoverable = true;
		mPrerequisiteId = undefined;
		mOneshotId = null;
		showOneshotGenerator = false;
		mDescriptionTab = 'write';
		showAdvanced = false;
		mEssencePayout = 4;
		mDifficulty = 'Standard';
		mItemRewardId = undefined;
		showCreateMission = true;
	}

	function openEdit(mission: Mission) {
		editingMissionId = mission.id;
		mName = mission.name;
		mDescription = mission.description || '';
		mStatus = mission.status;
		mTier = mission.tier || '';
		mRegion = mission.region || '';
		mCooldown = mission.cooldown_days;
		mIsRetired = mission.is_retired;
		mIsDiscoverable = mission.is_discoverable;
		mPrerequisiteId = mission.prerequisite_id;
		// Pull first reward row's xp as essence payout
		mEssencePayout = mission.rewards[0]?.xp ?? 4;
		mItemRewardId = mission.rewards.find((r) => r.item_id)?.item_id;
		mOneshotId = (mission as any).oneshot_id || null;
		showOneshotGenerator = false;
		mDescriptionTab = 'write';
		showAdvanced = false;
		mDifficulty = 'Standard';
		showCreateMission = true;
	}

	onMount(async () => {
		if (!$auth.isAuthenticated || $auth.user?.role !== 'admin') {
			goto('/dashboard');
			return;
		}
		await reloadData();
	});

	async function reloadData() {
		loading = true;
		try {
			await Promise.all([fetchMissions(), fetchItems()]);
		} catch (e) {
			error = 'Failed to load missions.';
		} finally {
			loading = false;
		}
	}

	async function fetchMissions() {
		missions = await api('GET', '/missions/');
	}

	async function fetchItems() {
		availableItems = await api('GET', '/items/');
	}

	async function saveMission() {
		try {
			const rewards = [{ xp: mEssencePayout, scrip: 0, item_id: mItemRewardId || null }];
			const body = {
				name: mName,
				description: mDescription,
				status: mStatus,
				tier: mTier || null,
				region: mRegion || null,
				cooldown_days: mCooldown,
				is_retired: mIsRetired,
				is_discoverable: mIsDiscoverable,
				prerequisite_id: mPrerequisiteId || null,
				oneshot_id: mOneshotId || null,
				rewards
			};
			if (editingMissionId) {
				await api('PUT', `/missions/${editingMissionId}`, body);
			} else {
				await api('POST', '/missions/', body);
			}
			success = editingMissionId ? 'Mission updated.' : 'Mission posted to the board.';
			showCreateMission = false;
			await fetchMissions();
		} catch (e) {
			error = 'Failed to save mission.';
		}
	}

	async function patchStatus(id: number, status: string) {
		try {
			await api('PUT', `/missions/${id}/status?status=${status}`);
			await fetchMissions();
		} catch (e) {}
	}

	function handleOneshotGenerated(oneshotId: number, description: string) {
		mOneshotId = oneshotId;
		if (!mDescription) {
			mDescription = description.substring(0, 500) + '...';
		}
		success = 'One-shot adventure generated!';
		showOneshotGenerator = false;
	}
</script>

<div class="container mx-auto max-w-6xl p-4">
	<div class="mb-8 flex items-center justify-between">
		<h1 class="text-4xl font-[var(--font-cinzel)] font-bold text-primary">Mission Board</h1>
		<button class="btn btn-primary" on:click={openCreate}>+ New Mission</button>
	</div>

	{#if success}
		<div class="mb-4 alert alert-success">{success}</div>
	{/if}
	{#if error}
		<div class="mb-4 alert alert-error">{error}</div>
	{/if}

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else}
		<div class="grid grid-cols-1 gap-4">
			{#each missions as mission}
				<div class="card bg-base-200 shadow-md">
					<div class="card-body">
						<div class="flex flex-col justify-between gap-4 md:flex-row">
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2 flex-wrap mb-1">
									<h3 class="text-xl font-bold">{mission.name}</h3>
									<div class="badge badge-sm">{displayStatus(mission.status)}</div>
									{#if mission.tier}
										<div class="badge badge-outline badge-sm">{mission.tier}</div>
									{/if}
									{#if mission.region}
										<span class="text-xs opacity-50">📍 {mission.region}</span>
									{/if}
								</div>
								{#if mission.rewards[0]?.xp}
									<div class="text-xs opacity-60 mb-2">⚡ {mission.rewards[0].xp} Essence net payout</div>
								{/if}
								<div class="text-sm opacity-70">
									<MarkdownRenderer content={mission.description || 'No briefing.'} />
								</div>
							</div>

							<div class="flex min-w-[200px] flex-col gap-2">
								{#if mission.status === 'Available'}
									<button
										class="btn btn-outline btn-sm"
										on:click={() => patchStatus(mission.id, 'In Progress')}>Mark Underway</button>
								{:else if mission.status === 'In Progress'}
									<button
										class="btn btn-outline btn-sm btn-success"
										on:click={() => patchStatus(mission.id, 'Completed')}>Mark Completed</button>
								{/if}
								<button
									class="btn btn-outline btn-sm btn-primary"
									on:click={() => openEdit(mission)}>Edit</button>
								<button
									class="btn btn-ghost btn-sm text-error"
									on:click={() => patchStatus(mission.id, 'Cancelled')}>Retire</button>
							</div>
						</div>

						{#if mission.players.length > 0}
							<div class="mt-4 border-t border-base-content/10 pt-4">
								<span class="mb-2 block text-[10px] font-bold uppercase opacity-50">Crew Enrolled</span>
								<div class="flex flex-wrap gap-2">
									{#each mission.players as p}
										<div class="badge badge-outline badge-md">{p.name}</div>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				</div>
			{/each}
			{#if missions.length === 0}
				<div class="py-12 text-center opacity-50">
					The board is empty. Post the first job above.
				</div>
			{/if}
		</div>
	{/if}
</div>

<Modal
	show={showCreateMission}
	title={editingMissionId ? 'Edit Mission' : 'Post to Mission Board'}
	onClose={() => (showCreateMission = false)}
>
	<div class="form-control gap-4">
		<!-- Title + Tier -->
		<div class="grid grid-cols-2 gap-4">
			<div class="form-control">
				<label class="label"><span class="label-text">Job Title</span></label>
				<input type="text" bind:value={mName} class="input-bordered input w-full" placeholder="e.g. Last Transmission" />
			</div>
			<div class="form-control">
				<label class="label"><span class="label-text">Tier</span></label>
				<select bind:value={mTier} class="select-bordered select w-full" on:change={applyPayout}>
					<option value="">— Select Tier —</option>
					<option value="Tier 1">Tier 1 (Level 1–4)</option>
					<option value="Tier 2">Tier 2 (Level 5–10)</option>
					<option value="Tier 3">Tier 3 (Level 11–16)</option>
					<option value="Tier 4">Tier 4 (Level 17–20)</option>
				</select>
			</div>
		</div>

		<!-- Difficulty + Payout -->
		<div class="grid grid-cols-2 gap-4">
			<div class="form-control">
				<label class="label"><span class="label-text">Difficulty</span></label>
				<select bind:value={mDifficulty} class="select-bordered select w-full" on:change={applyPayout}>
					<option value="Routine">Routine (below party level)</option>
					<option value="Standard">Standard (at party level)</option>
					<option value="Hard">Hard (above party level)</option>
					<option value="Extreme">Extreme</option>
				</select>
			</div>
			<div class="form-control">
				<label class="label">
					<span class="label-text">⚡ Essence Payout (net)</span>
					{#if suggestedPayout !== null && suggestedPayout !== mEssencePayout}
						<button class="label-text-alt text-primary text-xs cursor-pointer underline" on:click={applyPayout}>
							Use suggested ({suggestedPayout})
						</button>
					{/if}
				</label>
				<input type="number" bind:value={mEssencePayout} min="0" class="input-bordered input w-full" />
				<p class="text-xs opacity-50 mt-1">Net Essence to Meridian's reserves after transit deduction.</p>
			</div>
		</div>

		<!-- Region + Item reward -->
		<div class="grid grid-cols-2 gap-4">
			<div class="form-control">
				<label class="label"><span class="label-text">Region / Location</span></label>
				<input type="text" bind:value={mRegion} class="input-bordered input w-full" placeholder="e.g. Contested Band" />
			</div>
			<div class="form-control">
				<label class="label"><span class="label-text">Item Reward (optional)</span></label>
				<select bind:value={mItemRewardId} class="select-bordered select w-full">
					<option value={undefined}>No item reward</option>
					{#each availableItems as it}
						<option value={it.id}>{it.name}</option>
					{/each}
				</select>
			</div>
		</div>

		<!-- Status (edit only) + Discoverable -->
		{#if editingMissionId}
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="label"><span class="label-text">Status</span></label>
					<select bind:value={mStatus} class="select-bordered select w-full">
						<option value="Available">On the Board</option>
						<option value="In Progress">Underway</option>
						<option value="Completed">Completed</option>
						<option value="Cancelled">Cancelled</option>
					</select>
				</div>
				<div class="mt-8 flex items-center gap-4 px-2">
					<label class="label cursor-pointer gap-2">
						<span class="label-text">Retired</span>
						<input type="checkbox" bind:checked={mIsRetired} class="checkbox checkbox-error" />
					</label>
					<label class="label cursor-pointer gap-2">
						<span class="label-text">Visible</span>
						<input type="checkbox" bind:checked={mIsDiscoverable} class="checkbox checkbox-primary" />
					</label>
				</div>
			</div>
		{:else}
			<label class="label cursor-pointer gap-2 w-fit">
				<input type="checkbox" bind:checked={mIsDiscoverable} class="checkbox checkbox-primary" />
				<span class="label-text">Post visibly to the board</span>
			</label>
		{/if}

		<!-- Briefing -->
		<div>
			<div class="mb-2 flex items-center justify-between">
				<div class="flex items-center gap-4">
					<label class="label"><span class="label-text">Briefing</span></label>
					<div class="tabs-boxed tabs tabs-xs">
						<button type="button" class="tab {mDescriptionTab === 'write' ? 'tab-active' : ''}" on:click={() => (mDescriptionTab = 'write')}>Write</button>
						<button type="button" class="tab {mDescriptionTab === 'preview' ? 'tab-active' : ''}" on:click={() => (mDescriptionTab = 'preview')}>Preview</button>
					</div>
				</div>
				<button type="button" class="btn btn-ghost btn-xs" on:click={() => (showOneshotGenerator = !showOneshotGenerator)}>
					{showOneshotGenerator ? '✕ Close' : '🎲 AI Generator'}
				</button>
			</div>
			{#if mDescriptionTab === 'write'}
				<textarea bind:value={mDescription} class="textarea-bordered textarea h-32 w-full font-mono text-sm" placeholder="The question the crew is going to answer this session..."></textarea>
			{:else}
				<div class="min-h-32 rounded-lg border border-base-content/10 bg-base-300/30 p-4">
					<MarkdownRenderer content={mDescription || '*No content to preview*'} />
				</div>
			{/if}
		</div>

		{#if showOneshotGenerator}
			<OneshotGenerator missionTier={mTier} missionRegion={mRegion} onOneshotGenerated={handleOneshotGenerated} />
		{/if}

		{#if mOneshotId}
			<div class="alert text-xs alert-info">
				<span>✅ AI-generated adventure linked (ID: {mOneshotId})</span>
			</div>
		{/if}

		<!-- Advanced (collapsed) -->
		<div class="collapse collapse-arrow border border-base-content/10 rounded-lg">
			<input type="checkbox" bind:checked={showAdvanced} />
			<div class="collapse-title text-sm font-medium">Advanced</div>
			<div class="collapse-content form-control gap-3">
				<div class="form-control">
					<label class="label">
						<span class="label-text">Re-run cooldown (days)</span>
						<span class="label-text-alt opacity-50">Days before this hex can run again</span>
					</label>
					<input type="number" bind:value={mCooldown} min="0" class="input-bordered input input-sm w-full" />
				</div>
				<div class="form-control">
					<label class="label"><span class="label-text">Prerequisite mission</span></label>
					<select bind:value={mPrerequisiteId} class="select-bordered select select-sm w-full">
						<option value={undefined}>None</option>
						{#each missions.filter(m => m.id !== editingMissionId) as m}
							<option value={m.id}>{m.name}</option>
						{/each}
					</select>
				</div>
			</div>
		</div>
	</div>

	<div slot="action">
		<button class="btn w-full btn-primary" on:click={saveMission}>
			{editingMissionId ? 'Update Mission' : 'Post to Board'}
		</button>
	</div>
</Modal>
