<script lang="ts">
	import { onMount } from 'svelte';
	import type { Character, GameSessionWithPlayers, Mission } from '$lib/types';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import { MISSIONS_NAV } from '$lib/navigation';
	import SubNav from '$lib/components/SubNav.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SessionCard from '$lib/components/SessionCard.svelte';
	import ProposeModal from '$lib/components/ProposeModal.svelte';
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';

	let sessions: GameSessionWithPlayers[] = [];
	let availableMissions: Mission[] = [];
	let discoveredHexes: { id: number; q: number; r: number; terrain: string; linked_location_name?: string }[] = [];
	let myCharacters: Character[] = [];
	let error: string | null = null;
	let viewFilter: 'upcoming' | 'completed' = 'upcoming';

	let showProposeModal = false;
	let proposeSessionId: number | null = null;

	// Field report state
	let fieldReportDraft: Record<number, string> = {};
	let submittingFieldReport: number | null = null;

	$: userId = $auth.user?.id;
	$: myCharacterId = $auth.user?.active_character?.id;

	onMount(loadAll);

	async function loadAll() {
		error = null;
		const [sessRes, missRes, charRes, mapRes] = await Promise.all([
			api('GET', '/sessions/').catch((e) => {
				error = e instanceof Error ? e.message : 'Failed to fetch sessions';
				return [];
			}),
			api('GET', '/missions/').catch(() => []),
			api('GET', '/characters/').catch(() => []),
			api('GET', '/maps/').catch(() => [])
		]);
		sessions = sessRes ?? [];
		availableMissions = (missRes ?? []).filter((m: Mission) => !m.is_retired && m.is_discoverable);
		myCharacters = charRes ?? [];
		discoveredHexes = (mapRes ?? []).flatMap((m: any) => (m.hexes ?? []).filter((h: any) => h.is_discovered));
	}

	function isParticipant(session: GameSessionWithPlayers): boolean {
		return session.players.some((p) => p.owner_id === userId);
	}

	async function submitFieldReport(sessionId: number) {
		const text = fieldReportDraft[sessionId];
		if (!text?.trim()) return;
		submittingFieldReport = sessionId;
		error = null;
		try {
			await api('PATCH', `/sessions/${sessionId}/field-report`, { field_report: text });
			fieldReportDraft[sessionId] = '';
			await loadAll();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			submittingFieldReport = null;
		}
	}

	function openPropose(sessionId: number) {
		proposeSessionId = sessionId;
		showProposeModal = true;
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
		subtitle="Claim a seat for upcoming sessions, vote on quests or hexes, and read past recaps."
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
				Past Recaps &amp; AARs
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
	{:else if viewFilter === 'upcoming'}
		<div class="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
			{#each filteredSessions as session}
				<SessionCard
					{session}
					{userId}
					activeCharacterId={myCharacterId}
					{myCharacters}
					onRefresh={loadAll}
					onOpenPropose={openPropose}
					onError={(msg) => (error = msg)}
				/>
			{/each}
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
						<span class="badge badge-sm {session.result === 'success' ? 'badge-success' : 'badge-error'}">
							{session.result === 'success' ? 'Victory' : 'Defeat'}
						</span>
					</div>

					{#if session.confirmed_mission}
						<p class="mb-2 text-xs font-medium text-primary">Quest: {session.confirmed_mission.name}</p>
					{:else if session.confirmed_hex}
						<p class="mb-2 text-xs font-medium text-primary">
							Hex ({session.confirmed_hex.q}, {session.confirmed_hex.r}){#if session.confirmed_hex.linked_location_name} — {session.confirmed_hex.linked_location_name}{/if}
						</p>
					{/if}

					{#if session.players.length > 0}
						<div class="mb-3 flex flex-wrap gap-1">
							{#each session.players as p}
								<span class="rounded bg-base-300 px-1.5 py-0.5 text-[11px] text-base-content/80">{p.name}</span>
							{/each}
						</div>
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
					{:else if isParticipant(session)}
						<div class="mt-auto border-t border-base-content/10 pt-3">
							<label for="fr-{session.id}" class="section-label mb-1.5 block">
								File a Field Report
							</label>
							<textarea
								id="fr-{session.id}"
								class="textarea textarea-bordered w-full text-xs"
								rows="3"
								placeholder="Write your party's dispatch from this session..."
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
				</article>
			{/each}
		</div>
	{/if}
</div>

<ProposeModal
	bind:open={showProposeModal}
	sessionId={proposeSessionId}
	missions={availableMissions}
	hexes={discoveredHexes}
	onSuccess={loadAll}
	onError={(msg) => (error = msg)}
/>
