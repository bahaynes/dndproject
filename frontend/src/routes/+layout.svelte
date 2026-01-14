<script lang="ts">
	import '../app.css';
	import { auth, login, logout } from '$lib/auth';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { API_BASE_URL } from '$lib/config';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';

	onMount(async () => {
		if (browser) {
			const token = localStorage.getItem('accessToken');
			const currentAuth = get(auth);

			if (token && !currentAuth.isAuthenticated) {
				try {
					// Check if token is valid and get user info
					const response = await fetch(`${API_BASE_URL}/auth/me`, {
						headers: { Authorization: `Bearer ${token}` }
					});
					if (response.ok) {
						const user = await response.json();
						// We assume if /auth/me succeeds with a campaign-scoped token,
						// the user object has campaign info or we can fetch it.
						// My User model in backend has `campaign` relationship.
						login(user, token, user.campaign);
					} else {
						// Token is invalid
						handleLogout();
					}
				} catch (e) {
					console.error('Failed to fetch user profile', e);
					handleLogout();
				}
			}
		}
	});

	function handleLogout() {
		logout();
		if (browser) {
			localStorage.removeItem('accessToken');
			goto('/login');
		}
	}
</script>

<div class="flex min-h-screen flex-col">
	<nav class="navbar bg-base-300 border-base-content/10 border-b shadow-lg">
		<div class="navbar-start">
			<div class="dropdown">
				<button tabindex="0" class="btn btn-ghost lg:hidden">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 6h16M4 12h8m-8 6h16"
						/></svg
					>
				</button>
				<ul
					class="menu menu-sm dropdown-content bg-base-200 rounded-box border-base-content/10 z-[1] mt-3 w-52 border p-2 shadow"
				>
					{#if $auth.isAuthenticated}
						<li><a href="/dashboard">Dashboard</a></li>
						<li><a href="/campaigns">Switch Campaign</a></li>
						<li><hr class="my-1 opacity-10" /></li>
						<li><button on:click={handleLogout} class="text-error">Logout</button></li>
					{:else}
						<li><a href="/login">Login</a></li>
					{/if}
				</ul>
			</div>
			<a href="/" class="btn btn-ghost text-xl font-[var(--font-cinzel)] tracking-wider"
				>DnD Westmarches</a
			>
		</div>

		<div class="navbar-center hidden lg:flex">
			<ul class="menu menu-horizontal gap-2 px-1">
				{#if $auth.isAuthenticated}
					<li><a href="/dashboard" class="font-semibold">Dashboard</a></li>
					<li><a href="/maps" class="font-semibold">World Map</a></li>
					<li><a href="/campaigns" class="font-semibold">Switch Campaign</a></li>
				{/if}
			</ul>
		</div>

		<div class="navbar-end gap-2">
			{#if $auth.isAuthenticated}
				<div class="flex items-center gap-3">
					{#if $auth.campaign}
						<div class="badge badge-outline badge-primary hidden px-3 py-3 font-bold md:flex">
							{$auth.campaign.name}
						</div>
					{/if}

					<div class="hidden flex-col items-end leading-tight md:flex">
						<span class="text-[10px] font-bold uppercase opacity-50">Logged in as</span>
						<span class="text-sm font-bold">{$auth.user?.username}</span>
					</div>

					<div class="dropdown dropdown-end">
						<button
							tabindex="0"
							class="btn btn-ghost btn-circle avatar border-primary/20 overflow-hidden border"
						>
							<div class="w-10 rounded-full">
								{#if $auth.user?.avatar_url}
									<img alt="Avatar" src={$auth.user.avatar_url} />
								{:else}
									<div
										class="bg-primary text-primary-content flex h-full items-center justify-center text-xl font-bold"
									>
										{$auth.user?.username?.charAt(0).toUpperCase()}
									</div>
								{/if}
							</div>
						</button>
						<ul
							class="menu menu-sm dropdown-content bg-base-200 rounded-box border-base-content/10 z-[1] mt-3 w-52 border p-2 shadow"
						>
							<li class="menu-title text-xs md:hidden">{$auth.user?.username}</li>
							<li><a href="/dashboard" class="justify-between font-semibold">Dashboard</a></li>
							<li><a href="/campaigns">Switch Campaign</a></li>
							<li><hr class="border-base-content/10 my-1" /></li>
							<li><button on:click={handleLogout} class="text-error font-bold">Logout</button></li>
						</ul>
					</div>
				</div>
			{:else}
				<a href="/login" class="btn btn-primary btn-sm px-6">Login</a>
			{/if}
			<div class="ml-2">
				<ThemeSwitcher />
			</div>
		</div>
	</nav>

	<main class="bg-base-100 flex-grow">
		<slot />
	</main>
</div>
