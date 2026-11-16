<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { GameSessionWithPlayers } from '$lib/types';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { goto } from '$app/navigation';

	let sessions: GameSessionWithPlayers[] = [];
	let loading = true;
	let error = '';
	let success = '';

	// Create Session Form
	let showCreateSession = false;
	let sName = '';
	let sDesc = '';
	let sDate = '';
	let sMinPlayers = 4;
	let sMaxPlayers = 6;

	// Complete Session Modal
	let showCompleteModal = false;
	let completingSession: GameSessionWithPlayers | null = null;
	let cResult: 'success' | 'failure' = 'success';
	let cGoldEarned = 0;
	let cXpEarned = 0;
	let cAar = '';
	let cCasualties: number[] = [];
	let completing = false;

	let dataLoaded = false;

	onMount(() => {
		if (!localStorage.getItem('accessToken')) goto('/dashboard');
	});

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
		try {
			await api('POST', '/sessions/', {
				name: sName,
				description: sDesc,
				session_date: sDate ? new Date(sDate).toISOString() : new Date().toISOString(),
				min_players: sMinPlayers,
				max_players: sMaxPlayers
			});
			success = 'Session slot scheduled.';
			showCreateSession = false;
			sName = '';
			sDesc = '';
			sDate = '';
			await fetchSessions();
		} catch (e) {
			error = 'Failed to create session.';
		}
	}

	async function forceConfirm(proposalId: number) {
		try {
			await api('POST', `/sessions/proposals/${proposalId}/force_confirm`);
			success = 'Session confirmed!';
			await fetchSessions();
		} catch (e) {
			error = 'Failed to confirm proposal.';
		}
	}

	async function vetoProposal(proposalId: number) {
		try {
			await api('POST', `/sessions/proposals/${proposalId}/veto`);
			success = 'Proposal vetoed.';
			await fetchSessions();
		} catch (e) {
			error = 'Failed to veto proposal.';
		}
	}

	async function kickPlayer(sessionId: number, charId: number) {
		try {
			await api('DELETE', `/sessions/${sessionId}/kick/${charId}`);
			success = 'Player removed from session.';
			await fetchSessions();
		} catch (e) {
			error = 'Failed to remove player.';
		}
	}

	async function cancelSession(sessionId: number) {
		error = '';
		try {
			await api('POST', `/sessions/${sessionId}/cancel`);
			success = 'Session slot cancelled.';
			await fetchSessions();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to cancel session.';
		}
	}

	function openCompleteModal(session: GameSessionWithPlayers) {
		completingSession = session;
		cResult = 'success';
		const missionRewards = session.confirmed_mission?.rewards ?? [];
		cGoldEarned = missionRewards.reduce((sum, r) => sum + (r.gold ?? 0), 0);
		cXpEarned = missionRewards.reduce((sum, r) => sum + (r.xp ?? 0), 0);
		cAar = '';
		cCasualties = [];
		showCompleteModal = true;
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
				essence_earned: 0,
				gold_earned: cGoldEarned,
				xp_earned: cXpEarned,
				after_action_report: cAar || null,
				casualties: cCasualties
			});
			success = 'Session completed — Gold, XP, and Ledger updated.';
			showCompleteModal = false;
			await fetchSessions();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to complete session.';
		} finally {
			completing = false;
		}
	}
</script>

<PageHeader
	title="Manage Sessions"
	subtitle="Schedule game slots, confirm proposals, and distribute Gold & XP upon completion."
>
	<button slot="actions" class="btn btn-primary btn-sm" on:click={() => (showCreateSession = true)}>
		+ Schedule Slot
	</button>
</PageHeader>

