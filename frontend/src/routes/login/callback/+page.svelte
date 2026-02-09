<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { auth } from '$lib/auth';
	import { browser } from '$app/environment';

	onMount(async () => {
		if (browser) {
			const token = $page.url.searchParams.get('token');
			const discordToken = $page.url.searchParams.get('discord_token');

			if (token && discordToken) {
				localStorage.setItem('tempGlobalToken', token);
				localStorage.setItem('tempDiscordToken', discordToken);

				// Fetch Global User Info immediately to update Store
				try {
					const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/auth/me/global`, {
						headers: { Authorization: `Bearer ${token}` }
					});
					if (response.ok) {
						const globalUser = await response.json();
						// Import globalLogin dynamically or use the one from $lib/auth
						// We imported auth, need to import globalLogin
						// For now, rely on module import
						const { globalLogin } = await import('$lib/auth');
						globalLogin(globalUser, token);
					}
				} catch (e) {
					console.error('Failed to fetch global profile in callback', e);
				}

				const next = $page.url.searchParams.get('next');
				goto(next || '/campaigns');
			} else {
				goto('/login');
			}
		}
	});
</script>

<div class="flex min-h-screen items-center justify-center">
	<p class="text-xl">Authenticating...</p>
</div>
