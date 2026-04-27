<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { GameSessionWithPlayers } from '$lib/types';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { goto } from '$app/navigation';

	let sessions: GameSessionWithPlayers[] = [];
	let loading = true;
	let error = '';
	let success = '';

	// Complete session modal
	let showComplete = false;
	let completingSession: GameSessionWithPlayers | null = null;
	let cResult: 'success' | 'failure' = 'success';
	let cEssenceEarned = 0;
	let cAfterAction = '';
	let cCasualties: number[] = [];
	let completing = false;

	// Create Session Form
	let sName = '';
	let sDescription = '';
	let sDate = '';
	let sMinPlayers = 4;
	let sMaxPlayers = 6;
	let showCreate = false;

	let dataLoaded = false;

	onMount(() => {
		if (!localStorage.getItem('accessToken')) goto('/dashboard');
	});

	$: if ($auth.isAuthenticated && $auth.user?.role !== 'admin') {
		goto('/dashboard');
	}

	$: if ($auth.isAuthenticated && $auth.user?.role === 'admin' && !dataLoaded) {
		dataLoaded = true;
		fetchSessions();
	}

	async function fetchSessions() {
		loading = true;
		try {
			sessions = await api('GET', '/sessions/');
		} catch (e) {
			error = 'Failed to load sessions.';
		} finally {
			loading = false;
		}
	}

	async function createSession() {
		error = '';
		if (!sName || !sDate) {
			error = 'Session title and date/time are required!';
			return;
		}

		let sessionDateIso = '';
		try {
			sessionDateIso = new Date(sDate).toISOString();
		} catch (e) {
			error = 'Invalid date/time format.';
			return;
		}

		try {
			await api('POST', '/sessions/', {
				name: sName,
				description: sDescription,
				session_date: sessionDateIso,
				status: 'Open',
				min_players: sMinPlayers || 4,
				max_players: sMaxPlayers || 6
			});
			showCreate = false;
			sName = '';
			sDescription = '';
			sDate = '';
			await fetchSessions();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create session.';
		}
	}

	function openCompleteModal(session: GameSessionWithPlayers) {
		completingSession = session;
		cResult = 'success';
		cEssenceEarned = 0;
		cAfterAction = '';
		cCasualties = [];
		showComplete = true;
	}

	function toggleCasualty(charId: number) {
		if (cCasualties.includes(charId)) {
			cCasualties = cCasualties.filter((id) => id !== charId);
		} else {
			cCasualties = [...cCasualties, charId];
		}
	}

	async function submitComplete() {
		if (!completingSession) return;
		completing = true;
		error = '';
		try {
			await api('POST', `/sessions/${completingSession.id}/complete`, {
				result: cResult,
				essence_earned: cEssenceEarned,
				after_action_report: cAfterAction || null,
				casualties: cCasualties
			});
			showComplete = false;
			await fetchSessions();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to complete session.';
		} finally {
			completing = false;
		}
	}

	async function forceConfirm(proposalId: number) {
		try {
			await api('POST', `/sessions/proposals/${proposalId}/force_confirm`);
			await fetchSessions();
		} catch (e) {}
	}

	async function vetoProposal(proposalId: number) {
		try {
			await api('POST', `/sessions/proposals/${proposalId}/veto`);
			await fetchSessions();
		} catch (e) {}
	}

	async function kickPlayer(sessionId: number, characterId: number) {
		try {
			await api('DELETE', `/sessions/${sessionId}/kick/${characterId}`);
			await fetchSessions();
		} catch (e) {}
	}
</script>

