<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';

	// No network calls. Stash the OAuth tokens and hard-redirect to /campaigns.
	// Must use window.location (not goto) because adapter-static serves a pre-rendered
	// shell and SvelteKit's router isn't ready for goto() on first load.
	onMount(() => {
		if (!browser) return;

		const params = new URLSearchParams(window.location.search);
		const token = params.get('token');
		const discordToken = params.get('discord_token');

		if (token && discordToken) {
			localStorage.setItem('pendingToken', token);
			localStorage.setItem('pendingDiscordToken', discordToken);
			window.location.replace('/campaigns');
		} else {
			window.location.replace('/login');
		}
	});
</script>

<div class="flex min-h-screen items-center justify-center">
	<p class="text-xl">Redirecting...</p>
</div>
