<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import type { GameSessionWithPlayers } from '../../lib/types';
	import { auth } from '../../lib/auth';
	import { get } from 'svelte/store';
	import { serverEvents } from '$lib/events';

	let sessions: GameSessionWithPlayers[] = [];
	let error: string | null = null;
	let myCharacterId: number | undefined;

	const unsubscribe = serverEvents.subscribe((event) => {
		if (event && event.type === 'session_update') {
			fetchSessions();
		}
	});

	onMount(async () => {
		const authState = get(auth);
		myCharacterId = authState.user?.character?.id;
		await fetchSessions();
	});

	onDestroy(() => {
		unsubscribe();
	});

	async function fetchSessions() {
		error = null;
		try {
			const token = get(auth).token;
			if (!token) {
				throw new Error('Not authenticated. Please log in.');
			}
			const response = await fetch('/api/sessions/', {
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

	function isSignedUp(session: GameSessionWithPlayers): boolean {
		if (!myCharacterId) return false;
		return session.players.some((p) => p.id === myCharacterId);
	}

	async function toggleSignup(session: GameSessionWithPlayers) {
		error = null;
		const token = get(auth).token;
		if (!token) {
			error = 'You must be logged in to sign up.';
			return;
		}

		const method = isSignedUp(session) ? 'DELETE' : 'POST';
		const url = `/api/sessions/${session.id}/signup`;

		try {
			const response = await fetch(url, {
				method: method,
				headers: {
					Authorization: `Bearer ${token}`
				}
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to update signup status');
			}

			// Refresh the session list to show the change
			await fetchSessions();
		} catch (err) {
			if (err instanceof Error) {
				error = err.message;
			} else {
				error = 'An unknown error occurred';
			}
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
		<div class="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
			{#each sessions as session (session.id)}
				<div class="card bg-base-100 shadow-xl">
					<div class="card-body">
						<h2 class="card-title">{session.name}</h2>
						<p>{session.description}</p>
						<div class="my-2">
							<span class="font-bold">Date:</span>
							{new Date(session.session_date).toLocaleString()}
						</div>
						<div class="my-2">
							<span class="font-bold">Status:</span>
							<span
								class="badge {session.status === 'Completed' ? 'badge-success' : 'badge-info'} ml-2"
								>{session.status}</span
							>
						</div>
						<p><strong>Players ({session.players.length}):</strong></p>
						<ul class="list-inside list-disc">
							{#each session.players as player (player.id)}
								<li>{player.name}</li>
							{/each}
						</ul>
						<div class="card-actions mt-4 justify-end">
							{#if session.status === 'Scheduled'}
								<button
									class="btn {isSignedUp(session) ? 'btn-warning' : 'btn-primary'}"
									on:click={() => toggleSignup(session)}
									disabled={!myCharacterId}
								>
									{isSignedUp(session) ? 'Cancel Signup' : 'Sign Up'}
								</button>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
