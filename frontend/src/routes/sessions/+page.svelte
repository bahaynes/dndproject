<script lang="ts">
	import type { PageData } from './$types';
	import { auth, authedFetch } from '$lib/auth';
	import { invalidateAll } from '$app/navigation';
	import { browser } from '$app/environment';

	export let data: PageData;

	let isLoading: { [key: number]: boolean } = {};
	let isDeleting: { [key: number]: boolean } = {};

	$: ({ sessions, error } = data);
	$: isAdmin = $auth.user?.role === 'admin';
	$: userCharacterId = $auth.user?.character?.id;

	function isUserSignedUp(session) {
		if (!userCharacterId) return false;
		return session.players.some((p) => p.id === userCharacterId);
	}

	async function handleSignUp(sessionId: number) {
		isLoading = { ...isLoading, [sessionId]: true };
		try {
			const response = await authedFetch(`/api/sessions/${sessionId}/signup`, {
				method: 'POST'
			});
			if (response.ok) {
				await invalidateAll(); // Refreshes the page data
			} else {
				const errorData = await response.json();
				alert(`Error signing up: ${errorData.detail}`);
			}
		} catch (e) {
			alert('An unexpected error occurred during sign-up.');
			console.error(e);
		} finally {
			isLoading = { ...isLoading, [sessionId]: false };
		}
	}

	async function handleCancelSignUp(sessionId: number) {
		isLoading = { ...isLoading, [sessionId]: true };
		try {
			const response = await authedFetch(`/api/sessions/${sessionId}/signup`, {
				method: 'DELETE'
			});
			if (response.ok) {
				await invalidateAll();
			} else {
				const errorData = await response.json();
				alert(`Error cancelling sign-up: ${errorData.detail}`);
			}
		} catch (e) {
			alert('An unexpected error occurred while cancelling sign-up.');
			console.error(e);
		} finally {
			isLoading = { ...isLoading, [sessionId]: false };
		}
	}

	async function handleDelete(sessionId: number) {
		if (!browser) return;
		if (!confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
			return;
		}

		isDeleting = { ...isDeleting, [sessionId]: true };
		try {
			const response = await authedFetch(`/api/sessions/${sessionId}`, {
				method: 'DELETE'
			});
			if (response.ok) {
				await invalidateAll();
			} else {
				const errorData = await response.json();
				alert(`Error deleting session: ${errorData.detail}`);
			}
		} catch (e) {
			alert('An unexpected error occurred while deleting the session.');
			console.error(e);
		} finally {
			isDeleting = { ...isDeleting, [sessionId]: false };
		}
	}
</script>

<div class="container mx-auto p-4">
	<div class="flex justify-between items-center mb-4">
		<h1 class="text-2xl font-bold">Game Sessions</h1>
		{#if isAdmin}
			<a href="/sessions/new" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
				New Session
			</a>
		{/if}
	</div>

	{#if data.error && data.error.includes('unauthorized')}
		<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
			<strong class="font-bold">Unauthorized!</strong>
			<span class="block sm:inline">You do not have permission to perform that action.</span>
		</div>
	{/if}

	{#if error && !data.error.includes('unauthorized')}
		<p class="text-red-500">{error}</p>
	{/if}

	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
		{#each sessions as session (session.id)}
			<div class="border rounded-lg p-4 shadow flex flex-col">
				<div class="flex-grow">
					<h2 class="text-xl font-semibold">{session.name}</h2>
					<p class="text-gray-600">{new Date(session.session_date).toLocaleString()}</p>
					<p class="mt-2 text-gray-700">{session.description || 'No description.'}</p>
					<div class="mt-4">
						<span class="font-semibold">Status:</span>
						<span
							class="px-2 py-1 text-sm rounded
                        {session.status === 'Scheduled' ? 'bg-blue-200 text-blue-800' : ''}
                        {session.status === 'Completed' ? 'bg-green-200 text-green-800' : ''}"
						>
							{session.status}
						</span>
					</div>
					<div class="mt-4">
						<h3 class="font-semibold">Players ({session.players.length})</h3>
						<ul class="list-disc list-inside">
							{#each session.players as player}
								<li>{player.name}</li>
							{:else}
								<li class="text-gray-500">No players signed up yet.</li>
							{/each}
						</ul>
					</div>
				</div>

				<div class="mt-4 pt-4 border-t flex flex-wrap gap-2">
					<!-- Player actions -->
					{#if !isAdmin && session.status === 'Scheduled'}
						{#if isUserSignedUp(session)}
							<button
								on:click={() => handleCancelSignUp(session.id)}
								class="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600 disabled:bg-gray-300"
								disabled={isLoading[session.id]}
							>
								{isLoading[session.id] ? '...' : 'Cancel Signup'}
							</button>
						{:else}
							<button
								on:click={() => handleSignUp(session.id)}
								class="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 disabled:bg-green-300"
								disabled={isLoading[session.id]}
							>
								{isLoading[session.id] ? '...' : 'Sign Up'}
							</button>
						{/if}
					{/if}

					<!-- Admin actions -->
					{#if isAdmin}
						<a
							href="/sessions/{session.id}/edit"
							class="bg-yellow-500 text-white px-3 py-1 rounded text-sm hover:bg-yellow-600"
							>Edit</a
						>
						<button
							on:click={() => handleDelete(session.id)}
							class="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 disabled:bg-red-300"
							disabled={isDeleting[session.id]}
						>
							{isDeleting[session.id] ? '...' : 'Delete'}
						</button>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>
