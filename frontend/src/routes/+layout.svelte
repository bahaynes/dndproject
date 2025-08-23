<script lang="ts">
	import '../app.css';
	import { auth } from '$lib/stores/auth';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let { children } = $props();

	// This function runs when the component mounts on the client
	onMount(async () => {
		if (browser) {
			// If we have a token but no user data, fetch the user's profile
			if ($auth.isAuthenticated && !$auth.user) {
				try {
					const response = await fetch('/api/users/me/', {
						headers: {
							'Authorization': `Bearer ${$auth.token}`
						}
					});
					if (response.ok) {
						const user = await response.json();
						auth.setUser(user);
					} else {
						// If the token is invalid or expired, log the user out
						auth.logout();
						goto('/login');
					}
				} catch (e) {
					console.error("Failed to fetch user profile", e);
					auth.logout();
				}
			}
		}
	});

	function handleLogout() {
		auth.logout();
		goto('/login');
	}
</script>

<header class="bg-gray-800 text-white p-4 shadow-md">
	<nav class="container mx-auto flex justify-between items-center">
		<a href="/" class="text-xl font-bold hover:text-blue-300 transition-colors">DnD Westmarches Hub</a>
		<div class="flex items-center">
			{#if $auth.isAuthenticated}
				{#if $auth.user}
					<span class="px-4">Welcome, {$auth.user.username}</span>
				{/if}
                <a href="/dashboard" class="px-4 hover:underline">Dashboard</a>
				<button onclick={handleLogout} class="px-4 hover:underline">Logout</button>
			{:else}
				<a href="/login" class="px-4 hover:underline">Login</a>
				<a href="/register" class="px-4 hover:underline">Register</a>
			{/if}
		</div>
	</nav>
</header>

<main class="container mx-auto p-4">
	{@render children?.()}
</main>