<div class="container mx-auto max-w-6xl p-4">
	<div class="mb-8 flex items-center justify-between">
		<h1 class="text-4xl font-[var(--font-cinzel)] font-bold text-primary">Session Management</h1>
		<button class="btn btn-primary" on:click={() => (showCreate = true)}>+ Schedule Session</button>
	</div>

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else}
		<div class="grid grid-cols-1 gap-6">
			{#each sessions as session}
				<div class="card overflow-hidden bg-base-200 shadow-xl">
					<div class="flex h-full flex-col md:flex-row">
						<div
							class="flex min-w-[150px] flex-col items-center justify-center bg-primary/10 p-6 text-center"
						>
							<span class="text-xs font-bold text-base-content/65 uppercase"
								>{new Date(session.session_date).toLocaleDateString('en-US', {
									month: 'short'
								})}</span
							>
							<span class="text-3xl font-bold">{new Date(session.session_date).getDate()}</span>
							<span class="text-xs text-base-content/60"
								>{new Date(session.session_date).getFullYear()}</span
							>
						</div>

						<div class="card-body flex-grow">
							<div class="flex items-start justify-between">
								<h2 class="card-title text-2xl font-bold">{session.name}</h2>
								<div
									class="badge {session.status === 'Completed' ? 'badge-success' : 'badge-info'}"
								>
									{session.status}
								</div>
							</div>

							<p class="mb-4 text-sm text-base-content/70">
								{session.description || 'No description provided.'}
							</p>

							<div class="flex flex-col gap-4">
								{#if session.status === 'Confirmed' && session.confirmed_mission}
									<div class="rounded-lg border border-success/20 bg-success/5 p-3">
										<span class="text-xs font-bold text-success uppercase opacity-70"
											>Running Mission</span
										>
										<h3 class="text-lg font-bold">{session.confirmed_mission.name}</h3>
										<div class="mt-2 flex flex-wrap gap-2">
											{#each session.players as p}
												<div class="badge gap-2 badge-ghost badge-sm">
													{p.name}
													<button
														class="text-error hover:scale-110"
														on:click={() => kickPlayer(session.id, p.id)}>×</button
													>
												</div>
											{/each}
										</div>
									</div>
								{:else}
									<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
										{#each session.proposals as proposal}
											<div class="rounded border border-base-content/5 bg-base-300/30 p-3">
												<div class="flex items-start justify-between">
													<div>
														<h4 class="font-bold">{proposal.mission.name}</h4>
														<span class="text-xs text-base-content/60"
															>{proposal.backers.length} backers</span
														>
													</div>
													<div class="badge badge-xs">{proposal.status}</div>
												</div>
												<div class="mt-3 flex gap-2">
													<button
														class="btn btn-xs btn-primary"
														on:click={() => forceConfirm(proposal.id)}>Force Confirm</button
													>
													<button
														class="btn btn-outline btn-xs btn-error"
														on:click={() => vetoProposal(proposal.id)}>Veto</button
													>
												</div>
											</div>
										{/each}
									</div>
								{/if}

								<div class="mt-2 ml-auto flex gap-2">
									{#if session.status === 'Confirmed'}
										<button
											class="btn btn-sm btn-success"
											on:click={() => openCompleteModal(session)}>Finalize & Complete</button
										>
									{/if}
									<button class="btn text-error btn-ghost btn-sm">Cancel Slot</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/each}
			{#if sessions.length === 0}
				<div
					class="rounded-box border-2 border-dashed border-base-content/10 bg-base-200 py-20 text-center"
				>
					<h2 class="text-2xl font-bold text-base-content/60">No sessions scheduled yet.</h2>
				</div>
			{/if}
		</div>
	{/if}
</div>

<Modal show={showCreate} title="Schedule Game Session" onClose={() => (showCreate = false)}>
	<div class="form-control gap-4">
		<div>
			<label class="label"><span class="label-text">Session Title</span></label>
			<input
				type="text"
				bind:value={sName}
				class="input-bordered input w-full"
				placeholder="e.g. The Spooky Swamp Crawl"
			/>
		</div>
		<div class="grid grid-cols-2 gap-4">
			<div>
				<label class="label"><span class="label-text">Min Players</span></label>
				<input type="number" bind:value={sMinPlayers} class="input-bordered input w-full" />
			</div>
			<div>
				<label class="label"><span class="label-text">Max Players</span></label>
				<input type="number" bind:value={sMaxPlayers} class="input-bordered input w-full" />
			</div>
		</div>
		<div>
			<label class="label"><span class="label-text">Date and Time</span></label>
			<input type="datetime-local" bind:value={sDate} class="input-bordered input w-full" />
		</div>
		<div>
			<label class="label"><span class="label-text">Briefing</span></label>
			<textarea
				bind:value={sDescription}
				class="textarea-bordered textarea h-24 w-full"
				placeholder="What should they expect?"
			></textarea>
		</div>
		{#if error}
			<div class="alert text-sm alert-error">{error}</div>
		{/if}
	</div>
	<div slot="action">
		<button class="btn w-full btn-primary" on:click={createSession}>Schedule Session</button>
	</div>
</Modal>

<!-- Complete Session Modal -->
<Modal show={showComplete} title="Complete Session" onClose={() => (showComplete = false)}>
	{#if completingSession}
		<div class="form-control gap-4">
			<!-- Result -->
			<div>
				<label class="label"><span class="label-text font-semibold">Mission Result</span></label>
				<div class="flex gap-4">
					<label class="flex cursor-pointer items-center gap-2">
						<input type="radio" class="radio radio-success" bind:group={cResult} value="success" />
						<span class="font-medium text-success">✅ Success</span>
					</label>
					<label class="flex cursor-pointer items-center gap-2">
						<input type="radio" class="radio radio-warning" bind:group={cResult} value="failure" />
						<span class="font-medium text-warning">❌ Failure</span>
					</label>
				</div>
			</div>

			<!-- Resources -->
			<div>
				<label class="label"
					><span class="label-text">⚡ Essence Earned (net, after transit)</span></label
				>
				<input
					type="number"
					class="input-bordered input input-sm w-full"
					bind:value={cEssenceEarned}
				/>
				<p class="mt-1 text-xs text-base-content/60">
					Positive = Essence returned to reserves. Negative = reserves were spent.
				</p>
			</div>

			<!-- Casualties -->
			{#if completingSession.players.length > 0}
				<div>
					<label class="label"><span class="label-text">💀 Casualties (mark as Dead)</span></label>
					<div class="flex flex-wrap gap-2">
						{#each completingSession.players as p}
							<label
								class="flex cursor-pointer items-center gap-2 rounded border border-base-content/20 px-3 py-1 {cCasualties.includes(
									p.id
								)
									? 'border-error/40 bg-error/20'
									: ''}"
							>
								<input
									type="checkbox"
									class="checkbox checkbox-sm checkbox-error"
									checked={cCasualties.includes(p.id)}
									on:change={() => toggleCasualty(p.id)}
								/>
								<span class="text-sm">{p.name}</span>
							</label>
						{/each}
					</div>
				</div>
			{/if}

			<!-- After-Action Report -->
			<div>
				<label class="label"><span class="label-text">After-Action Report (optional)</span></label>
				<textarea
					class="textarea-bordered textarea h-20 w-full"
					bind:value={cAfterAction}
					placeholder="What happened? How did it go?"
				></textarea>
			</div>

			{#if error}
				<div class="alert text-sm alert-error">{error}</div>
			{/if}
		</div>
	{/if}
	<div slot="action">
		<button class="btn w-full btn-success" on:click={submitComplete} disabled={completing}>
			{completing ? 'Processing...' : 'Log Session Result'}
		</button>
	</div>
</Modal>
