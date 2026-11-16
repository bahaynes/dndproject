<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { Mission, Item } from '$lib/types';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Modal from '$lib/components/Modal.svelte';
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
	let mTier = 'Tier 1';
	let mRegion = '';
	let mCooldown = 7;
	let mIsRetired = false;
	let mIsDiscoverable = true;
	let mPrerequisiteId: number | undefined = undefined;
	let showAdvanced = false;

	// D&D 5e Reward state
	let mGold = 50;
	let mXp = 300;
	let mItemRewardId: number | undefined = undefined;

	// Client-side LLM Prompt Helper
	let showPromptHelper = false;
	let llmTheme = '';
	let llmPasteText = '';
	let copyFeedback = '';
	let parseError = '';

	const TIER_PRESETS: Record<string, { gold: number; xp: number; label: string }> = {
		'Tier 1': { gold: 50, xp: 300, label: 'Levels 1–4' },
		'Tier 2': { gold: 250, xp: 1500, label: 'Levels 5–10' },
		'Tier 3': { gold: 1000, xp: 5000, label: 'Levels 11–16' },
		'Tier 4': { gold: 5000, xp: 15000, label: 'Levels 17–20' }
	};

	function applyTierPreset() {
		const preset = TIER_PRESETS[mTier];
		if (preset) {
			mGold = preset.gold;
			mXp = preset.xp;
		}
	}

	function buildPrompt(): string {
		const tierLabel = mTier ? `${mTier} (${TIER_PRESETS[mTier]?.label ?? 'D&D 5e'})` : 'Tier 1 (Levels 1-4)';
		return [
			`Design a D&D 5e West Marches one-shot quest for ${tierLabel}.`,
			mRegion ? `Region / Setting: ${mRegion}.` : 'Region / Setting: Frontier wilderness.',
			llmTheme ? `Premise / Theme: ${llmTheme}.` : '',
			'',
			'Return ONLY a valid JSON object with these exact keys:',
			'{',
			'  "name": "Short evocative quest title",',
			'  "description": "Markdown briefing (2-3 paragraphs: hook, objective, known hazards)",',
			`  "tier": "${mTier || 'Tier 1'}",`,
			`  "region": "${mRegion || 'Borderlands'}",`,
			`  "gold": ${mGold},`,
			`  "xp": ${mXp}`,
			'}'
		]
			.filter(Boolean)
			.join('\n');
	}

	async function copyPrompt() {
		try {
			await navigator.clipboard.writeText(buildPrompt());
			copyFeedback = 'Copied prompt to clipboard. Paste into ChatGPT, Claude, or Gemini.';
			setTimeout(() => (copyFeedback = ''), 4000);
		} catch {
			copyFeedback = 'Clipboard unavailable — copy the prompt manually.';
		}
	}

	function parseLlmResponse() {
		parseError = '';
		const raw = llmPasteText.trim();
		if (!raw) return;

		try {
			// Strip optional ```json ... ``` fences
			const fenceMatch = raw.match(/```(?:json)?\s*([\s\S]*?)```/i);
			const jsonText = fenceMatch ? fenceMatch[1].trim() : raw;
			const parsed = JSON.parse(jsonText);

			if (parsed.name) mName = String(parsed.name);
			if (parsed.description) mDescription = String(parsed.description);
			if (parsed.tier) mTier = String(parsed.tier);
			if (parsed.region) mRegion = String(parsed.region);
			if (typeof parsed.gold === 'number') mGold = parsed.gold;
			if (typeof parsed.xp === 'number') mXp = parsed.xp;

			showPromptHelper = false;
			llmPasteText = '';
		} catch {
			parseError = 'Could not parse JSON. Ensure the LLM returned a valid JSON object.';
		}
	}

	function openCreate() {
		editingMissionId = null;
		mName = '';
		mDescription = '';
		mStatus = 'Available';
		mTier = 'Tier 1';
		mRegion = '';
		mCooldown = 7;
		mIsRetired = false;
		mIsDiscoverable = true;
		mPrerequisiteId = undefined;
		showPromptHelper = false;
		mDescriptionTab = 'write';
		showAdvanced = false;
		mGold = 50;
		mXp = 300;
		mItemRewardId = undefined;
		showCreateMission = true;
	}

	function openEdit(mission: Mission) {
		editingMissionId = mission.id;
		mName = mission.name;
		mDescription = mission.description || '';
		mStatus = mission.status;
		mTier = mission.tier || 'Tier 1';
		mRegion = mission.region || '';
		mCooldown = mission.cooldown_days;
		mIsRetired = mission.is_retired;
		mIsDiscoverable = mission.is_discoverable;
		mPrerequisiteId = mission.prerequisite_id;
		mGold = mission.rewards.reduce((sum, r) => sum + (r.gold ?? 0), 0);
		mXp = mission.rewards.reduce((sum, r) => sum + (r.xp ?? 0), 0);
		mItemRewardId = mission.rewards.find((r) => r.item_id)?.item_id;
		showPromptHelper = false;
		mDescriptionTab = 'write';
		showAdvanced = false;
		showCreateMission = true;
	}

	let dataLoaded = false;

	onMount(() => {
		if (!localStorage.getItem('accessToken')) goto('/dashboard');
	});

	$: if ($auth.isAuthenticated && $auth.user?.role === 'admin' && !dataLoaded) {
		dataLoaded = true;
		reloadData();
	}

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
		error = '';
		try {
			const rewards = [
				{
					is_hidden: false,
					gold: mGold || 0,
					xp: mXp || 0,
					item_id: mItemRewardId || null
				}
			];
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
				rewards
			};
			if (editingMissionId) {
				await api('PUT', `/missions/${editingMissionId}`, body);
			} else {
				await api('POST', '/missions/', body);
			}
			success = editingMissionId ? 'Quest updated.' : 'Quest posted to the board.';
			showCreateMission = false;
			await fetchMissions();
		} catch (e) {
			error = 'Failed to save quest.';
		}
	}

	async function patchStatus(id: number, status: string) {
		try {
			await api('PUT', `/missions/${id}/status?status=${status}`);
			await fetchMissions();
		} catch (e) {}
	}
