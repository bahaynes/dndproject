<script lang="ts">
	import { authedFetch } from '$lib/auth';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';

	let name = '';
	let description = '';
	let sessionDate = '';
	let error: string | null = null;
	let isLoading = false;

	async function handleSubmit() {
		if (!browser) return;
		error = null;
		isLoading = true;

		try {
			const response = await authedFetch('/api/sessions/', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					name,
					description,
					session_date: new Date(sessionDate).toISOString()
				})
			});

			if (response.ok) {
				await goto('/sessions');
			} else {
				const errorData = await response.json();
				error = errorData.detail || 'Failed to create session.';
			}
		} catch (e) {
			console.error(e);
			error = 'An unexpected error occurred.';
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="container mx-auto p-4">
	<h1 class="text-2xl font-bold mb-4">Create New Game Session</h1>

	<form on:submit|preventDefault={handleSubmit} class="max-w-xl bg-white p-6 rounded-lg shadow">
		<div class="mb-4">
			<label for="name" class="block text-gray-700 font-semibold mb-2">Session Name</label>
			<input
				type="text"
				id="name"
				bind:value={name}
				class="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
				required
			/>
		</div>

		<div class="mb-4">
			<label for="description" class="block text-gray-700 font-semibold mb-2"
				>Description</label
			>
			<textarea
				id="description"
				bind:value={description}
				class="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
				rows="4"
			></textarea>
		</div>

		<div class="mb-4">
			<label for="session_date" class="block text-gray-700 font-semibold mb-2"
				>Session Date and Time</label
			>
			<input
				type="datetime-local"
				id="session_date"
				bind:value={sessionDate}
				class="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
				required
			/>
		</div>

		{#if error}
			<p class="text-red-500 mb-4">{error}</p>
		{/if}

		<div class="flex items-center gap-4">
			<button
				type="submit"
				class="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
				disabled={isLoading}
			>
				{#if isLoading}
					Creating...
				{:else}
					Create Session
				{/if}
			</button>
			<a href="/sessions" class="text-gray-600 hover:underline">Cancel</a>
		</div>
	</form>
</div>
