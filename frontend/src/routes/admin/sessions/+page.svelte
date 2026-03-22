<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { get } from 'svelte/store';
	import { API_BASE_URL } from '$lib/config';
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

	onMount(async () => {
		const authState = get(auth);
		if (!authState.isAuthenticated || authState.user?.role !== 'admin') {
			goto('/dashboard');
			return;
		}
		await fetchSessions();
	});

	async function fetchSessions() {
		loading = true;
		try {
			const res = await fetch(`${API_BASE_URL}/sessions/`, {
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) sessions = await res.json();
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

		try {
			const res = await fetch(`${API_BASE_URL}/sessions/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${get(auth).token}`
				},
				body: JSON.stringify({
					name: sName,
					description: sDescription,
					session_date: new Date(sDate).toISOString(),
					status: 'Open',
					min_players: sMinPlayers,
					max_players: sMaxPlayers
				})
			});
			if (res.ok) {
				success = 'Session scheduled.';
				showCreate = false;
				await fetchSessions();
			}
		} catch (e) {
			error = 'Failed to create session.';
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
			cCasualties = cCasualties.filter(id => id !== charId);
		} else {
			cCasualties = [...cCasualties, charId];
		}
	}

	async function submitComplete() {
		if (!completingSession) return;
		completing = true;
		error = '';
		try {
			const res = await fetch(`${API_BASE_URL}/sessions/${completingSession.id}/complete`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${get(auth).token}` },
				body: JSON.stringify({
					result: cResult,
					essence_earned: cEssenceEarned,
					after_action_report: cAfterAction || null,
					casualties: cCasualties,
				}),
			});
			if (res.ok) {
				success = 'Session completed and ledger updated!';
				showComplete = false;
				await fetchSessions();
			} else {
				const data = await res.json();
				error = data.detail ?? 'Failed to complete session.';
			}
		} catch (e) {
			error = 'Failed to complete session.';
		} finally {
			completing = false;
		}
	}

	async function forceConfirm(proposalId: number) {
		try {
			const res = await fetch(`${API_BASE_URL}/sessions/proposals/${proposalId}/force_confirm`, {
				method: 'POST',
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) {
				success = 'Proposal force-confirmed.';
				await fetchSessions();
			}
		} catch (e) {}
	}

	async function vetoProposal(proposalId: number) {
		try {
			const res = await fetch(`${API_BASE_URL}/sessions/proposals/${proposalId}/veto`, {
				method: 'POST',
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) {
				success = 'Proposal vetoed.';
				await fetchSessions();
			}
		} catch (e) {}
	}

	async function kickPlayer(sessionId: number, characterId: number) {
		try {
			const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}/kick/${characterId}`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) {
				success = 'Player removed from roster.';
				await fetchSessions();
			}
		} catch (e) {}
	}
</script>