</script>

<PageHeader
	title="Manage Missions"
	subtitle="Create quests with D&D 5e Gold & XP rewards or use the zero-cost LLM prompt helper."
>
	<button slot="actions" class="btn btn-primary btn-sm" on:click={openCreate}>
		+ New Quest
	</button>
</PageHeader>

{#if success}
	<div class="alert alert-success mb-4 text-sm">{success}</div>
{/if}
{#if error}
	<div class="alert alert-error mb-4 text-sm">{error}</div>
{/if}

{#if loading}
	<LoadingSpinner size="lg" />
{:else if missions.length === 0}
	<div class="panel p-12 text-center text-sm text-base-content/60">
		No quests created yet. Click "+ New Quest" to post one.
	</div>
{:else}
	<div class="space-y-4">
		{#each missions as mission}
			{@const gp = mission.rewards.reduce((sum, r) => sum + (r.gold ?? 0), 0)}
			{@const xp = mission.rewards.reduce((sum, r) => sum + (r.xp ?? 0), 0)}
			<div class="panel p-5">
				<div class="flex flex-col justify-between gap-4 md:flex-row">
					<div class="min-w-0 flex-1">
						<div class="mb-2 flex flex-wrap items-center gap-2">
							<h3 class="text-base font-semibold text-base-content">{mission.name}</h3>
							<span class="badge badge-sm badge-outline">{mission.status}</span>
							{#if mission.tier}
								<span class="badge badge-ghost badge-sm">{mission.tier}</span>
							{/if}
							{#if mission.region}
								<span class="text-xs text-base-content/60">{mission.region}</span>
							{/if}
							{#if gp > 0}
								<span class="rounded bg-primary/15 px-2 py-0.5 text-xs text-primary stat-num">{gp} GP</span>
							{/if}
							{#if xp > 0}
								<span class="rounded bg-secondary/15 px-2 py-0.5 text-xs text-secondary stat-num">{xp} XP</span>
							{/if}
						</div>
						<div class="prose prose-sm max-w-none text-xs text-base-content/75">
							<MarkdownRenderer content={mission.description || 'No briefing.'} />
						</div>
					</div>

					<div class="flex shrink-0 flex-row gap-2 md:w-44 md:flex-col">
						{#if mission.status === 'Available'}
							<button
								class="btn btn-outline btn-xs"
								on:click={() => patchStatus(mission.id, 'In Progress')}
							>
								Mark In Progress
							</button>
						{:else if mission.status === 'In Progress'}
							<button
								class="btn btn-outline btn-success btn-xs"
								on:click={() => patchStatus(mission.id, 'Completed')}
							>
								Mark Completed
							</button>
						{/if}
						<button class="btn btn-outline btn-primary btn-xs" on:click={() => openEdit(mission)}>
							Edit
						</button>
						<button
							class="btn btn-ghost btn-xs text-base-content/60"
							on:click={() => patchStatus(mission.id, 'Cancelled')}
						>
							Retire
						</button>
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}

<!-- Create / Edit Mission Modal -->
<Modal
	show={showCreateMission}
	title={editingMissionId ? 'Edit Quest' : 'Create New Quest'}
	onClose={() => (showCreateMission = false)}
>
	<div class="space-y-4">
		<div class="flex items-center justify-between">
			<span class="section-label">Quest Details</span>
			<button
				type="button"
				class="btn btn-outline btn-xs border-primary/40 text-primary"
				on:click={() => (showPromptHelper = !showPromptHelper)}
			>
				{showPromptHelper ? 'Close Prompt Helper' : 'LLM Prompt Helper (Copy/Paste)'}
			</button>
		</div>

		{#if showPromptHelper}
			<div class="rounded-md border border-primary/30 bg-base-300/70 p-4 space-y-3">
				<p class="text-xs text-base-content/75">
					Generate a quest using your own ChatGPT, Claude, or Gemini account at zero cost.
				</p>
				<div class="flex gap-2">
					<input
						type="text"
						bind:value={llmTheme}
						placeholder="Optional theme (e.g. sunken goblin shrine, dragon cultists)"
						class="input input-bordered input-xs flex-1"
					/>
					<button type="button" class="btn btn-primary btn-xs" on:click={copyPrompt}>
						Copy Prompt
					</button>
				</div>
				{#if copyFeedback}
					<p class="text-xs text-success">{copyFeedback}</p>
				{/if}

				<div>
					<label for="llm-paste" class="mb-1 block text-xs text-base-content/70">
						Paste LLM JSON Response
					</label>
					<textarea
						id="llm-paste"
						bind:value={llmPasteText}
						rows="4"
						placeholder={'{"name": "...", "description": "...", "tier": "Tier 1", "region": "...", "gold": 50, "xp": 300}'}
						class="textarea textarea-bordered w-full font-mono text-xs"
					></textarea>
				</div>
				{#if parseError}
					<p class="text-xs text-error">{parseError}</p>
				{/if}
				<div class="flex justify-end">
					<button
						type="button"
						class="btn btn-secondary btn-xs"
						disabled={!llmPasteText.trim()}
						on:click={parseLlmResponse}
					>
						Parse &amp; Fill Form
					</button>
				</div>
			</div>
		{/if}

		<div>
			<label for="m-name" class="mb-1 block text-xs font-medium text-base-content/75">Quest Title</label>
			<input
				id="m-name"
				type="text"
				bind:value={mName}
				class="input input-bordered input-sm w-full"
				placeholder="e.g. The Sunken Vault"
			/>
		</div>

		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
			<div>
				<label for="m-tier" class="mb-1 block text-xs font-medium text-base-content/75">Tier</label>
				<div class="flex gap-2">
					<select id="m-tier" bind:value={mTier} class="select select-bordered select-sm flex-1">
						<option value="Tier 1">Tier 1 (Lvl 1–4)</option>
						<option value="Tier 2">Tier 2 (Lvl 5–10)</option>
						<option value="Tier 3">Tier 3 (Lvl 11–16)</option>
						<option value="Tier 4">Tier 4 (Lvl 17–20)</option>
					</select>
					<button type="button" class="btn btn-ghost btn-sm text-xs" on:click={applyTierPreset}>
						Preset
					</button>
				</div>
			</div>

			<div>
				<label for="m-region" class="mb-1 block text-xs font-medium text-base-content/75">
					Region / Location
				</label>
				<input
					id="m-region"
					type="text"
					bind:value={mRegion}
					class="input input-bordered input-sm w-full"
					placeholder="e.g. Ashwood Trail"
				/>
			</div>
		</div>

		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
			<div>
				<label for="m-gold" class="mb-1 block text-xs font-medium text-base-content/75">
					Gold Reward (GP)
				</label>
				<input
					id="m-gold"
					type="number"
					min="0"
					bind:value={mGold}
					class="input input-bordered input-sm w-full stat-num"
				/>
			</div>
			<div>
				<label for="m-xp" class="mb-1 block text-xs font-medium text-base-content/75">
					XP Reward
				</label>
				<input
					id="m-xp"
					type="number"
					min="0"
					bind:value={mXp}
					class="input input-bordered input-sm w-full stat-num"
				/>
			</div>
			<div class="col-span-2 sm:col-span-1">
				<label for="m-item" class="mb-1 block text-xs font-medium text-base-content/75">
					Item Reward
				</label>
				<select id="m-item" bind:value={mItemRewardId} class="select select-bordered select-sm w-full">
					<option value={undefined}>None</option>
					{#each availableItems as item}
						<option value={item.id}>{item.name}</option>
					{/each}
				</select>
			</div>
		</div>

		<div>
			<div class="mb-1 flex items-center justify-between">
				<label for="m-desc" class="text-xs font-medium text-base-content/75">Briefing (Markdown)</label>
				<div class="join">
					<button
						type="button"
						class="btn btn-xs join-item {mDescriptionTab === 'write' ? 'btn-primary' : 'btn-ghost'}"
						on:click={() => (mDescriptionTab = 'write')}
					>
						Write
					</button>
					<button
						type="button"
						class="btn btn-xs join-item {mDescriptionTab === 'preview' ? 'btn-primary' : 'btn-ghost'}"
						on:click={() => (mDescriptionTab = 'preview')}
					>
						Preview
					</button>
				</div>
			</div>
			{#if mDescriptionTab === 'write'}
				<textarea
					id="m-desc"
					bind:value={mDescription}
					class="textarea textarea-bordered h-32 w-full text-sm"
					placeholder="Describe the quest hook, objectives, and hazards..."
				></textarea>
			{:else}
				<div class="min-h-32 rounded-md border border-base-content/10 bg-base-300/50 p-3 text-sm">
					<MarkdownRenderer content={mDescription || '*Nothing to preview.*'} />
				</div>
			{/if}
		</div>

		<div>
			<button
				type="button"
				class="text-xs text-base-content/60 hover:text-base-content"
				on:click={() => (showAdvanced = !showAdvanced)}
			>
				{showAdvanced ? '▾' : '▸'} Advanced Options (Status, Cooldown, Prerequisites)
			</button>
			{#if showAdvanced}
				<div class="mt-2 grid grid-cols-1 gap-3 rounded-md border border-base-content/10 p-3 sm:grid-cols-2">
					<div>
						<label for="m-status" class="mb-1 block text-xs text-base-content/70">Status</label>
						<select id="m-status" bind:value={mStatus} class="select select-bordered select-xs w-full">
							<option value="Available">Available</option>
							<option value="In Progress">In Progress</option>
							<option value="Completed">Completed</option>
							<option value="Cancelled">Cancelled</option>
						</select>
					</div>
					<div>
						<label for="m-cooldown" class="mb-1 block text-xs text-base-content/70">Cooldown (days)</label>
						<input
							id="m-cooldown"
							type="number"
							min="0"
							bind:value={mCooldown}
							class="input input-bordered input-xs w-full stat-num"
						/>
					</div>
					<div class="sm:col-span-2">
						<label for="m-prereq" class="mb-1 block text-xs text-base-content/70">
							Prerequisite Quest
						</label>
						<select id="m-prereq" bind:value={mPrerequisiteId} class="select select-bordered select-xs w-full">
							<option value={undefined}>None</option>
							{#each missions.filter((m) => m.id !== editingMissionId) as prereq}
								<option value={prereq.id}>{prereq.name}</option>
							{/each}
						</select>
					</div>
					<label class="flex items-center gap-2 text-xs">
						<input type="checkbox" class="checkbox checkbox-xs" bind:checked={mIsDiscoverable} />
						Visible on Quest Board
					</label>
				</div>
			{/if}
		</div>
	</div>

	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={() => (showCreateMission = false)}>Cancel</button>
		<button class="btn btn-primary btn-sm" disabled={!mName.trim()} on:click={saveMission}>
			{editingMissionId ? 'Save Changes' : 'Post Quest'}
		</button>
	</div>
</Modal>
