<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import { parseUtcDate } from '$lib/date';
	import type { Mission, Item } from '$lib/types';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import OneshotGenerator from '$lib/components/OneshotGenerator.svelte';
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
	import RewardCard from '$lib/components/RewardCard.svelte';

	let missions: Mission[] = [];
	let availableItems: Item[] = [];
	let loading = true;
	let error = '';
	let success = '';
	let showArchived = false;

	// Admin: Create / Edit mission modal
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
	let mEssencePayout = 4;
	let mDifficulty = 'Standard';
	let mItemRewardId: number | undefined = undefined;

	const PAYOUTS: Record<string, Record<string, number>> = {
		'Tier 1': { Routine: 2, Standard: 4, Hard: 6, Extreme: 10 },
		'Tier 2': { Routine: 4, Standard: 8, Hard: 12, Extreme: 20 },
		'Tier 3': { Routine: 6, Standard: 12, Hard: 18, Extreme: 30 },
		'Tier 4': { Routine: 8, Standard: 16, Hard: 24, Extreme: 40 }
	};

	const STATUS_LABELS: Record<string, string> = {
		Available: 'On the Board',
		'In Progress': 'Underway',
		Completed: 'Completed',
		Cancelled: 'Cancelled'
	};

	$: myCharacterId = $auth.user?.active_character?.id;
	$: isAdmin = $auth.user?.role === 'admin';
	$: suggestedPayout = (mTier && PAYOUTS[mTier]?.[mDifficulty]) ?? null;

	$: activeMissions = missions.filter(
		(m) => !m.is_retired && m.status !== 'Completed' && m.status !== 'Cancelled'
	);
	$: archivedMissions = missions.filter(
		(m) => m.is_retired || m.status === 'Completed' || m.status === 'Cancelled'
	);

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		loading = true;
		error = '';
		try {
			const [m, items] = await Promise.all([
				api('GET', '/missions/'),
				api('GET', '/items/').catch(() => [])
			]);
			missions = m ?? [];
			availableItems = items ?? [];
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load missions.';
		} finally {
			loading = false;
		}
	}

	async function fetchMissions() {
		error = '';
		try {
			missions = await api('GET', '/missions/');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load missions.';
		}
	}

	function displayStatus(s: string) {
		return STATUS_LABELS[s] ?? s;
	}

	function inCooldown(m: Mission): boolean {
		if (!m.last_run_date) return false;
		return Date.now() - parseUtcDate(m.last_run_date).getTime() < m.cooldown_days * 86400000;
	}

	function isUserInMission(mission: Mission) {
		if (!myCharacterId) return false;
		return mission.players.some((p) => p.id === myCharacterId);
	}

	async function handleSignup(missionId: number) {
		error = '';
		try {
			await api('POST', `/missions/${missionId}/signup`);
			await fetchMissions();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to sign up for mission.';
		}
	}

	// --- Admin actions ---
	function applyPayout() {
		if (suggestedPayout !== null) mEssencePayout = suggestedPayout as number;
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
		mEssencePayout = 4;
		mItemRewardId = mission.rewards.find((r) => r.item_id)?.item_id;
		mOneshotId = (mission as any).oneshot_id || null;
		showOneshotGenerator = false;
		mDescriptionTab = 'write';
		showAdvanced = false;
		mDifficulty = 'Standard';
		showCreateMission = true;
	}

	async function saveMission() {
		error = '';
		success = '';
		try {
			const rewards = [{ is_hidden: false, item_id: mItemRewardId || null }];
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
			error = e instanceof Error ? e.message : 'Failed to save mission.';
		}
	}

	async function patchStatus(id: number, status: string) {
		error = '';
		try {
			await api('PUT', `/missions/${id}/status?status=${status}`);
			await fetchMissions();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to update mission status.';
		}
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

<div class="container mx-auto max-w-6xl space-y-8 p-4 py-8">
	<div class="flex flex-wrap items-center justify-between gap-4 border-b border-base-content/10 pb-4">
		<div>
			<h1 class="text-4xl font-[var(--font-cinzel)] font-bold text-primary">Mission Board</h1>
			<p class="mt-1 text-sm text-base-content/65">
				Browse active contracts, inspect rewards, and sign up with your crew.
			</p>
		</div>
		<div class="flex items-center gap-2">
			{#if isAdmin}
				<button class="btn btn-primary" on:click={openCreate}>+ New Mission</button>
			{/if}
			<button class="btn btn-ghost btn-sm" on:click={fetchMissions}>Refresh</button>
		</div>
	</div>

	{#if success}
		<div class="alert alert-success">{success}</div>
	{/if}

	{#if error}
		<div class="alert alert-error shadow-lg">
			<span>{error}</span>
		</div>
	{/if}

	{#if loading}
		<div class="flex justify-center py-16">
			<LoadingSpinner size="lg" />
		</div>
	{:else if missions.length === 0}
		<div class="card border border-base-content/10 bg-base-200/40 p-12 text-center">
			<h2 class="text-xl font-bold">The board is currently empty.</h2>
			<p class="mt-1 text-sm text-base-content/65">
				Check back later for new adventurous opportunities from the guild.
			</p>
			{#if isAdmin}
				<div class="mt-4">
					<button class="btn btn-sm btn-primary" on:click={openCreate}>+ Post First Mission</button>
				</div>
			{/if}
		</div>
	{:else}
		<!-- Active Missions -->
		<section class="space-y-4">
			<h2 class="text-xl font-[var(--font-cinzel)] font-bold text-primary">
				Active Contracts ({activeMissions.length})
			</h2>
			{#if activeMissions.length === 0}
				<p class="text-sm text-base-content/60 italic">No active contracts on the board.</p>
			{:else}
				<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
					{#each activeMissions as mission}
						<div
							class="card flex h-full flex-col border border-base-content/10 bg-base-100 shadow-lg {inCooldown(
								mission
							)
								? 'opacity-75'
								: ''}"
						>
							<div class="card-body p-5">
								<div class="mb-2 flex items-start justify-between gap-2">
									<h3 class="card-title font-[var(--font-cinzel)]">{mission.name}</h3>
									<div
										class="badge shrink-0 badge-sm {mission.status === 'Available'
											? 'badge-success'
											: 'badge-warning'}"
									>
										{displayStatus(mission.status)}
									</div>
								</div>

								<div class="mb-3 flex flex-wrap gap-1.5">
									{#if mission.tier}
										<span class="badge badge-outline badge-xs">{mission.tier}</span>
									{/if}
									{#if mission.region}
										<span class="badge badge-ghost badge-xs">📍 {mission.region}</span>
									{/if}
									{#if inCooldown(mission)}
										<span class="badge badge-warning badge-xs">❄️ Cooldown</span>
									{/if}
									{#if !mission.is_discoverable}
										<span class="badge badge-ghost badge-xs">Hidden</span>
									{/if}
								</div>

								<div class="mb-4 line-clamp-3 text-sm text-base-content/80">
									<MarkdownRenderer content={mission.description || 'No mission brief available.'} />
								</div>

								{#if mission.rewards.length > 0}
									<div class="mb-4 rounded-lg bg-base-200 p-3">
										<span class="mb-2 block text-[10px] font-bold text-base-content/60 uppercase"
											>Potential Rewards</span
										>
										<div class="flex flex-wrap gap-2">
											{#each mission.rewards as reward}
												<RewardCard
													{reward}
													interactive={mission.status === 'Completed'}
													isRevealed={!reward.is_hidden}
												/>
											{/each}
										</div>
									</div>
								{/if}

								<div class="mt-auto space-y-3">
									<div class="flex items-center gap-2">
										<div class="avatar-group -space-x-3 rtl:space-x-reverse">
											{#each mission.players.slice(0, 3) as player}
												<div class="placeholder avatar border-base-100">
													<div
														class="w-6 rounded-full bg-primary text-[8px] font-bold text-primary-content"
													>
														{player.name.charAt(0)}
													</div>
												</div>
											{/each}
											{#if mission.players.length > 3}
												<div class="placeholder avatar border-base-100">
													<div
														class="w-6 rounded-full bg-neutral text-[8px] font-bold text-neutral-content"
													>
														+{mission.players.length - 3}
													</div>
												</div>
											{/if}
										</div>
										<span class="text-xs text-base-content/65">
											{mission.players.length === 0
												? 'Seeking members'
												: `${mission.players.length} members signed up`}
										</span>
									</div>

									<div class="card-actions">
										{#if isUserInMission(mission)}
											<button class="btn btn-disabled w-full btn-sm">✓ Signed Up</button>
										{:else if mission.status === 'Available'}
											<button
												class="btn w-full btn-sm btn-primary"
												on:click={() => handleSignup(mission.id)}
												disabled={!myCharacterId}
											>
												{!myCharacterId ? 'Create Character to Sign Up' : 'Sign Up'}
											</button>
										{:else}
											<button class="btn btn-disabled w-full btn-sm"
												>Mission {displayStatus(mission.status)}</button
											>
										{/if}
									</div>

									{#if isAdmin}
										<div
											class="flex flex-wrap justify-end gap-1.5 border-t border-base-content/10 pt-3"
										>
											{#if mission.status === 'Available'}
												<button
													class="btn btn-outline btn-xs"
													on:click={() => patchStatus(mission.id, 'In Progress')}
													>Mark Underway</button
												>
											{:else if mission.status === 'In Progress'}
												<button
													class="btn btn-outline btn-xs btn-success"
													on:click={() => patchStatus(mission.id, 'Completed')}
													>Mark Completed</button
												>
											{/if}
											<button class="btn btn-ghost btn-xs" on:click={() => openEdit(mission)}
												>Edit</button
											>
											<button
												class="btn btn-ghost btn-xs text-error"
												on:click={() => patchStatus(mission.id, 'Cancelled')}>Retire</button
											>
										</div>
									{/if}
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</section>

		<!-- Archived / Completed / Cancelled -->
		{#if archivedMissions.length > 0}
			<section class="space-y-4">
				<button
					class="btn btn-ghost btn-sm text-base-content/70"
					on:click={() => (showArchived = !showArchived)}
				>
					{showArchived ? '▾' : '▸'} Completed &amp; Retired ({archivedMissions.length})
				</button>
				{#if showArchived}
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
						{#each archivedMissions as mission}
							<div class="card border border-base-content/10 bg-base-100/80 shadow">
								<div class="card-body p-5">
									<div class="mb-2 flex items-start justify-between gap-2">
										<h3 class="card-title font-[var(--font-cinzel)]">{mission.name}</h3>
										<span class="badge badge-neutral badge-sm">{displayStatus(mission.status)}</span>
									</div>
									<div class="line-clamp-3 text-sm text-base-content/70">
										<MarkdownRenderer content={mission.description || 'No mission brief.'} />
									</div>
									{#if isAdmin}
										<div class="mt-3 flex justify-end gap-2 border-t border-base-content/10 pt-3">
											<button class="btn btn-ghost btn-xs" on:click={() => openEdit(mission)}
												>Edit</button
											>
										</div>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</section>
		{/if}
	{/if}
</div>

<!-- Admin: Create / Edit Mission Modal -->
<Modal
	show={showCreateMission}
	title={editingMissionId ? 'Edit Mission' : 'Post to Mission Board'}
	onClose={() => (showCreateMission = false)}
>
	<div class="form-control gap-4">
		<div class="grid grid-cols-2 gap-4">
			<div class="form-control">
				<label class="label" for="m-name"><span class="label-text">Job Title</span></label>
				<input
					id="m-name"
					type="text"
					bind:value={mName}
					class="input-bordered input w-full"
					placeholder="e.g. Last Transmission"
				/>
			</div>
			<div class="form-control">
				<label class="label" for="m-tier"><span class="label-text">Tier</span></label>
				<select
					id="m-tier"
					bind:value={mTier}
					class="select-bordered select w-full"
					on:change={applyPayout}
				>
					<option value="">— Select Tier —</option>
					<option value="Tier 1">Tier 1 (Level 1–4)</option>
					<option value="Tier 2">Tier 2 (Level 5–10)</option>
					<option value="Tier 3">Tier 3 (Level 11–16)</option>
					<option value="Tier 4">Tier 4 (Level 17–20)</option>
				</select>
			</div>
		</div>

		<div class="grid grid-cols-2 gap-4">
			<div class="form-control">
				<label class="label" for="m-diff"><span class="label-text">Difficulty</span></label>
				<select
					id="m-diff"
					bind:value={mDifficulty}
					class="select-bordered select w-full"
					on:change={applyPayout}
				>
					<option value="Routine">Routine (below party level)</option>
					<option value="Standard">Standard (at party level)</option>
					<option value="Hard">Hard (above party level)</option>
					<option value="Extreme">Extreme</option>
				</select>
			</div>
			<div class="form-control">
				<label class="label" for="m-payout">
					<span class="label-text">⚡ Essence Payout (net)</span>
					{#if suggestedPayout !== null && suggestedPayout !== mEssencePayout}
						<button
							type="button"
							class="label-text-alt cursor-pointer text-xs text-primary underline"
							on:click={applyPayout}
						>
							Use suggested ({suggestedPayout})
						</button>
					{/if}
				</label>
				<input
					id="m-payout"
					type="number"
					bind:value={mEssencePayout}
					min="0"
					class="input-bordered input w-full"
				/>
			</div>
		</div>

		<div class="grid grid-cols-2 gap-4">
			<div class="form-control">
				<label class="label" for="m-region"><span class="label-text">Region / Location</span></label>
				<input
					id="m-region"
					type="text"
					bind:value={mRegion}
					class="input-bordered input w-full"
					placeholder="e.g. Contested Band"
				/>
			</div>
			<div class="form-control">
				<label class="label" for="m-item"
					><span class="label-text">Item Reward (optional)</span></label
				>
				<select id="m-item" bind:value={mItemRewardId} class="select-bordered select w-full">
					<option value={undefined}>No item reward</option>
					{#each availableItems as it}
						<option value={it.id}>{it.name}</option>
					{/each}
				</select>
			</div>
		</div>

		{#if editingMissionId}
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="label" for="m-status"><span class="label-text">Status</span></label>
					<select id="m-status" bind:value={mStatus} class="select-bordered select w-full">
						<option value="Available">On the Board</option>
						<option value="In Progress">Underway</option>
						<option value="Completed">Completed</option>
						<option value="Cancelled">Cancelled</option>
					</select>
				</div>
				<div class="mt-8 flex items-center gap-4 px-2">
					<label class="label cursor-pointer gap-2">
						<span class="label-text">Retired</span>
						<input type="checkbox" bind:checked={mIsRetired} class="checkbox checkbox-warning" />
					</label>
					<label class="label cursor-pointer gap-2">
						<span class="label-text">Visible</span>
						<input
							type="checkbox"
							bind:checked={mIsDiscoverable}
							class="checkbox checkbox-primary"
						/>
					</label>
				</div>
			</div>
		{:else}
			<label class="label w-fit cursor-pointer gap-2">
				<input type="checkbox" bind:checked={mIsDiscoverable} class="checkbox checkbox-primary" />
				<span class="label-text">Post visibly to the board</span>
			</label>
		{/if}

		<div>
			<div class="mb-2 flex items-center justify-between">
				<div class="flex items-center gap-4">
					<span class="label-text">Briefing</span>
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
					placeholder="The question the crew is going to answer this session..."
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

		<div class="collapse-arrow collapse rounded-lg border border-base-content/10">
			<input type="checkbox" bind:checked={showAdvanced} />
			<div class="collapse-title text-sm font-medium">Advanced</div>
			<div class="form-control collapse-content gap-3">
				<div class="form-control">
					<label class="label" for="m-cooldown">
						<span class="label-text">Re-run cooldown (days)</span>
						<span class="label-text-alt text-base-content/60"
							>Days before this hex can run again</span
						>
					</label>
					<input
						id="m-cooldown"
						type="number"
						bind:value={mCooldown}
						min="0"
						class="input-bordered input input-sm w-full"
					/>
				</div>
				<div class="form-control">
					<label class="label" for="m-prereq"
						><span class="label-text">Prerequisite mission</span></label
					>
					<select
						id="m-prereq"
						bind:value={mPrerequisiteId}
						class="select-bordered select w-full select-sm"
					>
						<option value={undefined}>None</option>
						{#each missions.filter((m) => m.id !== editingMissionId) as m}
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