<div class="container mx-auto max-w-6xl p-4">
	<div class="mb-8 flex items-center justify-between">
		<h1 class="text-primary text-4xl font-[var(--font-cinzel)] font-bold">Session Management</h1>
		<button class="btn btn-primary" on:click={() => (showCreate = true)}>+ Schedule Session</button>
	</div>

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else}
		<div class="grid grid-cols-1 gap-6">
			{#each sessions as session}
				<div class="card bg-base-200 overflow-hidden shadow-xl">
					<div class="flex h-full flex-col md:flex-row">
						<div
							class="bg-primary/10 flex min-w-[150px] flex-col items-center justify-center p-6 text-center"
						>
							<span class="text-xs font-bold uppercase opacity-50"
								>{new Date(session.session_date).toLocaleDateString('en-US', {
									month: 'short'
								})}</span
							>
							<span class="text-3xl font-bold">{new Date(session.session_date).getDate()}</span>
							<span class="text-xs opacity-50">{new Date(session.session_date).getFullYear()}</span>
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

							<p class="mb-4 text-sm opacity-70">
								{session.description || 'No description provided.'}
							</p>

							<div class="flex flex-col gap-4">
								{#if session.status === 'Confirmed' && session.confirmed_mission}
									<div class="bg-success/5 border-success/20 rounded-lg border p-3">
										<span class="text-success text-xs font-bold uppercase opacity-70"
											>Running Mission</span
										>
										<h3 class="text-lg font-bold">{session.confirmed_mission.name}</h3>
										<div class="mt-2 flex flex-wrap gap-2">
											{#each session.players as p}
												<div class="badge badge-sm badge-ghost gap-2">
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
											<div class="bg-base-300/30 border-base-content/5 rounded border p-3">
												<div class="flex items-start justify-between">
													<div>
														<h4 class="font-bold">{proposal.mission.name}</h4>
														<span class="text-xs opacity-50">{proposal.backers.length} backers</span
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
														class="btn btn-xs btn-outline btn-error"
														on:click={() => vetoProposal(proposal.id)}>Veto</button
													>
												</div>
											</div>
										{/each}
									</div>
								{/if}

								<div class="ml-auto mt-2 flex gap-2">
									{#if session.status === 'Confirmed'}
										<button
											class="btn btn-sm btn-success"
											on:click={() => openCompleteModal(session)}>Finalize & Complete</button
										>
									{/if}
									<button class="btn btn-sm btn-ghost text-error">Cancel Slot</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/each}
			{#if sessions.length === 0}
				<div
					class="bg-base-200 rounded-box border-base-content/10 border-2 border-dashed py-20 text-center"
				>
					<h2 class="text-2xl font-bold opacity-50">No sessions scheduled yet.</h2>
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
				class="input input-bordered w-full"
				placeholder="e.g. The Spooky Swamp Crawl"
			/>
		</div>
		<div class="grid grid-cols-2 gap-4">
			<div>
				<label class="label"><span class="label-text">Min Players</span></label>
				<input type="number" bind:value={sMinPlayers} class="input input-bordered w-full" />
			</div>
			<div>
				<label class="label"><span class="label-text">Max Players</span></label>
				<input type="number" bind:value={sMaxPlayers} class="input input-bordered w-full" />
			</div>
		</div>
		<div>
			<label class="label"><span class="label-text">Date and Time</span></label>
			<input type="datetime-local" bind:value={sDate} class="input input-bordered w-full" />
		</div>
		<div>
			<label class="label"><span class="label-text">Admin Override Name</span></label>
			<input
				type="text"
				bind:value={sName}
				class="input input-bordered w-full"
				placeholder="e.g. Saturday Slot"
			/>
		</div>
		<div>
			<label class="label"><span class="label-text">Briefing</span></label>
			<textarea
				bind:value={sDescription}
				class="textarea textarea-bordered h-24 w-full"
				placeholder="What should they expect?"
			></textarea>
		</div>
	</div>
	<div slot="action">
		<button class="btn btn-primary w-full" on:click={createSession}>Schedule Session</button>
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
				<label class="flex items-center gap-2 cursor-pointer">
					<input type="radio" class="radio radio-success" bind:group={cResult} value="success" />
					<span class="text-success font-medium">✅ Success</span>
				</label>
				<label class="flex items-center gap-2 cursor-pointer">
					<input type="radio" class="radio radio-error" bind:group={cResult} value="failure" />
					<span class="text-error font-medium">❌ Failure</span>
				</label>
			</div>
		</div>

		<!-- Resources -->
		<div>
			<label class="label"><span class="label-text">⚡ Essence Earned (net, after transit)</span></label>
			<input type="number" class="input input-bordered input-sm w-full" bind:value={cEssenceEarned} />
			<p class="text-xs opacity-50 mt-1">Positive = crew brought Essence back to Meridian. Negative = reserves were spent.</p>
		</div>

		<!-- Casualties -->
		{#if completingSession.players.length > 0}
		<div>
			<label class="label"><span class="label-text">💀 Casualties (mark as Dead)</span></label>
			<div class="flex flex-wrap gap-2">
				{#each completingSession.players as p}
				<label class="flex items-center gap-2 cursor-pointer border border-base-content/20 rounded px-3 py-1 {cCasualties.includes(p.id) ? 'bg-error/20 border-error/40' : ''}">
					<input type="checkbox" class="checkbox checkbox-sm checkbox-error"
						checked={cCasualties.includes(p.id)}
						on:change={() => toggleCasualty(p.id)} />
					<span class="text-sm">{p.name}</span>
				</label>
				{/each}
			</div>
		</div>
		{/if}

		<!-- After-Action Report -->
		<div>
			<label class="label"><span class="label-text">After-Action Report (optional)</span></label>
			<textarea class="textarea textarea-bordered w-full h-20" bind:value={cAfterAction} placeholder="What happened? How did it go?"></textarea>
		</div>

		{#if error}
		<div class="alert alert-error text-sm">{error}</div>
		{/if}
	</div>
	{/if}
	<div slot="action">
		<button class="btn btn-success w-full" on:click={submitComplete} disabled={completing}>
			{completing ? 'Processing...' : 'Log Session Result'}
		</button>
	</div>
</Modal>
