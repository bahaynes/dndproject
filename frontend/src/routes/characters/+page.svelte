<script lang="ts">
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { Character } from '$lib/types';
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

	async function fetchMyCharacters() {
		try {
			characters = await api('GET', '/characters/');
			const active = characters.find((c) => c.id === activeCharacterId);
			viewCharacter = active || characters[0] || null;
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
			console.error('Failed to activate character', e);
		}
	}

	async function createCharacter() {
		if (!newCharName) return;
		try {
			const newChar = await api('POST', '/characters/', {
				name: newCharName,
				description: newCharDesc || 'A new adventurer.'
			});
			await fetchMyCharacters();
			const found = characters.find((c) => c.id === newChar.id);
			if (found) selectCharacter(found);
			isCreating = false;
			newCharName = '';
			newCharDesc = '';
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Error creating character');
		}
	}

	async function handleUpdate() {
		if (!viewCharacter) return;
		const { token, campaign, user } = $auth;
		try {
			const updated = await api('PUT', `/characters/${viewCharacter.id}`, {
				name: editName,
				description: editDescription,
				character_sheet_url: editCharacterSheetUrl,
				class_name: editClassName || null,
				level: editLevel
			});
			characters = characters.map((c) => (c.id === updated.id ? updated : c));
			viewCharacter = updated;
			isEditing = false;
			if (activeCharacterId === updated.id && user && token) {
				auth.login({ ...user, active_character: updated }, token, campaign ?? undefined);
			}
		} catch (e) {
			alert('Failed to update character');
		}
	}
</script>

