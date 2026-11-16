<script lang="ts">
	import { onMount } from 'svelte';
	import type { GameSessionWithPlayers, Mission } from '../../lib/types';
	import { auth } from '../../lib/auth';
	import { api } from '$lib/api';
	import { formatSessionDateTime, parseUtcDate, toLocalDateTimeInput } from '$lib/date';
	import Modal from '$lib/components/Modal.svelte';
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
	import { DragDropManager } from '$lib/dnd.svelte';

	const dnd = new DragDropManager<Mission>();

	let sessions: GameSessionWithPlayers[] = [];
	let availableMissions: Mission[] = [];
	let error: string | null = null;
	let loading = true;
	let showPast = false;

	// Propose modal
	let showProposeModal = false;
	let selectedSessionId: number | null = null;
	let selectedMissionId: number | null = null;

	// Field report state
	let fieldReportDraft: Record<number, string> = {};
	let submittingFieldReport: number | null = null;

	// Admin: Create / Edit session modal
	let showSessionModal = false;
	let editingSessionId: number | null = null;
	let sName = '';
	let sDescription = '';
	let sDate = '';
	let sMinPlayers = 4;
	let sMaxPlayers = 6;
	let sStatus = 'Open';
	let savingSession = false;

	// Admin: Complete session modal
	let showCompleteModal = false;
	let completingSession: GameSessionWithPlayers | null = null;
	let cResult: 'success' | 'failure' = 'success';
	let cEssenceEarned = 0;
	let cAfterAction = '';
	let cCasualties: number[] = [];
	let completing = false;

	$: myCharacterId = $auth.user?.active_character?.id;
	$: isAdmin = $auth.user?.role === 'admin';

	$: upcomingSessions = sessions
		.filter((s) => s.status !== 'Completed' && s.status !== 'Cancelled')
		.sort((a, b) => parseUtcDate(a.session_date).getTime() - parseUtcDate(b.session_date).getTime());

	$: pastSessions = sessions
		.filter((s) => s.status === 'Completed' || s.status === 'Cancelled')
		.sort((a, b) => parseUtcDate(b.session_date).getTime() - parseUtcDate(a.session_date).getTime());

	onMount(async () => {
		await Promise.all([fetchSessions(), fetchMissions()]);
		loading = false;
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
		const proposal = session?.proposals.find((p) => p.id === proposalId);
		return proposal?.backers.some((b) => b.id === myCharacterId) || false;
	}

	function isSignedUp(session: GameSessionWithPlayers): boolean {
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

	async function toggleSessionSignup(session: GameSessionWithPlayers) {
		error = null;
		try {
			if (isSignedUp(session)) {
				await api('DELETE', `/sessions/${session.id}/signup`);
			} else {
				await api('POST', `/sessions/${session.id}/signup`);
			}
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update session signup';
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

	async function handleDrop(e: DragEvent, sessionId: number) {
		const payload = dnd.getPayload(e);
		if (!payload) return;
		selectedSessionId = sessionId;
		selectedMissionId = payload.id;
		await proposeMission();
	}

	// --- Admin actions ---
	function openCreateModal() {
		editingSessionId = null;
		sName = '';
		sDescription = '';
		sDate = '';
		sMinPlayers = 4;
		sMaxPlayers = 6;
		sStatus = 'Open';
		showSessionModal = true;
	}

	function openEditModal(session: GameSessionWithPlayers) {
		editingSessionId = session.id;
		sName = session.name;
		sDescription = session.description ?? '';
		sDate = toLocalDateTimeInput(session.session_date);
		sMinPlayers = session.min_players;
		sMaxPlayers = session.max_players;
		sStatus = session.status;
		showSessionModal = true;
	}

	async function saveSession() {
		error = null;
		if (!sName.trim() || !sDate) {
			error = 'Session title and date/time are required.';
			return;
		}
		savingSession = true;
		try {
			const payload = {
				name: sName.trim(),
				description: sDescription,
				session_date: new Date(sDate).toISOString(),
				status: sStatus,
				min_players: Number(sMinPlayers),
				max_players: Number(sMaxPlayers)
			};
			if (editingSessionId !== null) {
				await api('PUT', `/sessions/${editingSessionId}`, payload);
			} else {
				await api('POST', '/sessions/', payload);
			}
			showSessionModal = false;
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to save session.';
		} finally {
			savingSession = false;
		}
	}

	async function cancelSession(session: GameSessionWithPlayers) {
		error = null;
		try {
			await api('PUT', `/sessions/${session.id}`, {
				name: session.name,
				description: session.description ?? '',
				session_date: parseUtcDate(session.session_date).toISOString(),
				status: 'Cancelled',
				min_players: session.min_players,
				max_players: session.max_players
			});
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to cancel session.';
		}
	}

	function openCompleteModal(session: GameSessionWithPlayers) {
		completingSession = session;
		cResult = 'success';
		cEssenceEarned = 0;
		cAfterAction = '';
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
		error = null;
		try {
			await api('POST', `/sessions/${completingSession.id}/complete`, {
				result: cResult,
				essence_earned: cEssenceEarned,
				after_action_report: cAfterAction || null,
				casualties: cCasualties
			});
			showCompleteModal = false;
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to complete session.';
		} finally {
			completing = false;
		}
	}

	async function forceConfirm(proposalId: number) {
		error = null;
		try {
			await api('POST', `/sessions/proposals/${proposalId}/force_confirm`);
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to confirm proposal.';
		}
	}

	async function vetoProposal(proposalId: number) {
		error = null;
		try {
			await api('POST', `/sessions/proposals/${proposalId}/veto`);
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to veto proposal.';
		}
	}

	async function kickPlayer(sessionId: number, characterId: number) {
		error = null;
		try {
			await api('DELETE', `/sessions/${sessionId}/kick/${characterId}`);
			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to remove player.';
		}
	}
</script>

<div class="container mx-auto max-w-6xl space-y-8 p-4 py-8">
	<div class="flex flex-wrap items-center justify-between gap-4 border-b border-base-content/10 pb-4">
		<div>
			<h1 class="text-4xl font-[var(--font-cinzel)] font-bold text-primary">Game Sessions</h1>
			<p class="mt-1 text-sm text-base-content/65">
				Propose or sign up for upcoming games, or file dispatches for completed runs.
			</p>
		</div>
		{#if isAdmin}
			<button class="btn btn-primary" on:click={openCreateModal}>+ Schedule Session</button>
		{/if}
	</div>

	{#if !myCharacterId && $auth.isAuthenticated}
		<div class="alert border border-primary/25 bg-primary/10 text-sm">
			<span>You need an active character before you can propose or sign up for a session.</span>
			<a href="/characters" class="btn btn-xs btn-primary">Create Character →</a>
		</div>
	{/if}

	{#if error}
		<div class="alert alert-error">
			<span>{error}</span>
		</div>
	{/if}

	{#if loading}
		<div class="flex justify-center py-16">
			<span class="loading loading-lg loading-spinner text-primary"></span>
		</div>
	{:else if sessions.length === 0}
		<div class="rounded-xl border border-base-content/10 bg-base-200/40 p-10 text-center">
			<p class="text-base-content/60">There are no scheduled sessions at this time.</p>
			{#if isAdmin}
				<button class="btn mt-4 btn-sm btn-primary" on:click={openCreateModal}
					>+ Schedule Your First Session</button
				>
			{/if}
		</div>
	{:else}
		<!-- Available Missions for Dragging (only shown if there are upcoming sessions) -->
		{#if upcomingSessions.length > 0 && availableMissions.length > 0}
			<div>
				<h2 class="mb-3 text-sm font-bold tracking-wider text-base-content/65 uppercase">
					Available Missions <span class="font-normal normal-case opacity-75"
						>(Drag onto a session card to propose)</span
					>
				</h2>
				<div class="flex gap-3 overflow-x-auto pb-2">
					{#each availableMissions as mission}
						{@const inCooldown =
							mission.last_run_date &&
							Date.now() - parseUtcDate(mission.last_run_date).getTime() <
								mission.cooldown_days * 86400000}
						<!-- svelte-ignore a11y-no-static-element-interactions -->
						<div
							class="card min-w-[220px] border border-base-content/10 bg-base-200 shadow-sm {inCooldown
								? 'cursor-not-allowed opacity-50'
								: 'cursor-grab hover:bg-base-300'}"
							draggable={!inCooldown}
							on:dragstart={(e) => !inCooldown && dnd.handleDragStart(e, mission)}
							on:dragend={() => dnd.handleDragEnd()}
						>
							<div class="card-body p-3">
								<h3 class="text-sm font-[var(--font-cinzel)] font-bold">{mission.name}</h3>
								<div class="mt-1 flex items-center justify-between text-xs">
									<span class="badge badge-outline badge-xs">{mission.tier || 'No Tier'}</span>
									{#if inCooldown}
										<span class="font-bold text-warning">❄️ Cooldown</span>
									{/if}
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Upcoming Sessions -->
		<section class="space-y-4">
			<h2 class="text-xl font-[var(--font-cinzel)] font-bold text-primary">
				Upcoming ({upcomingSessions.length})
			</h2>
			{#if upcomingSessions.length === 0}
				<p class="text-sm text-base-content/60 italic">No upcoming sessions scheduled.</p>
			{:else}
				<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
					{#each upcomingSessions as session}
						<!-- svelte-ignore a11y-no-static-element-interactions -->
						<div
							class="card border border-base-content/10 bg-base-100 shadow-lg transition-colors duration-200"
							on:dragover|preventDefault={(e) => {
								e.dataTransfer!.dropEffect = 'copy';
							}}
							on:drop|preventDefault={(e) => handleDrop(e, session.id)}
							class:ring-2={dnd.isDragging}
							class:ring-primary={dnd.isDragging}
						>
							<div class="card-body p-5">
								<div class="flex items-start justify-between gap-2">
									<div>
										<h3 class="card-title font-[var(--font-cinzel)] text-primary">
											{session.name}
										</h3>
										<p class="mt-1 text-xs font-medium text-base-content/75">
											📅 {formatSessionDateTime(session.session_date)}
										</p>
									</div>
									<div class="flex items-center gap-2">
										<span
											class="badge badge-sm {session.status === 'Confirmed'
												? 'badge-success'
												: 'badge-info'}"
										>
											{session.status}
										</span>
										{#if isAdmin}
											<button
												class="btn btn-ghost btn-xs"
												on:click={() => openEditModal(session)}
												title="Edit Session">Edit</button
											>
										{/if}
									</div>
								</div>

								{#if session.description}
									<div class="mt-2 text-sm text-base-content/75">
										<MarkdownRenderer content={session.description} />
									</div>
								{/if}

								{#if session.status === 'Confirmed' && session.confirmed_mission}
									<div class="mt-4 rounded-xl border border-success/20 bg-success/10 p-4">
										<div class="flex items-start justify-between gap-2">
											<div>
												<p class="text-xs font-bold tracking-wider text-success uppercase">
													Confirmed Mission
												</p>
												<p class="text-lg font-[var(--font-cinzel)] font-bold">
													{session.confirmed_mission.name}
												</p>
												{#if session.confirmed_mission.tier}
													<span class="mt-1 badge badge-outline badge-xs"
														>{session.confirmed_mission.tier}</span
													>
												{/if}
											</div>
											{#if myCharacterId}
												<button
													class="btn btn-xs {isSignedUp(session)
														? 'btn-secondary'
														: 'btn-primary'}"
													on:click={() => toggleSessionSignup(session)}
												>
													{isSignedUp(session) ? '✓ Signed Up' : 'Join Roster'}
												</button>
											{/if}
										</div>

										<div class="mt-3">
											<span class="text-xs font-bold text-base-content/60 uppercase">
												Roster ({session.players.length} / {session.max_players})
											</span>
											<div class="mt-1.5 flex flex-wrap gap-1.5">
												{#each session.players as player}
													<span class="badge gap-1 badge-ghost badge-sm">
														{player.name}
														{#if isAdmin}
															<button
																class="text-error hover:font-bold"
																on:click={() => kickPlayer(session.id, player.id)}
																title="Remove player">✕</button
															>
														{/if}
													</span>
												{/each}
											</div>
										</div>
									</div>
								{:else}
									<div class="mt-4">
										<div class="mb-2 flex items-center justify-between">
											<h4 class="text-xs font-bold text-base-content/60 uppercase">
												Proposals (min {session.min_players} crew)
											</h4>
											<button
												class="btn btn-ghost btn-xs"
												disabled={!myCharacterId}
												on:click={() => {
													selectedSessionId = session.id;
													showProposeModal = true;
												}}>+ Propose</button
											>
										</div>

										{#each session.proposals as proposal}
											<div class="mb-3 rounded-xl border border-base-content/5 bg-base-200/50 p-3">
												<div class="flex items-center justify-between gap-2">
													<span class="font-bold">{proposal.mission.name}</span>
													<span class="text-xs text-base-content/70">
														{proposal.backers.length} / {session.min_players}
													</span>
												</div>

												<progress
													class="progress mt-2 w-full progress-primary"
													value={proposal.backers.length}
													max={session.min_players}
												></progress>

												<div class="mt-3 flex flex-wrap items-center justify-between gap-2">
													<div class="flex flex-wrap gap-1">
														{#each proposal.backers as backer}
															<span class="badge badge-ghost badge-xs">{backer.name}</span>
														{/each}
													</div>
													<div class="flex items-center gap-1.5">
														{#if isAdmin && proposal.status !== 'vetoed'}
															<button
																class="btn btn-outline btn-xs btn-success"
																on:click={() => forceConfirm(proposal.id)}>Confirm</button
															>
															<button
																class="btn btn-ghost btn-xs text-error"
																on:click={() => vetoProposal(proposal.id)}>Veto</button
															>
														{/if}
														<button
															class="btn btn-xs {isBacking(proposal.id)
																? 'btn-secondary'
																: 'btn-outline btn-primary'}"
															on:click={() => toggleBacking(proposal.id)}
															disabled={!myCharacterId}
														>
															{isBacking(proposal.id) ? '✓ Signed Up' : 'Sign Up'}
														</button>
													</div>
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

								{#if isAdmin}
									<div class="mt-4 flex justify-end gap-2 border-t border-base-content/10 pt-3">
										{#if session.status === 'Confirmed'}
											<button
												class="btn btn-xs btn-primary"
												on:click={() => openCompleteModal(session)}>Complete Session</button
											>
										{/if}
										<button
											class="btn btn-ghost btn-xs text-error"
											on:click={() => cancelSession(session)}>Cancel</button
										>
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</section>

		<!-- Past / Completed Sessions -->
		{#if pastSessions.length > 0}
			<section class="space-y-4">
				<button
					class="btn btn-ghost btn-sm text-base-content/70"
					on:click={() => (showPast = !showPast)}
				>
					{showPast ? '▾' : '▸'} Past &amp; Cancelled Sessions ({pastSessions.length})
				</button>
				{#if showPast}
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						{#each pastSessions as session}
							<div class="card border border-base-content/10 bg-base-100/80 shadow">
								<div class="card-body p-5">
									<div class="flex items-start justify-between">
										<div>
											<h3 class="card-title font-[var(--font-cinzel)]">{session.name}</h3>
											<p class="mt-1 text-xs text-base-content/65">
												📅 {formatSessionDateTime(session.session_date)}
											</p>
										</div>
										<span
											class="badge badge-sm {session.status === 'Completed'
												? 'badge-neutral'
												: 'badge-error'}">{session.status}</span
										>
									</div>

									{#if session.status === 'Completed'}
										{#if session.field_report}
											<div class="mt-4 rounded-xl border border-primary/30 bg-primary/5 p-4">
												<p class="mb-2 text-xs font-bold tracking-widest text-base-content/65 uppercase">
													Dispatch from the Field
												</p>
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
													rows="3"
													placeholder="Write your dispatch from the mission..."
													bind:value={fieldReportDraft[session.id]}
												></textarea>
												<button
													class="btn mt-2 w-full btn-sm btn-primary"
													disabled={!fieldReportDraft[session.id]?.trim() ||
														submittingFieldReport === session.id}
													on:click={() => submitFieldReport(session.id)}
												>
													{submittingFieldReport === session.id
														? 'Submitting...'
														: 'Post to the Board'}
												</button>
											</div>
										{/if}
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

<!-- Propose Mission Modal -->
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
					Date.now() - parseUtcDate(mission.last_run_date).getTime() <
						mission.cooldown_days * 86400000}
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

<!-- Admin: Create / Edit Session Modal -->
<Modal
	show={showSessionModal}
	title={editingSessionId !== null ? 'Edit Session' : 'Schedule New Session'}
	onClose={() => (showSessionModal = false)}
>
	<div class="space-y-4">
		<div>
			<label class="label" for="session-title"><span class="label-text">Session Title</span></label>
			<input
				id="session-title"
				type="text"
				bind:value={sName}
				placeholder="e.g., Expedition: The Outer Reach"
				class="input-bordered input w-full"
			/>
		</div>
		<div class="grid grid-cols-2 gap-4">
			<div>
				<label class="label" for="session-min"><span class="label-text">Min Players</span></label>
				<input id="session-min" type="number" bind:value={sMinPlayers} class="input-bordered input w-full" />
			</div>
			<div>
				<label class="label" for="session-max"><span class="label-text">Max Players</span></label>
				<input id="session-max" type="number" bind:value={sMaxPlayers} class="input-bordered input w-full" />
			</div>
		</div>
		<div>
			<label class="label" for="session-date"><span class="label-text">Date and Time (Local)</span></label>
			<input id="session-date" type="datetime-local" bind:value={sDate} class="input-bordered input w-full" />
		</div>
		{#if editingSessionId !== null}
			<div>
				<label class="label" for="session-status"><span class="label-text">Status</span></label>
				<select id="session-status" bind:value={sStatus} class="select-bordered select w-full">
					<option value="Open">Open</option>
					<option value="Proposed">Proposed</option>
					<option value="Confirmed">Confirmed</option>
					<option value="Cancelled">Cancelled</option>
				</select>
			</div>
		{/if}
		<div>
			<label class="label" for="session-desc"><span class="label-text">Briefing</span></label>
			<textarea
				id="session-desc"
				bind:value={sDescription}
				class="textarea-bordered textarea h-24 w-full"
				placeholder="Session notes, meeting point, or requirements..."
			></textarea>
		</div>
	</div>
	<div slot="action">
		<button class="btn w-full btn-primary" on:click={saveSession} disabled={savingSession}>
			{savingSession ? 'Saving...' : editingSessionId !== null ? 'Save Changes' : 'Create Session'}
		</button>
	</div>
</Modal>

<!-- Admin: Complete Session Modal -->
<Modal
	show={showCompleteModal}
	title="Complete Session"
	onClose={() => (showCompleteModal = false)}
>
	{#if completingSession}
		<div class="space-y-4">
			<div>
				<span class="label-text font-semibold">Mission Result</span>
				<div class="mt-2 flex gap-4">
					<label class="flex cursor-pointer items-center gap-2">
						<input type="radio" bind:group={cResult} value="success" class="radio radio-success" />
						<span>Success</span>
					</label>
					<label class="flex cursor-pointer items-center gap-2">
						<input type="radio" bind:group={cResult} value="failure" class="radio radio-error" />
						<span>Failure</span>
					</label>
				</div>
			</div>
			<div>
				<label class="label" for="complete-essence"
					><span class="label-text">⚡ Essence Earned (net, after transit)</span></label
				>
				<input
					id="complete-essence"
					type="number"
					bind:value={cEssenceEarned}
					class="input-bordered input w-full"
					placeholder="0"
				/>
			</div>
			{#if completingSession.players.length > 0}
				<div>
					<span class="label-text">💀 Casualties (mark as Dead)</span>
					<div class="mt-2 flex flex-wrap gap-2">
						{#each completingSession.players as player}
							<label class="flex cursor-pointer items-center gap-1 rounded border border-base-content/20 px-2 py-1 text-xs">
								<input
									type="checkbox"
									checked={cCasualties.includes(player.id)}
									on:change={() => toggleCasualty(player.id)}
									class="checkbox checkbox-xs checkbox-error"
								/>
								<span>{player.name}</span>
							</label>
						{/each}
					</div>
				</div>
			{/if}
			<div>
				<label class="label" for="complete-aar"
					><span class="label-text">After-Action Report (optional)</span></label
				>
				<textarea
					id="complete-aar"
					bind:value={cAfterAction}
					class="textarea-bordered textarea h-24 w-full"
					placeholder="What happened on this expedition..."
				></textarea>
			</div>
		</div>
	{/if}
	<div slot="action">
		<button class="btn w-full btn-primary" on:click={submitComplete} disabled={completing}>
			{completing ? 'Completing...' : 'Record Outcome'}
		</button>
	</div>
</Modal>
