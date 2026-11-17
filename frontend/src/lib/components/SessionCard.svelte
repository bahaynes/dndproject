<script lang="ts">
	import { api } from '$lib/api';
	import type { Character, GameSessionWithPlayers, SessionProposal } from '$lib/types';

	export let session: GameSessionWithPlayers;
	export let userId: number | undefined = undefined;
	export let activeCharacterId: number | undefined = undefined;
	export let myCharacters: Character[] = [];
	export let onRefresh: () => Promise<void> | void = () => {};
	export let onOpenPropose: ((sessionId: number) => void) | null = null;
	export let onError: (msg: string) => void = () => {};

	let busy = false;

	$: mySeatedChar = session.players.find((p) => p.owner_id === userId) ?? null;
	$: activeChoices = myCharacters.filter((c) => c.status === 'Active');
	$: isFull = session.players.length >= session.max_players;
	$: activeProposals = session.proposals.filter((p) => p.status !== 'vetoed');

	function formatDate(iso: string) {
		return new Date(iso).toLocaleDateString(undefined, {
			weekday: 'short',
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	}

	function proposalTitle(p: SessionProposal): string {
		if (p.mission) return p.mission.name;
		if (p.hex) {
			const loc = p.hex.linked_location_name ? ` — ${p.hex.linked_location_name}` : '';
			return `Explore Hex (${p.hex.q}, ${p.hex.r})${loc}`;
		}
		return 'Custom Destination';
	}

	function isVoting(p: SessionProposal): boolean {
		if (!mySeatedChar) return false;
		return p.backers.some((b) => b.id === mySeatedChar.id);
	}

	async function joinSession() {
		busy = true;
		try {
			await api('POST', `/sessions/${session.id}/signup`);
			await onRefresh();
		} catch (e) {
			onError(e instanceof Error ? e.message : 'Failed to join session.');
		} finally {
			busy = false;
		}
	}

	async function leaveSession() {
		busy = true;
		try {
			await api('DELETE', `/sessions/${session.id}/signup`);
			await onRefresh();
		} catch (e) {
			onError(e instanceof Error ? e.message : 'Failed to leave session.');
		} finally {
			busy = false;
		}
	}

	async function swapCharacter(e: Event) {
		const target = e.currentTarget as HTMLSelectElement;
		const charId = Number(target.value);
		if (!charId || charId === mySeatedChar?.id) return;
		busy = true;
		try {
			await api('POST', `/sessions/${session.id}/swap-character`, { character_id: charId });
			await onRefresh();
		} catch (err) {
			onError(err instanceof Error ? err.message : 'Failed to swap character.');
			if (mySeatedChar) target.value = String(mySeatedChar.id);
		} finally {
			busy = false;
		}
	}

	async function toggleVote(proposalId: number) {
		busy = true;
		try {
			await api('POST', `/sessions/proposals/${proposalId}/toggle_back`);
			await onRefresh();
		} catch (e) {
			onError(e instanceof Error ? e.message : 'Failed to update vote.');
		} finally {
			busy = false;
		}
	}
</script>

<div class="panel flex flex-col p-5">
	<div class="mb-3 flex items-start justify-between gap-3">
		<div class="min-w-0">
			<h3 class="text-base font-semibold text-base-content">{session.name}</h3>
			<p class="mt-0.5 text-xs text-base-content/65 stat-num">
				{formatDate(session.session_date)} · {session.players.length}/{session.max_players} seats
			</p>
		</div>
		<span
			class="badge badge-sm shrink-0 whitespace-nowrap {session.status === 'Confirmed'
				? 'badge-success'
				: 'badge-outline border-primary/40 text-primary'}"
		>
			{session.status === 'Confirmed' ? 'Quest Locked' : 'Open Seats'}
		</span>
	</div>

	{#if session.description}
		<p class="mb-3 text-xs text-base-content/70">{session.description}</p>
	{/if}

	<!-- Seated Party -->
	<div class="mb-3">
		<p class="section-label mb-1.5">Seated Party ({session.players.length}/{session.max_players})</p>
		{#if session.players.length === 0}
			<p class="text-xs italic text-base-content/45">No one signed up yet — claim the first seat.</p>
		{:else}
			<div class="flex flex-wrap gap-1.5">
				{#each session.players as player}
					<span
						class="rounded px-2 py-0.5 text-xs {player.owner_id === userId
							? 'border border-primary/40 bg-primary/15 text-primary'
							: 'bg-base-300 text-base-content/85'}"
					>
						{player.name}{#if player.level} · L{player.level}{/if}{#if player.class_name} {player.class_name}{/if}
					</span>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Confirmed Destination OR Consensus Poll -->
	{#if session.confirmed_mission || session.confirmed_hex}
		<div class="mb-3 rounded-md border border-success/25 bg-success/5 p-3">
			<p class="section-label text-success">Locked Destination</p>
			<p class="mt-0.5 text-sm font-semibold text-base-content">
				{#if session.confirmed_mission}
					{session.confirmed_mission.name}
				{:else if session.confirmed_hex}
					Hex ({session.confirmed_hex.q}, {session.confirmed_hex.r}){#if session.confirmed_hex.linked_location_name} — {session.confirmed_hex.linked_location_name}{/if}
				{/if}
			</p>
		</div>
	{:else}
		<div class="mb-3 flex-1 space-y-2">
			<div class="flex items-center justify-between">
				<p class="section-label">Quest / Hex Poll (or Decide Night-Of)</p>
				{#if mySeatedChar && onOpenPropose}
					<button
						class="text-xs font-medium text-primary hover:underline"
						disabled={busy}
						on:click={() => onOpenPropose?.(session.id)}
					>
						+ Propose
					</button>
				{/if}
			</div>

			{#if activeProposals.length === 0}
				<p class="rounded-md border border-dashed border-base-content/15 p-2.5 text-xs text-base-content/50">
					No proposals yet — join a seat to propose a quest or hex, or decide at the table.
				</p>
			{:else}
				{#each activeProposals as proposal}
					<div class="flex items-center justify-between gap-2 rounded-md border border-base-content/10 bg-base-300/40 px-3 py-2">
						<div class="min-w-0">
							<p class="truncate text-xs font-medium text-base-content">
								{proposalTitle(proposal)}
							</p>
							<p class="text-[11px] text-base-content/55 stat-num">
								{proposal.backers.length} {proposal.backers.length === 1 ? 'vote' : 'votes'}
								{#if proposal.mission?.tier} · {proposal.mission.tier}{/if}
								{#if proposal.hex} · {proposal.hex.terrain}{/if}
							</p>
						</div>
						{#if mySeatedChar}
							<button
								class="btn btn-xs shrink-0 {isVoting(proposal) ? 'btn-primary' : 'btn-outline'}"
								disabled={busy}
								on:click={() => toggleVote(proposal.id)}
							>
								{isVoting(proposal) ? 'Voted' : 'Vote'}
							</button>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	{/if}

	<!-- Actions: Join / Leave / Swap Character -->
	<div class="mt-auto flex flex-wrap items-center justify-between gap-2 border-t border-base-content/10 pt-3">
		{#if mySeatedChar}
			<div class="flex items-center gap-2">
				{#if activeChoices.length > 1}
					<select
						class="select select-bordered select-sm"
						aria-label="Swap character for this session"
						value={mySeatedChar.id}
						disabled={busy}
						on:change={swapCharacter}
					>
						{#each activeChoices as c}
							<option value={c.id}>{c.name} (L{c.level} {c.class_name ?? ''})</option>
						{/each}
					</select>
				{/if}
			</div>
			<button class="btn btn-outline btn-error btn-xs" disabled={busy} on:click={leaveSession}>
				Leave Seat
			</button>
		{:else if !isFull}
			<span class="text-xs text-base-content/50">
				{#if !activeCharacterId}Create a character to join{:else}Join to vote on quest/hex{/if}
			</span>
			<button
				class="btn btn-primary btn-xs"
				disabled={busy || !activeCharacterId}
				on:click={joinSession}
			>
				I'm Playing ({session.players.length}/{session.max_players})
			</button>
		{:else}
			<span class="text-xs text-base-content/50">Table Full</span>
		{/if}
	</div>
</div>
