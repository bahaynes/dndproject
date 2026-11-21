<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { API_BASE_URL } from '$lib/config';

	// Exchange the HttpOnly oauth_exchange cookie via POST so tokens never travel in URLs.
	// Must use window.location (not goto) because adapter-static serves a pre-rendered
	// shell and SvelteKit's router isn't ready for goto() on first load.
	onMount(async () => {
		if (!browser) return;

		try {
			const res = await fetch(`${API_BASE_URL}/auth/exchange`, {
				method: 'POST',
				credentials: 'include'
			});

			if (res.ok) {
				const data = await res.json();
				if (data?.token && data?.discord_token) {
					sessionStorage.setItem('pendingToken', data.token);
					sessionStorage.setItem('pendingDiscordToken', data.discord_token);
					window.location.replace('/campaigns');
					return;
				}
			}
		} catch {
			// Fall through to /login on exchange error
		}

		window.location.replace('/login');
	});
</script>

<div class="flex min-h-screen items-center justify-center">
	<p class="text-xl">Redirecting...</p>
</div>
