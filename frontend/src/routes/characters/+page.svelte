<script lang="ts">
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { Character, InventoryItem } from '$lib/types';
	import { safeExternalUrl } from '$lib/utils/url';
	import { ADVENTURERS_NAV } from '$lib/navigation';
	import SubNav from '$lib/components/SubNav.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let characters: Character[] = [];
	let viewCharacter: Character | null = null;
	let loading = true;
	let error = '';

	// Editing state
	let isEditing = false;
	let editName = '';
	let editDescription = '';
	let editCharacterSheetUrl = '';
	let editClassName = '';
	let editLevel = 1;

	// Creation state
	let isCreating = false;
	let newCharName = '';
	let newCharDesc = '';

	$: activeCharacterId = $auth.user?.active_character?.id;

	$: if ($auth.token && loading && characters.length === 0 && !error) {
		fetchMyCharacters();
	}

	$: xpCurrent = viewCharacter?.stats?.xp ?? 0;
	$: xpNext = viewCharacter?.stats?.next_level_xp ?? null;
	$: xpPct = xpNext ? Math.min(100, Math.round((xpCurrent / xpNext) * 100)) : 100;
	$: safeSheetUrl = safeExternalUrl(viewCharacter?.character_sheet_url);
	$: isAdmin = $auth.user?.role === 'admin';

	async function fetchMyCharacters() {
		try {
			characters = await api('GET', '/characters/');
			const currentId = viewCharacter?.id ?? activeCharacterId;
			const found = characters.find((c) => c.id === currentId);
			viewCharacter = found || characters[0] || null;
			if (viewCharacter) resetEditForm();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load characters.';
		} finally {
			loading = false;
		}
	}

	function resetEditForm() {
		if (viewCharacter) {
			editName = viewCharacter.name;
			editDescription = viewCharacter.description || '';
			editCharacterSheetUrl = viewCharacter.character_sheet_url || '';
			editClassName = viewCharacter.class_name || '';
			editLevel = viewCharacter.level ?? 1;
		}
	}

	function selectCharacter(char: Character) {
		viewCharacter = char;
		isEditing = false;
		resetEditForm();
	}

	async function activateCharacter(char: Character) {
		const { token, campaign } = $auth;
		try {
			const updatedUser = await api('POST', `/characters/${char.id}/activate`);
			if (token) auth.login(updatedUser, token, campaign ?? undefined);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to activate character.';
		}
	}

	async function createCharacter() {
		if (!newCharName.trim()) return;
		error = '';
		try {
			const newChar = await api('POST', '/characters/', {
				name: newCharName.trim(),
				description: newCharDesc.trim() || 'A new adventurer.'
			});
			await fetchMyCharacters();
			const found = characters.find((c) => c.id === newChar.id);
			if (found) selectCharacter(found);
			isCreating = false;
			newCharName = '';
			newCharDesc = '';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error creating character.';
		}
	}

	async function handleUpdate() {
		if (!viewCharacter) return;
		const { token, campaign, user } = $auth;
		error = '';
		try {
			const payload: Record<string, unknown> = {
				name: editName,
				description: editDescription,
				character_sheet_url: editCharacterSheetUrl,
				class_name: editClassName || null
			};
			if (isAdmin) {
				payload.level = editLevel;
			}
			const updated = await api('PUT', `/characters/${viewCharacter.id}`, payload);
			characters = characters.map((c) => (c.id === updated.id ? updated : c));
			viewCharacter = updated;
			isEditing = false;
			if (activeCharacterId === updated.id && user && token) {
				auth.login({ ...user, active_character: updated }, token, campaign ?? undefined);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to update character.';
		}
	}

	async function removeInventoryItem(invItem: InventoryItem) {
		if (!viewCharacter) return;
		error = '';
		try {
			await api('DELETE', `/characters/${viewCharacter.id}/inventory/${invItem.id}`);
			await fetchMyCharacters();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to remove item.';
		}
	}
</script>

<div class="page-container">
	<SubNav items={ADVENTURERS_NAV} />

	<PageHeader
		title="My Characters"
		subtitle="Manage your adventurers, 5e progression, external character sheets, and equipment."
	>
		<button slot="actions" class="btn btn-primary btn-sm" on:click={() => (isCreating = !isCreating)}>
			{isCreating ? 'Cancel' : '+ New Character'}
		</button>
	</PageHeader>

	{#if error}
		<div class="alert alert-error mb-6 text-sm">{error}</div>
	{/if}

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else}
		<div class="flex flex-col gap-6 lg:flex-row">
			<!-- Left Sidebar: Character Selector -->
			<aside class="w-full space-y-3 lg:w-64 shrink-0">
				{#if isCreating}
					<div class="panel border-primary/40 p-4 space-y-2.5">
						<h2 class="text-sm font-semibold text-base-content">New Adventurer</h2>
						<input
							type="text"
							placeholder="Character Name"
							class="input input-sm input-bordered w-full"
							bind:value={newCharName}
						/>
						<textarea
							placeholder="Brief backstory"
							class="textarea textarea-sm textarea-bordered w-full"
							rows="2"
							bind:value={newCharDesc}
						></textarea>
						<div class="flex gap-2">
							<button class="btn btn-primary btn-xs flex-1" on:click={createCharacter}>Create</button>
							<button class="btn btn-ghost btn-xs flex-1" on:click={() => (isCreating = false)}>
								Cancel
							</button>
						</div>
					</div>
				{/if}

				{#if characters.length === 0 && !isCreating}
					<div class="panel p-6 text-center">
						<p class="text-sm text-base-content/65">No characters yet.</p>
						<button class="btn btn-primary btn-sm mt-3 w-full" on:click={() => (isCreating = true)}>
							Create First Character
						</button>
					</div>
				{:else}
					<div class="space-y-2">
						{#each characters as char}
							<button
								class="panel flex w-full items-center gap-3 p-3 text-left transition-colors {viewCharacter?.id ===
								char.id
									? 'border-primary/60 bg-base-300/60'
									: 'hover:border-base-content/20'}"
								on:click={() => selectCharacter(char)}
							>
								<div
									class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-base-300 text-sm font-semibold text-primary"
								>
									{char.name.charAt(0).toUpperCase()}
								</div>
								<div class="min-w-0 flex-1">
									<p class="truncate text-sm font-medium text-base-content">{char.name}</p>
									<p class="text-xs text-base-content/60 stat-num">
										Lvl {char.level} {char.class_name || 'Adventurer'}
									</p>
								</div>
								{#if activeCharacterId === char.id}
									<span class="badge badge-success badge-xs">Active</span>
								{/if}
							</button>
						{/each}
					</div>
				{/if}
			</aside>

			<!-- Right Main: Character Sheet & Inline Inventory -->
			<div class="min-w-0 flex-1 space-y-6">
				{#if viewCharacter}
					<section class="panel p-6">
						<div class="flex flex-col justify-between gap-4 border-b border-base-content/10 pb-5 sm:flex-row sm:items-start">
							<div class="flex items-start gap-4">
								<div
									class="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg border border-primary/30 bg-base-300 font-[var(--font-cinzel)] text-2xl font-semibold text-primary"
								>
									{viewCharacter.name.charAt(0).toUpperCase()}
								</div>
								<div>
									{#if isEditing}
										<input
											type="text"
											class="input input-bordered input-sm mb-2 w-full max-w-xs font-semibold"
											bind:value={editName}
											aria-label="Character Name"
										/>
										<div class="flex gap-2">
											<input
												type="text"
												class="input input-bordered input-xs w-36"
												placeholder="Class (e.g. Fighter)"
												bind:value={editClassName}
												aria-label="Class"
											/>
											{#if isAdmin}
												<input
													type="number"
													class="input input-bordered input-xs w-20 stat-num"
													min="1"
													max="20"
													bind:value={editLevel}
													aria-label="Level"
												/>
											{/if}
										</div>
									{:else}
										<div class="flex flex-wrap items-center gap-2">
											<h2 class="text-xl font-semibold text-base-content">{viewCharacter.name}</h2>
											<span
												class="badge badge-sm {viewCharacter.status === 'Active'
													? 'badge-success'
													: viewCharacter.status === 'Dead'
														? 'badge-error'
														: 'badge-ghost'}"
											>
												{viewCharacter.status}
											</span>
										</div>
										<p class="mt-0.5 text-sm text-base-content/65">
											Level <span class="stat-num font-medium text-base-content">{viewCharacter.level}</span>
											{viewCharacter.class_name || 'Adventurer'} ·
											<span class="stat-num">{viewCharacter.missions_completed}</span> quests completed
										</p>
									{/if}
								</div>
							</div>

							<div class="flex flex-wrap items-center gap-2">
								{#if activeCharacterId !== viewCharacter.id}
									<button
										class="btn btn-primary btn-sm"
										on:click={() => activateCharacter(viewCharacter!)}
									>
										Set Active
									</button>
								{:else}
									<span class="badge badge-outline border-success/40 text-success badge-sm">
										Active Character
									</span>
								{/if}
								{#if !isEditing}
									<button class="btn btn-ghost btn-sm" on:click={() => (isEditing = true)}>
										Edit
									</button>
								{/if}
							</div>
						</div>

						<!-- Gold & 5e XP Progression Bar -->
						<div class="grid grid-cols-1 gap-4 border-b border-base-content/10 py-4 sm:grid-cols-3">
							<div>
								<p class="section-label">Gold</p>
								<p class="mt-1 text-lg font-semibold text-primary stat-num">
									{viewCharacter.stats?.gold ?? 0} GP
								</p>
							</div>
							<div class="sm:col-span-2">
								<div class="mb-1 flex justify-between text-xs">
									<span class="section-label">Experience (5e)</span>
									<span class="text-base-content/75 stat-num">
										{xpCurrent.toLocaleString()} {xpNext ? `/ ${xpNext.toLocaleString()} XP` : 'XP (Max)'}
									</span>
								</div>
								<progress class="progress progress-primary h-2 w-full" value={xpPct} max="100"></progress>
							</div>
						</div>

						<!-- Backstory / Edit Form -->
						{#if isEditing}
							<div class="mt-4 space-y-3">
								<div>
									<label for="edit-backstory" class="mb-1 block text-xs font-medium text-base-content/70">
										Backstory &amp; Notes
									</label>
									<textarea
										id="edit-backstory"
										class="textarea textarea-bordered w-full text-sm"
										rows="4"
										bind:value={editDescription}
									></textarea>
								</div>
								<div>
									<label for="edit-sheet-url" class="mb-1 block text-xs font-medium text-base-content/70">
										External Character Sheet URL (D&amp;D Beyond, Foundry, etc.)
									</label>
									<input
										id="edit-sheet-url"
										type="url"
										class="input input-bordered input-sm w-full"
										placeholder="https://..."
										bind:value={editCharacterSheetUrl}
									/>
								</div>
								<div class="flex justify-end gap-2 pt-2">
									<button
										class="btn btn-ghost btn-sm"
										on:click={() => {
											isEditing = false;
											resetEditForm();
										}}
									>
										Cancel
									</button>
									<button class="btn btn-primary btn-sm" on:click={handleUpdate}>Save Changes</button>
								</div>
							</div>
						{:else}
							<div class="mt-4 space-y-3">
								<p class="whitespace-pre-wrap text-sm leading-relaxed text-base-content/80">
									{viewCharacter.description || 'No backstory provided.'}
								</p>
								{#if safeSheetUrl}
									<div>
										<a
											href={safeSheetUrl}
											target="_blank"
											rel="noopener noreferrer"
											class="btn btn-outline btn-xs border-primary/40 text-primary"
										>
											Open External Character Sheet →
										</a>
									</div>
								{/if}
							</div>
						{/if}
					</section>

					<!-- Inline Inventory -->
					<section class="panel p-6">
						<div class="mb-4 flex items-center justify-between">
							<div>
								<h3 class="text-base font-semibold text-base-content">Inventory &amp; Gear</h3>
								<p class="text-xs text-base-content/55">
									Items acquired from quests or the Quartermaster Store.
								</p>
							</div>
							<a href="/store" class="btn btn-outline btn-xs border-primary/40 text-primary">
								Visit Store →
							</a>
						</div>

						{#if !viewCharacter.inventory || viewCharacter.inventory.length === 0}
							<p class="py-4 text-center text-sm text-base-content/50">
								No items in inventory.
							</p>
						{:else}
							<div class="overflow-x-auto">
								<table class="table table-sm">
									<thead>
										<tr class="border-b border-base-content/10 text-xs text-base-content/55">
											<th>Item</th>
											<th>Notes</th>
											<th class="text-right">Qty</th>
											<th class="text-right">Action</th>
										</tr>
									</thead>
									<tbody>
										{#each viewCharacter.inventory as invItem}
											<tr class="border-b border-base-content/5">
												<td class="font-medium text-base-content">{invItem.item.name}</td>
												<td class="text-xs text-base-content/65">
													{invItem.item.description || '—'}
												</td>
												<td class="text-right stat-num">{invItem.quantity}</td>
												<td class="text-right">
													<button
														class="btn btn-ghost btn-xs text-error"
														on:click={() => removeInventoryItem(invItem)}
													>
														Remove
													</button>
												</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						{/if}
					</section>
				{:else}
					<div class="panel p-12 text-center text-sm text-base-content/55">
						Select or create a character to view details.
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
