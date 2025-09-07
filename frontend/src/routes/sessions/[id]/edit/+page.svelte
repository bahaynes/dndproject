<script lang="ts">
	import { authedFetch } from '$lib/auth';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
    import type { PageData } from './$types';
    import { onMount } from 'svelte';

    export let data: PageData;
    $: ({ session, error: loadError } = data);

	let name = '';
	let description = '';
	let sessionDate = '';
    let status = '';
    let afterActionReport = '';

	let error: string | null = loadError;
	let isLoading = false;

    onMount(() => {
        if (session) {
            name = session.name;
            description = session.description || '';
            status = session.status;
            afterActionReport = session.after_action_report || '';
            // Format the date for the datetime-local input
            const d = new Date(session.session_date);
            // Adjust for timezone offset
            d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
            sessionDate = d.toISOString().slice(0, 16);
        }
    });

	async function handleSubmit() {
		if (!browser || !session) return;
		error = null;
		isLoading = true;

		try {
			const response = await authedFetch(`/api/sessions/${session.id}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					name,
					description,
					session_date: new Date(sessionDate).toISOString(),
                    status,
                    after_action_report: afterActionReport,
				})
			});

			if (response.ok) {
				await goto('/sessions');
			} else {
				const errorData = await response.json();
				error = errorData.detail || 'Failed to update session.';
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
	<h1 class="text-2xl font-bold mb-4">Edit Game Session</h1>

    {#if session}
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

        <div class="mb-4">
            <label for="status" class="block text-gray-700 font-semibold mb-2">Status</label>
            <select id="status" bind:value={status} class="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600">
                <option value="Scheduled">Scheduled</option>
                <option value="Completed">Completed</option>
            </select>
        </div>

        <div class="mb-4">
			<label for="after_action_report" class="block text-gray-700 font-semibold mb-2"
				>After-Action Report</label
			>
			<textarea
				id="after_action_report"
				bind:value={afterActionReport}
				class="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
				rows="6"
                placeholder="Write a summary of what happened in the session..."
			></textarea>
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
					Saving...
				{:else}
					Save Changes
				{/if}
			</button>
			<a href="/sessions" class="text-gray-600 hover:underline">Cancel</a>
		</div>
	</form>
    {:else}
        <p class="text-red-500">Could not load session data. {error || ''}</p>
        <a href="/sessions" class="text-blue-500 hover:underline mt-4 inline-block">Back to sessions</a>
    {/if}
</div>
