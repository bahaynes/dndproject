<script lang="ts">
	import '../app.css';
	import { auth, login, logout } from '$lib/auth';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { API_BASE_URL } from '$lib/config';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';

	// Rehydrate auth from localStorage on every page load.
	// Only ever looks at accessToken — nothing else.
	onMount(async () => {
		if (!browser) return;

		const token = localStorage.getItem('accessToken');
		if (!token || $auth.isAuthenticated) return;

		try {
			const controller = new AbortController();
			const timer = setTimeout(() => controller.abort(), 8000);
			const response = await fetch(`${API_BASE_URL}/auth/me`, {
				headers: { Authorization: `Bearer ${token}` },
				signal: controller.signal
			});
			clearTimeout(timer);

			if (response.ok) {
				const user = await response.json();
				login(user, token, user.campaign);
			} else {
				localStorage.removeItem('accessToken');
			}
		} catch (e) {
			console.error('Auth rehydration failed', e);
			localStorage.removeItem('accessToken');
		}
	});

	function handleLogout() {
		logout();
		if (browser) goto('/login');
	}
</script>

<div class="flex min-h-screen flex-col">
	<nav class="navbar border-b border-base-content/10 bg-base-300 shadow-lg">
		<div class="navbar-start">
			<div class="dropdown">
				<button tabindex="0" class="btn btn-ghost lg:hidden" aria-label="Mobile Menu">
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
					class="dropdown-content menu z-[1] mt-3 w-52 menu-sm rounded-box border border-base-content/10 bg-base-200 p-2 shadow"
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
			<a href="/" class="btn text-xl font-[var(--font-cinzel)] tracking-wider btn-ghost"
				>DnD Westmarches</a
			>
		</div>

		<div class="navbar-center hidden lg:flex">
			<ul class="menu menu-horizontal gap-2 px-1">
				{#if $auth.isAuthenticated}
					<li><a href="/dashboard" class="font-semibold">Dashboard</a></li>
					<li><a href="/maps" class="font-semibold">World Map</a></li>
					<li><a href="/factions" class="font-semibold">Factions</a></li>
					<li><a href="/campaigns" class="font-semibold">Switch Campaign</a></li>
				{/if}
			</ul>
		</div>

		<div class="navbar-end gap-2">
			{#if $auth.isAuthenticated}
				<div class="flex items-center gap-3">
					{#if $auth.campaign}
						<div class="badge hidden badge-outline px-3 py-3 font-bold badge-primary md:flex">
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
							class="btn avatar btn-circle overflow-hidden border border-primary/20 btn-ghost"
							aria-label="User Menu"
						>
							<div class="w-10 rounded-full">
								{#if $auth.user?.avatar_url}
									<img alt="Avatar" src={$auth.user.avatar_url} />
								{:else}
									<div
										class="flex h-full items-center justify-center bg-primary text-xl font-bold text-primary-content"
									>
										{$auth.user?.username?.charAt(0).toUpperCase()}
									</div>
								{/if}
							</div>
						</button>
						<ul
							class="dropdown-content menu z-[1] mt-3 w-52 menu-sm rounded-box border border-base-content/10 bg-base-200 p-2 shadow"
						>
							<li class="menu-title text-xs md:hidden">{$auth.user?.username}</li>
							<li><a href="/dashboard" class="justify-between font-semibold">Dashboard</a></li>
							<li><a href="/campaigns">Switch Campaign</a></li>
							<li><hr class="my-1 border-base-content/10" /></li>
							<li><button on:click={handleLogout} class="font-bold text-error">Logout</button></li>
						</ul>
					</div>
				</div>
			{:else}
				<a href="/login" class="btn px-6 btn-sm btn-primary">Login</a>
			{/if}
			<div class="ml-2">
				<ThemeSwitcher />
			</div>
		</div>
	</nav>

	<main class="flex-grow bg-base-100">
		<slot />
	</main>
</div>
