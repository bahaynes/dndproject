<script lang="ts">
	import { onMount } from 'svelte';
	import type { GameSessionWithPlayers, Mission } from '../../lib/types';
	import { auth } from '../../lib/auth';
	import { api } from '$lib/api';
	import Modal from '$lib/components/Modal.svelte';
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';

	let sessions: GameSessionWithPlayers[] = [];
	let availableMissions: Mission[] = [];
	let error: string | null = null;
	let myCharacterId: number | undefined;

	let showProposeModal = false;
	let selectedSessionId: number | null = null;
	let selectedMissionId: number | null = null;

	// Field report state
	let fieldReportDraft: Record<number, string> = {};
	let submittingFieldReport: number | null = null;

	$: myCharacterId = $auth.user?.active_character?.id;

	onMount(async () => {
		await Promise.all([fetchSessions(), fetchMissions()]);
	});

	async function fetchSessions() {
		error = null;
		try {
			sessions = await api('GET', '/sessions/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to fetch sessions';
		}
	}

	async function fetchMissions() {
		try {
			availableMissions = await api('GET', '/missions/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load missions';
		}
	}

	function isBacking(proposalId: number): boolean {
		if (!myCharacterId) return false;
		const session = sessions.find((s) => s.proposals.some((p) => p.id === proposalId));
		if (!session) return false;
		const proposal = session.proposals.find((p) => p.id === proposalId);
		return proposal?.backers.some((b) => b.id === myCharacterId) || false;
	}

	async function toggleBacking(proposalId: number) {
		error = null;
		try {
			await api('POST', `/sessions/proposals/${proposalId}/toggle_back`);
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		}
	}

	async function submitFieldReport(sessionId: number) {
		const text = fieldReportDraft[sessionId];
		if (!text?.trim()) return;
		submittingFieldReport = sessionId;
		error = null;
		try {
			await api('PATCH', `/sessions/${sessionId}/field-report`, { field_report: text });
			fieldReportDraft[sessionId] = '';
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			submittingFieldReport = null;
		}
	}

	async function proposeMission() {
		if (!selectedSessionId || !selectedMissionId) return;
		error = null;
		try {
			await api('POST', '/sessions/proposals', {
				session_id: selectedSessionId,
				mission_id: selectedMissionId
			});
			showProposeModal = false;
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		}
	}
</script>

<div class="container mx-auto p-4">
	<h1 class="text-2xl font-bold">Game Sessions</h1>

	{#if error}
		<div class="my-4 alert alert-error">
			<div class="flex-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					class="mx-2 h-6 w-6 stroke-current"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
					></path>
				</svg>
				<span>{error}</span>
			</div>
		</div>
	{/if}

	{#if sessions.length === 0 && !error}
		<p class="mt-4">There are no scheduled sessions at this time. Check back later!</p>
	{:else}
		<div class="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
			{#each sessions as session}
				<div class="card border border-base-content/10 bg-base-100 shadow-xl">
					<div class="card-body">
						<div class="flex items-start justify-between">
							<h2 class="card-title text-primary">{session.name}</h2>
							<div class="badge {session.status === 'Confirmed' ? 'badge-success' : 'badge-info'}">
								{session.status}
							</div>
						</div>

						<div class="mb-4 text-sm text-base-content/70">
							<MarkdownRenderer content={session.description || 'No description provided.'} />
						</div>
						<div class="my-2 rounded bg-base-200 p-2 text-sm">
							<span class="font-bold">📅 Date:</span>
							{new Date(session.session_date).toLocaleString()}
						</div>

						{#if session.status === 'Completed'}
							<!-- Dispatch from the Mission Board -->
							{#if session.field_report}
								<div class="mt-4 rounded-xl border border-primary/30 bg-primary/5 p-4">
									<div class="mb-2 flex items-center gap-2">
										<span class="text-xs font-bold tracking-widest text-base-content/65 uppercase"
											>Dispatch from the Field</span
										>
									</div>
									<div class="prose prose-sm max-w-none font-serif opacity-90">
										<MarkdownRenderer content={session.field_report} />
									</div>
								</div>
							{:else if session.players.some((p) => p.id === myCharacterId)}
								<div class="mt-4 rounded-xl border border-base-content/10 bg-base-200/50 p-4">
									<p class="mb-2 text-xs font-bold text-base-content/60 uppercase">
										File a Field Report
									</p>
									<textarea
										class="textarea-bordered textarea w-full text-sm"
										rows="4"
										placeholder="Write your dispatch from the mission, in the voice of your character..."
										bind:value={fieldReportDraft[session.id]}
									></textarea>
									<button
										class="btn mt-2 w-full btn-sm btn-primary"
										disabled={!fieldReportDraft[session.id]?.trim() ||
											submittingFieldReport === session.id}
										on:click={() => submitFieldReport(session.id)}
									>
										{submittingFieldReport === session.id ? 'Submitting...' : 'Post to the Board'}
									</button>
								</div>
							{/if}
						{:else if session.status === 'Confirmed' && session.confirmed_mission}
							<div class="mt-4 rounded-xl border border-success/20 bg-success/10 p-4">
								<h3 class="font-bold text-success">Confirmed Content</h3>
								<p class="text-lg font-[var(--font-cinzel)]">{session.confirmed_mission.name}</p>
								{#if session.confirmed_mission.tier}
									<div class="mt-1 badge badge-outline badge-sm">
										{session.confirmed_mission.tier}
									</div>
								{/if}
								<div class="mt-4">
									<span class="text-xs font-bold text-base-content/60 uppercase"
										>Heroes Confirmed</span
									>
									<div class="mt-1 flex flex-wrap gap-1">
										{#each session.players as player}
											<div class="badge badge-ghost badge-sm">{player.name}</div>
										{/each}
									</div>
								</div>
							</div>
						{:else}
							<div class="mt-4">
								<div class="mb-2 flex items-center justify-between">
									<h3 class="text-xs font-bold text-base-content/60 uppercase">Proposals</h3>
									{#if session.status !== 'Completed' && session.status !== 'Cancelled'}
										<button
											class="btn btn-ghost btn-xs"
											on:click={() => {
												selectedSessionId = session.id;
												showProposeModal = true;
											}}>+ Propose</button
										>
									{/if}
								</div>

								{#each session.proposals as proposal}
									<div class="mb-4 rounded-xl border border-base-content/5 bg-base-200/50 p-3">
										<div class="flex items-center justify-between">
											<span class="font-bold">{proposal.mission.name}</span>
											<span class="text-xs">{proposal.backers.length} / {session.min_players}</span>
										</div>

										<progress
											class="progress mt-2 w-full progress-primary"
											value={proposal.backers.length}
											max={session.min_players}
										></progress>

										<div class="mt-3 flex items-center justify-between">
											<div class="flex -space-x-2">
												{#each proposal.backers as backer}
													<div class="placeholder avatar">
														<div
															class="h-6 w-6 rounded-full border-2 border-base-100 bg-neutral text-neutral-content"
														>
															<span class="text-[8px]">{backer.name.charAt(0)}</span>
														</div>
													</div>
												{/each}
											</div>
											<button
												class="btn btn-xs {isBacking(proposal.id)
													? 'btn-secondary'
													: 'btn-outline btn-primary'}"
												on:click={() => toggleBacking(proposal.id)}
												disabled={!myCharacterId}
											>
												{isBacking(proposal.id) ? 'Backing' : 'Back This'}
											</button>
										</div>
									</div>
								{/each}
								{#if session.proposals.length === 0}
									<div class="py-4 text-center text-xs text-base-content/60 italic">
										No proposals yet. Be the first!
									</div>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<Modal
	show={showProposeModal}
	title="Propose Content for Slot"
	onClose={() => (showProposeModal = false)}
>
	<div class="form-control w-full">
		<label class="label" for="mission-select"
			><span class="label-text">Select a Mission</span></label
		>
		<select
			id="mission-select"
			bind:value={selectedMissionId}
			class="select-bordered select w-full"
		>
			<option value={null}>-- Pick a Mission --</option>
			{#each availableMissions as mission}
				{@const inCooldown =
					mission.last_run_date &&
					new Date().getTime() - new Date(mission.last_run_date).getTime() <
						mission.cooldown_days * 24 * 60 * 60 * 1000}
				<option value={mission.id} disabled={!!inCooldown}>
					{mission.name} ({mission.tier || 'No Tier'}) {inCooldown ? '- ❄️ Cooldown' : ''}
				</option>
			{/each}
		</select>
		<p class="mt-4 text-sm text-base-content/70 italic">
			Proposing will add you as the first backer. When a proposal hits {sessions.find(
				(s) => s.id === selectedSessionId
			)?.min_players || 4} backers, the session is locked.
		</p>
	</div>
	<div slot="action">
		<button class="btn w-full btn-primary" on:click={proposeMission} disabled={!selectedMissionId}
			>Propose Now</button
		>
	</div>
</Modal>
