<script lang="ts">
	import { onMount } from 'svelte';
	import type { GameSessionWithPlayers, Mission } from '$lib/types';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import { MISSIONS_NAV } from '$lib/navigation';
	import SubNav from '$lib/components/SubNav.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';

	let sessions: GameSessionWithPlayers[] = [];
	let availableMissions: Mission[] = [];
	let error: string | null = null;
	let viewFilter: 'upcoming' | 'completed' = 'upcoming';

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
			const all: Mission[] = await api('GET', '/missions/');
			availableMissions = (all ?? []).filter((m) => !m.is_retired && m.is_discoverable);
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

	function isInSession(session: GameSessionWithPlayers): boolean {
		if (!myCharacterId) return false;
		return session.players.some((p) => p.id === myCharacterId);
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

	async function joinConfirmedSession(sessionId: number) {
		error = null;
		try {
			await api('POST', `/sessions/${sessionId}/signup`);
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to join session';
		}
	}

	async function leaveConfirmedSession(sessionId: number) {
		error = null;
		try {
			await api('DELETE', `/sessions/${sessionId}/signup`);
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to leave session';
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

	$: filteredSessions = sessions
		.filter((s) =>
			viewFilter === 'upcoming'
				? s.status !== 'Completed' && s.status !== 'Cancelled'
				: s.status === 'Completed'
		)
		.sort((a, b) =>
			viewFilter === 'upcoming'
				? new Date(a.session_date).getTime() - new Date(b.session_date).getTime()
				: new Date(b.session_date).getTime() - new Date(a.session_date).getTime()
		);
</script>

<div class="page-container">
	<SubNav items={MISSIONS_NAV} />

	<PageHeader
		title="Session Schedule"
		subtitle="Propose quests for open slots, join confirmed parties, or read past field reports."
	>
		<div slot="actions" class="join">
			<button
				class="btn btn-sm join-item {viewFilter === 'upcoming' ? 'btn-primary' : 'btn-ghost border border-base-content/15'}"
				on:click={() => (viewFilter = 'upcoming')}
			>
				Upcoming
			</button>
			<button
				class="btn btn-sm join-item {viewFilter === 'completed' ? 'btn-primary' : 'btn-ghost border border-base-content/15'}"
				on:click={() => (viewFilter = 'completed')}
			>
				Past Sessions &amp; AARs
			</button>
		</div>
	</PageHeader>

	{#if error}
		<div class="alert alert-error mb-6 text-sm">{error}</div>
	{/if}

	{#if filteredSessions.length === 0}
		<div class="panel p-12 text-center">
			<p class="text-base font-medium text-base-content/75">
				{viewFilter === 'upcoming'
					? 'No upcoming sessions scheduled.'
					: 'No completed sessions recorded yet.'}
			</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
			{#each filteredSessions as session}
				<article class="panel flex flex-col p-5">
					<div class="mb-2 flex items-start justify-between gap-2">
						<div>
							<h2 class="text-base font-semibold text-base-content">{session.name}</h2>
							<p class="mt-0.5 text-xs text-base-content/60 stat-num">
								{new Date(session.session_date).toLocaleString(undefined, {
									dateStyle: 'medium',
									timeStyle: 'short'
								})}
							</p>
						</div>
						<span
							class="badge badge-sm shrink-0 {session.status === 'Confirmed'
								? 'badge-success'
								: session.status === 'Completed'
									? 'badge-ghost'
									: 'badge-outline border-warning/40 text-warning'}"
						>
							{session.status}
						</span>
					</div>

					{#if session.description}
						<div class="prose prose-sm mb-3 max-w-none text-xs text-base-content/70">
							<MarkdownRenderer content={session.description} />
						</div>
					{/if}

					{#if session.status === 'Completed'}
						{#if session.confirmed_mission}
							<p class="mb-2 text-xs font-medium text-primary">
								Quest: {session.confirmed_mission.name}
							</p>
						{/if}
						{#if session.after_action_report}
							<div class="mb-3 rounded-md border border-base-content/10 bg-base-300/60 p-3 text-xs text-base-content/80">
								<p class="section-label mb-1">DM Summary</p>
								<MarkdownRenderer content={session.after_action_report} />
							</div>
						{/if}
						{#if session.field_report}
							<div class="mt-auto rounded-md border border-primary/25 bg-primary/5 p-3 text-xs">
								<p class="section-label mb-1 text-primary">Field Report</p>
								<div class="prose prose-sm max-w-none text-base-content/85">
									<MarkdownRenderer content={session.field_report} />
								</div>
							</div>
						{:else if isInSession(session)}
							<div class="mt-auto border-t border-base-content/10 pt-3">
								<label for="fr-{session.id}" class="section-label mb-1.5 block">
									File a Field Report
								</label>
								<textarea
									id="fr-{session.id}"
									class="textarea textarea-bordered w-full text-xs"
									rows="3"
									placeholder="Write your character's dispatch from this session..."
									bind:value={fieldReportDraft[session.id]}
								></textarea>
								<button
									class="btn btn-primary btn-xs mt-2 w-full"
									disabled={!fieldReportDraft[session.id]?.trim() || submittingFieldReport === session.id}
									on:click={() => submitFieldReport(session.id)}
								>
									{submittingFieldReport === session.id ? 'Submitting...' : 'Post Field Report'}
								</button>
							</div>
						{/if}
					{:else if session.status === 'Confirmed' && session.confirmed_mission}
						<div class="mt-2 flex-1 rounded-md border border-success/25 bg-success/5 p-3.5">
							<p class="section-label text-success">Confirmed Quest</p>
							<p class="mt-0.5 text-sm font-semibold text-base-content">
								{session.confirmed_mission.name}
							</p>
							{#if session.confirmed_mission.tier}
								<span class="badge badge-outline badge-xs mt-1">{session.confirmed_mission.tier}</span>
							{/if}

							<div class="mt-3">
								<p class="section-label mb-1.5">
									Party ({session.players.length}/{session.max_players})
								</p>
								<div class="flex flex-wrap gap-1.5">
									{#each session.players as player}
										<span class="rounded bg-base-300 px-2 py-0.5 text-xs text-base-content/85">
											{player.name}
										</span>
									{/each}
								</div>
							</div>
						</div>

						<div class="mt-3 flex justify-end">
							{#if isInSession(session)}
								<button
									class="btn btn-outline btn-error btn-xs"
									on:click={() => leaveConfirmedSession(session.id)}
								>
									Leave Party
								</button>
							{:else if session.players.length < session.max_players}
								<button
									class="btn btn-primary btn-xs w-full"
									disabled={!myCharacterId}
									on:click={() => joinConfirmedSession(session.id)}
								>
									Join Party ({session.players.length}/{session.max_players})
								</button>
							{:else}
								<span class="text-xs text-base-content/50">Party Full</span>
							{/if}
						</div>
					{:else}
						<div class="mt-2 flex-1 space-y-2.5">
							<div class="flex items-center justify-between">
								<span class="section-label">Quest Proposals</span>
								<button
									class="btn btn-ghost btn-xs text-primary"
									disabled={!myCharacterId || availableMissions.length === 0}
									on:click={() => {
										selectedSessionId = session.id;
										selectedMissionId = availableMissions[0]?.id ?? null;
										showProposeModal = true;
									}}
								>
									+ Propose
								</button>
							</div>

							{#if session.proposals.length === 0}
								<p class="py-3 text-center text-xs text-base-content/50">No quests proposed yet.</p>
							{:else}
								{#each session.proposals as proposal}
									<div class="rounded-md border border-base-content/10 bg-base-300/50 p-3">
										<div class="flex items-start justify-between gap-2">
											<span class="text-sm font-medium text-base-content">{proposal.mission.name}</span>
											<button
												class="btn btn-xs shrink-0 {isBacking(proposal.id)
													? 'btn-primary'
													: 'btn-outline border-base-content/20'}"
												disabled={!myCharacterId}
												on:click={() => toggleBacking(proposal.id)}
											>
												{isBacking(proposal.id) ? 'Backing' : 'Back'}
											</button>
										</div>
										<div class="mt-2 flex items-center gap-2">
											<progress
												class="progress progress-primary h-1.5 flex-1"
												value={proposal.backers.length}
												max={session.min_players}
											></progress>
											<span class="text-xs text-base-content/65 stat-num">
												{proposal.backers.length}/{session.min_players}
											</span>
										</div>
									</div>
								{/each}
							{/if}
						</div>
					{/if}
				</article>
			{/each}
		</div>
	{/if}
</div>

<Modal show={showProposeModal} title="Propose a Quest" onClose={() => (showProposeModal = false)}>
	<div>
		<label for="sess-propose-mission" class="mb-1 block text-xs font-medium text-base-content/75">
			Select Quest
		</label>
		<select
			id="sess-propose-mission"
			bind:value={selectedMissionId}
			class="select select-bordered select-sm w-full"
		>
			{#each availableMissions as mission}
				<option value={mission.id}>{mission.name} {mission.tier ? `(${mission.tier})` : ''}</option>
			{/each}
		</select>
	</div>
	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={() => (showProposeModal = false)}>Cancel</button>
		<button
			class="btn btn-primary btn-sm"
			disabled={!selectedMissionId}
			on:click={proposeMission}
		>
			Submit Proposal
		</button>
	</div>
</Modal>