{#if error}
	<div class="alert alert-error mb-4 text-sm">{error}</div>
{/if}
{#if success}
	<div class="alert alert-success mb-4 text-sm">{success}</div>
{/if}

{#if loading}
	<LoadingSpinner size="lg" />
{:else if sessions.length === 0}
	<div class="panel p-12 text-center text-sm text-base-content/60">
		No sessions scheduled yet.
	</div>
{:else}
	<div class="space-y-4">
		{#each sessions as session}
			<div class="panel overflow-hidden">
				<div class="flex flex-col md:flex-row">
					<div
						class="flex min-w-32 flex-col items-center justify-center border-b border-base-content/10 bg-base-300/60 p-4 text-center md:border-r md:border-b-0"
					>
						<span class="section-label">
							{new Date(session.session_date).toLocaleDateString('en-US', { month: 'short' })}
						</span>
						<span class="text-2xl font-semibold text-primary stat-num">
							{new Date(session.session_date).getDate()}
						</span>
						<span class="text-xs text-base-content/55 stat-num">
							{new Date(session.session_date).getFullYear()}
						</span>
					</div>

					<div class="flex-1 p-5 space-y-4">
						<div class="flex items-start justify-between gap-2">
							<div>
								<h2 class="text-base font-semibold text-base-content">{session.name}</h2>
								{#if session.description}
									<p class="mt-0.5 text-xs text-base-content/65">{session.description}</p>
								{/if}
							</div>
							<span
								class="badge badge-sm shrink-0 {session.status === 'Completed'
									? 'badge-success'
									: session.status === 'Cancelled'
										? 'badge-error'
										: session.status === 'Confirmed'
											? 'badge-primary'
											: 'badge-outline'}"
							>
								{session.status}
							</span>
						</div>

						{#if session.status === 'Confirmed' && session.confirmed_mission}
							<div class="rounded-md border border-success/25 bg-success/5 p-3">
								<p class="section-label text-success">Confirmed Quest</p>
								<p class="text-sm font-semibold text-base-content">{session.confirmed_mission.name}</p>
								<div class="mt-2 flex flex-wrap gap-1.5">
									{#each session.players as p}
										<span class="badge badge-ghost badge-sm gap-1.5">
											{p.name}
											<button
												class="text-error hover:underline"
												aria-label="Remove {p.name}"
												on:click={() => kickPlayer(session.id, p.id)}
											>
												×
											</button>
										</span>
									{/each}
								</div>
							</div>
						{:else if session.proposals.length > 0}
							<div class="grid grid-cols-1 gap-3 md:grid-cols-2">
								{#each session.proposals as proposal}
									<div class="rounded-md border border-base-content/10 bg-base-300/50 p-3">
										<div class="flex items-start justify-between gap-2">
											<div>
												<p class="text-sm font-medium text-base-content">{proposal.mission.name}</p>
												<span class="text-xs text-base-content/60 stat-num">
													{proposal.backers.length} backers
												</span>
											</div>
											<span class="badge badge-xs badge-outline">{proposal.status}</span>
										</div>
										<div class="mt-2.5 flex gap-2">
											<button
												class="btn btn-primary btn-xs"
												on:click={() => forceConfirm(proposal.id)}
											>
												Confirm
											</button>
											<button
												class="btn btn-outline btn-error btn-xs"
												on:click={() => vetoProposal(proposal.id)}
											>
												Veto
											</button>
										</div>
									</div>
								{/each}
							</div>
						{/if}

						{#if session.status !== 'Completed' && session.status !== 'Cancelled'}
							<div class="flex justify-end gap-2 border-t border-base-content/10 pt-3">
								{#if session.status === 'Confirmed'}
									<button class="btn btn-success btn-xs" on:click={() => openCompleteModal(session)}>
										Complete &amp; Award Rewards
									</button>
								{/if}
								<button
									class="btn btn-ghost btn-xs text-error"
									on:click={() => cancelSession(session.id)}
								>
									Cancel Slot
								</button>
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}

<!-- Schedule Slot Modal -->
<Modal show={showCreateSession} title="Schedule Session Slot" onClose={() => (showCreateSession = false)}>
	<div class="space-y-4">
		<div>
			<label for="s-name" class="mb-1 block text-xs font-medium text-base-content/75">Session Title</label>
			<input
				id="s-name"
				type="text"
				bind:value={sName}
				class="input input-bordered input-sm w-full"
				placeholder="e.g. Friday Night Expedition"
			/>
		</div>
		<div class="grid grid-cols-2 gap-3">
			<div>
				<label for="s-min" class="mb-1 block text-xs font-medium text-base-content/75">Min Players</label>
				<input id="s-min" type="number" bind:value={sMinPlayers} class="input input-bordered input-sm w-full stat-num" />
			</div>
			<div>
				<label for="s-max" class="mb-1 block text-xs font-medium text-base-content/75">Max Players</label>
				<input id="s-max" type="number" bind:value={sMaxPlayers} class="input input-bordered input-sm w-full stat-num" />
			</div>
		</div>
		<div>
			<label for="s-date" class="mb-1 block text-xs font-medium text-base-content/75">Date &amp; Time</label>
			<input id="s-date" type="datetime-local" bind:value={sDate} class="input input-bordered input-sm w-full" />
		</div>
		<div>
			<label for="s-desc" class="mb-1 block text-xs font-medium text-base-content/75">Notes</label>
			<textarea
				id="s-desc"
				bind:value={sDesc}
				class="textarea textarea-bordered w-full text-sm"
				rows="3"
				placeholder="Session details or tier restrictions..."
			></textarea>
		</div>
	</div>
	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={() => (showCreateSession = false)}>Cancel</button>
		<button class="btn btn-primary btn-sm" disabled={!sName.trim()} on:click={createSession}>
			Create Slot
		</button>
	</div>
</Modal>

<!-- Complete Session Modal -->
<Modal
	show={showCompleteModal}
	title="Complete Session — {completingSession?.name ?? ''}"
	onClose={() => (showCompleteModal = false)}
>
	{#if completingSession}
		<div class="space-y-4">
			<div>
				<span class="mb-1.5 block text-xs font-medium text-base-content/75">Outcome</span>
				<div class="flex gap-4">
					<label class="flex cursor-pointer items-center gap-2 text-sm">
						<input type="radio" class="radio radio-success radio-sm" bind:group={cResult} value="success" />
						<span>Success</span>
					</label>
					<label class="flex cursor-pointer items-center gap-2 text-sm">
						<input type="radio" class="radio radio-error radio-sm" bind:group={cResult} value="failure" />
						<span>Failure</span>
					</label>
				</div>
			</div>

			<div class="grid grid-cols-2 gap-3">
				<div>
					<label for="c-gold" class="mb-1 block text-xs font-medium text-base-content/75">
						Bonus Gold / Player (GP)
					</label>
					<input
						id="c-gold"
						type="number"
						min="0"
						bind:value={cGoldEarned}
						class="input input-bordered input-sm w-full stat-num"
					/>
				</div>
				<div>
					<label for="c-xp" class="mb-1 block text-xs font-medium text-base-content/75">
						Bonus XP / Player
					</label>
					<input
						id="c-xp"
						type="number"
						min="0"
						bind:value={cXpEarned}
						class="input input-bordered input-sm w-full stat-num"
					/>
				</div>
			</div>

			{#if completingSession.players.length > 0}
				<div>
					<span class="mb-1.5 block text-xs font-medium text-base-content/75">
						Casualties (mark as Dead)
					</span>
					<div class="flex flex-wrap gap-2">
						{#each completingSession.players as player}
							<label class="flex cursor-pointer items-center gap-1.5 rounded border border-base-content/15 px-2.5 py-1 text-xs">
								<input
									type="checkbox"
									class="checkbox checkbox-error checkbox-xs"
									checked={cCasualties.includes(player.id)}
									on:change={() => toggleCasualty(player.id)}
								/>
								<span>{player.name}</span>
							</label>
						{/each}
					</div>
				</div>
			{/if}

			<div>
				<label for="c-aar" class="mb-1 block text-xs font-medium text-base-content/75">
					After-Action Report (optional)
				</label>
				<textarea
					id="c-aar"
					class="textarea textarea-bordered w-full text-sm"
					rows="3"
					bind:value={cAar}
					placeholder="Summary of events, faction consequences, and notable loot..."
				></textarea>
			</div>
		</div>
	{/if}
	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={() => (showCompleteModal = false)}>Cancel</button>
		<button class="btn btn-success btn-sm" disabled={completing} on:click={submitComplete}>
			{completing ? 'Completing...' : 'Finalize & Award'}
		</button>
	</div>
</Modal>