<div class="container mx-auto max-w-6xl p-4">
	{#if loading}
		<div class="flex justify-center p-12"><LoadingSpinner size="lg" /></div>
	{:else if error}
		<div class="alert alert-error">{error}</div>
	{:else}
		<div class="flex flex-col gap-6 lg:flex-row">
			<!-- LEFT SIDEBAR: Character List -->
			<div class="flex w-full flex-col gap-4 lg:w-1/4">
				<div class="flex items-center justify-between">
					<h2 class="text-xl font-[var(--font-cinzel)] font-bold">Heroes</h2>
					<button class="btn btn-xs btn-ghost" on:click={() => (isCreating = true)}>+ New</button>
				</div>

				{#if isCreating}
					<div class="card bg-base-200 border-primary border p-4">
						<h3 class="mb-2 text-sm font-bold">New Hero</h3>
						<input
							type="text"
							placeholder="Name"
							class="input input-sm input-bordered mb-2 w-full"
							bind:value={newCharName}
						/>
						<textarea
							placeholder="Brief description"
							class="textarea textarea-sm textarea-bordered mb-2 w-full"
							bind:value={newCharDesc}
						></textarea>
						<div class="flex gap-2">
							<button class="btn btn-xs btn-primary flex-1" on:click={createCharacter}
								>Create</button
							>
							<button class="btn btn-xs flex-1" on:click={() => (isCreating = false)}>Cancel</button
							>
						</div>
					</div>
				{/if}

				<div class="flex flex-col gap-2">
					{#each characters as char}
						<button
							class="card card-side bg-base-100 hover:bg-base-200 items-center gap-3 border p-2 text-left transition-all
                         {viewCharacter?.id === char.id
								? 'border-primary ring-primary ring-1'
								: 'border-base-content/10'}"
							on:click={() => selectCharacter(char)}
						>
							<div class="avatar placeholder">
								<div class="bg-neutral text-neutral-content w-10 rounded-full">
									<span class="text-xs">{char.name.charAt(0)}</span>
								</div>
							</div>
							<div class="min-w-0 flex-1">
								<div class="truncate text-sm font-bold">{char.name}</div>
								<div class="text-[10px] opacity-60">Lvl {char.level} {char.class_name || 'Adventurer'}</div>
							</div>
							{#if activeCharacterId === char.id}
								<div class="badge badge-success badge-xs">Active</div>
							{/if}
						</button>
					{/each}

					{#if characters.length === 0 && !isCreating}
						<div class="py-4 text-center text-sm italic opacity-50">
							No heroes found. Create one to begin!
						</div>
						<button class="btn btn-primary btn-sm w-full" on:click={() => (isCreating = true)}
							>Create First Character</button
						>
					{/if}
				</div>
			</div>

			<!-- RIGHT MAIN: Character Detail -->
			<div class="w-full lg:w-3/4">
				{#if viewCharacter}
					<div class="flex flex-col gap-6">
						<!-- Header / Banner -->
						<div class="card bg-base-200 border-primary/10 border shadow-xl">
							<div class="card-body">
								<div
									class="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center"
								>
									<div class="flex items-center gap-4">
										<div class="avatar placeholder">
											<div class="bg-primary text-primary-content h-20 w-20 rounded-xl text-3xl">
												{viewCharacter.name.charAt(0)}
											</div>
										</div>
										<div>
											{#if isEditing}
												<input
													type="text"
													class="input input-bordered input-lg w-full max-w-xs font-[var(--font-cinzel)]"
													bind:value={editName}
												/>
												<div class="flex gap-2 mt-2">
													<input type="text" class="input input-bordered input-sm w-32" placeholder="Class" bind:value={editClassName} />
													<input type="number" class="input input-bordered input-sm w-20" min="1" max="20" placeholder="Lvl" bind:value={editLevel} />
												</div>
											{:else}
												<h1 class="text-primary text-3xl font-[var(--font-cinzel)] font-bold">
													{viewCharacter.name}
												</h1>
												<p class="text-sm opacity-70">Level {viewCharacter.level} {viewCharacter.class_name || 'Adventurer'}</p>
												<div class="flex gap-2 mt-1">
													<span class="badge badge-sm {viewCharacter.status === 'Active' ? 'badge-success' : viewCharacter.status === 'Dead' ? 'badge-error' : 'badge-ghost'}">{viewCharacter.status}</span>
													{#if viewCharacter.missions_completed > 0}
														<span class="badge badge-sm badge-outline">{viewCharacter.missions_completed} missions</span>
													{/if}
												</div>
											{/if}
										</div>
									</div>

									<div class="flex flex-col items-end gap-2">
										{#if activeCharacterId !== viewCharacter.id}
											<button
												class="btn btn-primary btn-sm"
												on:click={() => activateCharacter(viewCharacter!)}
											>
												Set as Active
											</button>
										{:else}
											<div class="badge badge-lg badge-success gap-2 p-3">
												<span class="h-2 w-2 animate-pulse rounded-full bg-black"></span>
												Currently Active
											</div>
										{/if}
										<div class="mt-2 flex gap-2">
											<div class="badge badge-outline">Essence: {viewCharacter.stats.xp}</div>
											<div class="badge badge-outline badge-primary">
												Scrip: {viewCharacter.stats.scrip}
											</div>
										</div>
									</div>
								</div>

								<div class="divider my-2"></div>

								{#if isEditing}
									<div class="form-control">
										<label class="label">
											<span class="label-text">Backstory</span>
											<textarea
												class="textarea textarea-bordered mt-1 h-32 w-full"
												bind:value={editDescription}
											></textarea>
										</label>
									</div>
									<div class="form-control mt-2">
										<label class="label">
											<span class="label-text">Character Sheet URL</span>
											<input
												type="text"
												class="input input-bordered mt-1 w-full"
												bind:value={editCharacterSheetUrl}
											/>
										</label>
									</div>
									<div class="mt-4 flex justify-end gap-2">
										<button
											class="btn btn-ghost"
											on:click={() => {
												isEditing = false;
												resetEditForm();
											}}>Cancel</button
										>
										<button class="btn btn-primary" on:click={handleUpdate}>Save Changes</button>
									</div>
								{:else}
									<div class="prose mb-4 max-w-none whitespace-pre-wrap text-sm opacity-80">
										{viewCharacter.description || 'No backstory provided.'}
									</div>

									<div class="mt-4 flex items-center justify-between">
										<div class="flex gap-2">
											{#if viewCharacter.character_sheet_url}
												<a
													href={viewCharacter.character_sheet_url}
													target="_blank"
													class="btn btn-xs btn-outline">Ext. Sheet</a
												>
											{/if}
											<button class="btn btn-xs btn-ghost" on:click={() => (isEditing = true)}
												>Edit Profile</button
											>
										</div>
									</div>
								{/if}
							</div>
						</div>

						<!-- Action Grid (Only enabled if this is active character?) -->
						<!-- Actually, we should probably allow viewing inventory/missions even inactive, but context might get weird. 
                     For now, let's allow it but the pages themselves assume active_character. 
                     Ideally we'd pass ID in URL, but our routes are /inventory currently.
                     So we should warn if viewing non-active. -->

						{#if activeCharacterId !== viewCharacter.id}
							<div class="alert alert-warning text-sm shadow-lg">
								<span
									>Activate this character to manage their inventory, missions, or store purchases.</span
								>
							</div>
						{/if}

						<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
							<a
								href="/characters/inventory"
								class="btn h-auto flex-col gap-1 py-4 {activeCharacterId !== viewCharacter.id
									? 'btn-disabled opacity-50'
									: 'btn-outline'}"
							>
								<span class="text-xl">🎒</span>
								<span>Inventory</span>
							</a>
							<a
								href="/missions"
								class="btn h-auto flex-col gap-1 py-4 {activeCharacterId !== viewCharacter.id
									? 'btn-disabled opacity-50'
									: 'btn-outline'}"
							>
								<span class="text-xl">📜</span>
								<span>Missions</span>
							</a>
							<a
								href="/sessions"
								class="btn h-auto flex-col gap-1 py-4 {activeCharacterId !== viewCharacter.id
									? 'btn-disabled opacity-50'
									: 'btn-outline'}"
							>
								<span class="text-xl">📅</span>
								<span>Sessions</span>
							</a>
							<a
								href="/store"
								class="btn h-auto flex-col gap-1 py-4 {activeCharacterId !== viewCharacter.id
									? 'btn-disabled opacity-50'
									: 'btn-outline'}"
							>
								<span class="text-xl">⚖️</span>
								<span>Store</span>
							</a>
						</div>
					</div>
				{:else if !loading}
					<div class="flex h-full items-center justify-center opacity-50">
						Select or create a hero to view details.
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
