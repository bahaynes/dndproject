<script lang="ts">
	import { onMount } from 'svelte';
	import type { GameSessionWithPlayers, Mission } from '../../lib/types';
	import { auth } from '../../lib/auth';
	import { get } from 'svelte/store';
	import { API_BASE_URL } from '$lib/config';
	import Modal from '$lib/components/Modal.svelte';

	let sessions: GameSessionWithPlayers[] = [];
	let availableMissions: Mission[] = [];
	let error: string | null = null;
	let myCharacterId: number | undefined;

	let showProposeModal = false;
	let selectedSessionId: number | null = null;
	let selectedMissionId: number | null = null;

	onMount(async () => {
		const authState = get(auth);
		myCharacterId = authState.user?.character?.id;
		await Promise.all([fetchSessions(), fetchMissions()]);
	});

	async function fetchSessions() {
		error = null;
		try {
			const token = get(auth).token;
			if (!token) {
				throw new Error('Not authenticated. Please log in.');
			}
			const response = await fetch(`${API_BASE_URL}/sessions/`, {
				headers: {
					Authorization: `Bearer ${token}`
				}
			});
			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to fetch sessions');
			}
			sessions = await response.json();
		} catch (err) {
			if (err instanceof Error) {
				error = err.message;
			} else {
				error = 'An unknown error occurred';
			}
		}
	}

	async function fetchMissions() {
		try {
			const res = await fetch(`${API_BASE_URL}/missions/`, {
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) availableMissions = await res.json();
		} catch (e) {}
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
		const token = get(auth).token;
		if (!token) {
			error = 'You must be logged in.';
			return;
		}

		try {
			const response = await fetch(`${API_BASE_URL}/sessions/proposals/${proposalId}/toggle_back`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${token}`
				}
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to update backing');
			}

			await fetchSessions();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		}
	}

	async function proposeMission() {
		if (!selectedSessionId || !selectedMissionId) return;
		error = null;
		const token = get(auth).token;

		try {
			const response = await fetch(`${API_BASE_URL}/sessions/proposals`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: JSON.stringify({
					session_id: selectedSessionId,
					mission_id: selectedMissionId
				})
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to propose mission');
			}

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
		<div class="alert alert-error my-4">
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
				<div class="card bg-base-100 border-base-content/10 border shadow-xl">
					<div class="card-body">
						<div class="flex items-start justify-between">
							<h2 class="card-title text-primary">{session.name}</h2>
							<div class="badge {session.status === 'Confirmed' ? 'badge-success' : 'badge-info'}">
								{session.status}
							</div>
						</div>

						<p class="text-sm opacity-70">{session.description || 'No description.'}</p>
						<div class="bg-base-200 my-2 rounded p-2 text-sm">
							<span class="font-bold">📅 Date:</span>
							{new Date(session.session_date).toLocaleString()}
						</div>

						{#if session.status === 'Confirmed' && session.confirmed_mission}
							<div class="bg-success/10 border-success/20 mt-4 rounded-xl border p-4">
								<h3 class="text-success font-bold">Confirmed Content</h3>
								<p class="text-lg font-[var(--font-cinzel)]">{session.confirmed_mission.name}</p>
								{#if session.confirmed_mission.tier}
									<div class="badge badge-sm badge-outline mt-1">
										{session.confirmed_mission.tier}
									</div>
								{/if}
								<div class="mt-4">
									<span class="text-xs font-bold uppercase opacity-50">Heroes Confirmed</span>
									<div class="mt-1 flex flex-wrap gap-1">
										{#each session.players as player}
											<div class="badge badge-sm badge-ghost">{player.name}</div>
										{/each}
									</div>
								</div>
							</div>
						{:else}
							<div class="mt-4">
								<div class="mb-2 flex items-center justify-between">
									<h3 class="text-xs font-bold uppercase opacity-50">Proposals</h3>
									{#if session.status !== 'Completed' && session.status !== 'Cancelled'}
										<button
											class="btn btn-xs btn-ghost"
											on:click={() => {
												selectedSessionId = session.id;
												showProposeModal = true;
											}}>+ Propose</button
										>
									{/if}
								</div>

								{#each session.proposals as proposal}
									<div class="bg-base-200/50 border-base-content/5 mb-4 rounded-xl border p-3">
										<div class="flex items-center justify-between">
											<span class="font-bold">{proposal.mission.name}</span>
											<span class="text-xs">{proposal.backers.length} / {session.min_players}</span>
										</div>

										<progress
											class="progress progress-primary mt-2 w-full"
											value={proposal.backers.length}
											max={session.min_players}
										></progress>

										<div class="mt-3 flex items-center justify-between">
											<div class="flex -space-x-2">
												{#each proposal.backers as backer}
													<div class="avatar placeholder">
														<div
															class="bg-neutral text-neutral-content border-base-100 h-6 w-6 rounded-full border-2"
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
									<div class="py-4 text-center text-xs italic opacity-50">
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
			class="select select-bordered w-full"
		>
			<option value={null}>-- Pick a Mission --</option>
			{#each availableMissions as mission}
				{@const inCooldown =
					mission.last_run_date &&
					new Date().getTime() - new Date(mission.last_run_date).getTime() <
						mission.cooldown_days * 24 * 60 * 60 * 1000}
				<option value={mission.id} disabled={inCooldown}>
					{mission.name} ({mission.tier || 'No Tier'}) {inCooldown ? '- ❄️ Cooldown' : ''}
				</option>
			{/each}
		</select>
		<p class="mt-4 text-sm italic opacity-70">
			Proposing will add you as the first backer. When a proposal hits {sessions.find(
				(s) => s.id === selectedSessionId
			)?.min_players || 4} backers, the session is locked.
		</p>
	</div>
	<div slot="action">
		<button class="btn btn-primary w-full" on:click={proposeMission} disabled={!selectedMissionId}
			>Propose Now</button
		>
	</div>
</Modal>
