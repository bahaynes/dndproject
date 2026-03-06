<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { get } from 'svelte/store';
	import { API_BASE_URL } from '$lib/config';
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

	// Mission Design
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
	let mRewards: { item_id?: number; xp: number; scrip: number }[] = [];
	let mOneshotId: number | null = null;
	let showOneshotGenerator = false;

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
		mRewards = [];
		mOneshotId = null;
		showOneshotGenerator = false;
		mDescriptionTab = 'write';
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
		mRewards = mission.rewards.map((r) => ({
			item_id: r.item_id,
			xp: r.xp || 0,
			scrip: r.scrip || 0
		}));
		mOneshotId = (mission as any).oneshot_id || null;
		showOneshotGenerator = false;
		mDescriptionTab = 'write';
		showCreateMission = true;
	}

	onMount(async () => {
		const authState = get(auth);
		if (!authState.isAuthenticated || authState.user?.role !== 'admin') {
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
		const res = await fetch(`${API_BASE_URL}/missions/`, {
			headers: { Authorization: `Bearer ${get(auth).token}` }
		});
		if (res.ok) missions = await res.json();
	}

	async function fetchItems() {
		const res = await fetch(`${API_BASE_URL}/items/`, {
			headers: { Authorization: `Bearer ${get(auth).token}` }
		});
		if (res.ok) availableItems = await res.json();
	}

	async function saveMission() {
		try {
			const url = editingMissionId
				? `${API_BASE_URL}/missions/${editingMissionId}`
				: `${API_BASE_URL}/missions/`;

			const method = editingMissionId ? 'PUT' : 'POST';

			const res = await fetch(url, {
				method: method,
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${get(auth).token}`
				},
				body: JSON.stringify({
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
					rewards: mRewards.map((r) => ({
						item_id: r.item_id || null,
						xp: r.xp,
						scrip: r.scrip
					}))
				})
			});

			if (res.ok) {
				success = editingMissionId ? 'Mission updated.' : 'Mission posted.';
				showCreateMission = false;
				await fetchMissions();
			}
		} catch (e) {
			error = 'Failed to save mission.';
		}
	}

	async function patchStatus(id: number, status: string) {
		try {
			const res = await fetch(`${API_BASE_URL}/missions/${id}/status?status=${status}`, {
				method: 'PUT',
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) await fetchMissions();
		} catch (e) {}
	}

	async function distributeRewards(id: number) {
		try {
			const res = await fetch(`${API_BASE_URL}/missions/${id}/distribute_rewards`, {
				method: 'POST',
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) {
				success = 'Rewards distributed to all participants.';
				await fetchMissions();
			} else {
				const d = await res.json();
				error = d.detail || 'Failed to distribute rewards.';
			}
		} catch (e) {}
	}

	function addRewardRow() {
		mRewards = [...mRewards, { xp: 0, scrip: 0 }];
	}

	function handleOneshotGenerated(oneshotId: number, description: string) {
		mOneshotId = oneshotId;
		if (!mDescription) {
			mDescription = description.substring(0, 500) + '...';
		}
		success = 'One-shot adventure generated successfully!';
		showOneshotGenerator = false;
	}
</script>

<div class="container mx-auto max-w-6xl p-4">
	<div class="mb-8 flex items-center justify-between">
		<h1 class="text-4xl font-[var(--font-cinzel)] font-bold text-primary">Mission Management</h1>
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
							<div>
								<h3 class="text-xl font-bold">{mission.name}</h3>
								<div class="mt-1 flex items-center gap-2">
									<div class="badge badge-sm">{mission.status}</div>
									<span class="text-xs opacity-50">{mission.players.length} Heroes Enrolled</span>
								</div>
								<div class="mt-4 text-sm opacity-70">
									<MarkdownRenderer content={mission.description || 'No description.'} />
								</div>
							</div>

							<div class="flex min-w-[200px] flex-col gap-2">
								{#if mission.status === 'Available'}
									<button
										class="btn btn-outline btn-sm"
										on:click={() => patchStatus(mission.id, 'In Progress')}>Mark In-Progress</button
									>
								{:else if mission.status === 'In Progress'}
									<button
										class="btn btn-outline btn-sm btn-success"
										on:click={() => patchStatus(mission.id, 'Completed')}>Mark Completed</button
									>
								{:else if mission.status === 'Completed'}
									<button
										class="btn btn-sm btn-secondary"
										on:click={() => distributeRewards(mission.id)}>Distribute Rewards</button
									>
								{/if}
								<button
									class="btn btn-outline btn-sm btn-primary"
									on:click={() => openEdit(mission)}>Edit Mission</button
								>
								<button class="btn text-error btn-ghost btn-sm">Delete Mission</button>
							</div>
						</div>

						<!-- Participants list -->
						{#if mission.players.length > 0}
							<div class="mt-4 border-t border-base-content/10 pt-4">
								<span class="mb-2 block text-[10px] font-bold uppercase opacity-50"
									>Heroes Enrolled</span
								>
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
					No missions found. Create your first one above.
				</div>
			{/if}
		</div>
	{/if}
</div>

<Modal
	show={showCreateMission}
	title={editingMissionId ? 'Edit Mission' : 'Draft New Mission'}
	onClose={() => (showCreateMission = false)}
>
	<div class="form-control gap-4">
		<div class="grid grid-cols-2 gap-4">
			<div class="form-control">
				<label class="label"><span class="label-text">Mission Title</span></label>
				<input type="text" bind:value={mName} class="input-bordered input w-full" />
			</div>
			<div class="form-control">
				<label class="label"><span class="label-text">Tier</span></label>
				<select bind:value={mTier} class="select-bordered select w-full">
					<option value="">No Tier</option>
					<option value="Tier 1">Tier 1 (Lvl 1-4)</option>
					<option value="Tier 2">Tier 2 (Lvl 5-10)</option>
					<option value="Tier 3">Tier 3 (Lvl 11-16)</option>
					<option value="Tier 4">Tier 4 (Lvl 17-20)</option>
				</select>
			</div>
		</div>
		<div class="grid grid-cols-2 gap-4">
			<div class="form-control">
				<label class="label"><span class="label-text">Region / Location</span></label>
				<input
					type="text"
					bind:value={mRegion}
					class="input-bordered input w-full"
					placeholder="e.g. Northlands"
				/>
			</div>
			<div class="form-control">
				<label class="label"><span class="label-text">Cooldown (Days)</span></label>
				<input type="number" bind:value={mCooldown} class="input-bordered input w-full" />
			</div>
		</div>
		{#if editingMissionId}
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="label"><span class="label-text">Mission Status</span></label>
					<select bind:value={mStatus} class="select-bordered select w-full">
						<option value="Available">Available</option>
						<option value="In Progress">In Progress</option>
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
						<span class="label-text">Discoverable</span>
						<input
							type="checkbox"
							bind:checked={mIsDiscoverable}
							class="checkbox checkbox-primary"
						/>
					</label>
				</div>
			</div>
		{:else}
			<div class="flex items-center gap-4 px-2">
				<label class="label cursor-pointer gap-2">
					<span class="label-text">Discoverable</span>
					<input type="checkbox" bind:checked={mIsDiscoverable} class="checkbox checkbox-primary" />
				</label>
			</div>
		{/if}
		<div>
			<div class="mb-2 flex items-center justify-between">
				<div class="flex items-center gap-4">
					<label class="label"><span class="label-text">Briefing / Description</span></label>
					<div class="tabs-boxed tabs tabs-xs">
						<button
							type="button"
							class="tab {mDescriptionTab === 'write' ? 'tab-active' : ''}"
							on:click={() => (mDescriptionTab = 'write')}>Write</button
						>
						<button
							type="button"
							class="tab {mDescriptionTab === 'preview' ? 'tab-active' : ''}"
							on:click={() => (mDescriptionTab = 'preview')}>Preview</button
						>
					</div>
				</div>
				<button
					type="button"
					class="btn btn-ghost btn-xs"
					on:click={() => (showOneshotGenerator = !showOneshotGenerator)}
				>
					{showOneshotGenerator ? '✕ Close' : '🎲 AI Generator'}
				</button>
			</div>
			{#if mDescriptionTab === 'write'}
				<textarea
					bind:value={mDescription}
					class="textarea-bordered textarea h-32 w-full font-mono text-sm"
					placeholder="Describe the objective, threats, and flavor..."
				></textarea>
			{:else}
				<div class="min-h-32 rounded-lg border border-base-content/10 bg-base-300/30 p-4">
					<MarkdownRenderer content={mDescription || '*No content to preview*'} />
				</div>
			{/if}
		</div>

		{#if showOneshotGenerator}
			<OneshotGenerator
				missionTier={mTier}
				missionRegion={mRegion}
				onOneshotGenerated={handleOneshotGenerated}
			/>
		{/if}

		{#if mOneshotId}
			<div class="alert text-xs alert-info">
				<span>✅ AI-generated adventure linked (ID: {mOneshotId})</span>
			</div>
		{/if}

		<div>
			<div class="mb-2 flex items-center justify-between">
				<label class="label"><span class="label-text font-bold">Rewards</span></label>
				<button class="btn btn-ghost btn-xs" on:click={addRewardRow}>+ Add Reward Row</button>
			</div>

			{#each mRewards as reward, i}
				<div class="b-base-200 mb-2 flex items-end gap-2 rounded border p-2">
					<div class="flex-grow">
						<label class="label p-1"><span class="text-[10px]">XP</span></label>
						<input
							type="number"
							bind:value={reward.xp}
							class="input-bordered input input-xs w-full"
						/>
					</div>
					<div class="flex-grow">
						<label class="label p-1"><span class="text-[10px]">Scrip</span></label>
						<input
							type="number"
							bind:value={reward.scrip}
							class="input-bordered input input-xs w-full"
						/>
					</div>
					<div class="flex-grow">
						<label class="label p-1"><span class="text-[10px]">Item</span></label>
						<select bind:value={reward.item_id} class="select-bordered select w-full select-xs">
							<option value={undefined}>No Item</option>
							{#each availableItems as it}
								<option value={it.id}>{it.name}</option>
							{/each}
						</select>
					</div>
					<button
						class="btn btn-circle text-error btn-ghost btn-xs"
						on:click={() => (mRewards = mRewards.filter((_, idx) => idx !== i))}>×</button
					>
				</div>
			{/each}
		</div>
	</div>
	<div slot="action">
		<button class="btn w-full btn-primary" on:click={saveMission}
			>{editingMissionId ? 'Update Mission' : 'Post to Board'}</button
		>
	</div>
</Modal>
