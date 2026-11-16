<script lang="ts">
	import '../app.css';
	import { auth, login, logout } from '$lib/auth';
	import { browser } from '$app/environment';
	import { goto, afterNavigate } from '$app/navigation';
	import { onMount } from 'svelte';
	import { API_BASE_URL } from '$lib/config';
	import { page } from '$app/stores';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';

	let navEl: HTMLElement | null = null;

	$: currentPath = $page?.url?.pathname ?? '/';

	function isActive(path: string, exact = false): boolean {
		if (exact) return currentPath === path;
		return currentPath === path || currentPath.startsWith(path + '/');
	}

	function closeMenus() {
		if (!browser) return;
		navEl?.querySelectorAll('details[open]').forEach((el) => el.removeAttribute('open'));
		if (document.activeElement instanceof HTMLElement) {
			document.activeElement.blur();
		}
	}

	afterNavigate(() => {
		closeMenus();
	});

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
		closeMenus();
		logout();
		if (browser) goto('/login');
	}
</script>

<div class="flex min-h-screen flex-col">
	<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
	<nav
		bind:this={navEl}
		on:click={(e) => {
			if (e.target instanceof Element && e.target.closest('a')) {
				closeMenus();
			}
		}}
		class="navbar sticky top-0 z-30 border-b border-base-content/10 bg-base-300 shadow-lg"
	>
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
					class="dropdown-content menu z-50 mt-3 w-60 menu-sm rounded-box border border-base-content/10 bg-base-200 p-2 shadow-xl"
				>
					{#if $auth.isAuthenticated}
						<li class="menu-title text-[10px] uppercase opacity-60">Play</li>
						<li><a href="/dashboard" class:active={isActive('/dashboard', true)}>Dashboard</a></li>
						<li><a href="/sessions" class:active={isActive('/sessions')}>Sessions</a></li>
						<li><a href="/missions" class:active={isActive('/missions')}>Missions</a></li>
						<li><a href="/maps" class:active={isActive('/maps')}>World Map</a></li>
						<li class="menu-title mt-1 text-[10px] uppercase opacity-60">Crew &amp; World</li>
						<li><a href="/characters" class:active={isActive('/characters', true)}>Character</a></li>
						<li><a href="/characters/inventory" class:active={isActive('/characters/inventory')}>Inventory</a></li>
						<li><a href="/store" class:active={isActive('/store')}>Store</a></li>
						<li><a href="/factions" class:active={isActive('/factions')}>Factions</a></li>
						<li><a href="/roster" class:active={isActive('/roster')}>Roster</a></li>
						<li><a href="/ledger" class:active={isActive('/ledger')}>Ledger</a></li>
						{#if $auth.user?.role === 'admin'}
							<li class="menu-title mt-1 text-[10px] uppercase opacity-60">DM Tools</li>
							<li><a href="/admin/sessions" class:active={isActive('/admin/sessions')}>Manage Sessions</a></li>
							<li><a href="/admin/missions" class:active={isActive('/admin/missions')}>Manage Missions</a></li>
							<li><a href="/admin/maps" class:active={isActive('/admin/maps')}>Manage Maps</a></li>
							<li><a href="/admin/items" class:active={isActive('/admin/items')}>Manage Items</a></li>
							<li><a href="/admin/ship" class:active={isActive('/admin/ship')}>Ship Config</a></li>
						{/if}
						<li><hr class="my-1 opacity-10" /></li>
						<li><a href="/campaigns" class:active={isActive('/campaigns')}>Switch Campaign</a></li>
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
			<ul class="menu menu-horizontal items-center gap-1 px-1">
				{#if $auth.isAuthenticated}
					<li>
						<a
							href="/dashboard"
							class="font-semibold {isActive('/dashboard', true) ? 'bg-primary/15 text-primary' : ''}"
							>Dashboard</a
						>
					</li>
					<li>
						<a
							href="/sessions"
							class="font-semibold {isActive('/sessions') ? 'bg-primary/15 text-primary' : ''}"
							>Sessions</a
						>
					</li>
					<li>
						<a
							href="/missions"
							class="font-semibold {isActive('/missions') ? 'bg-primary/15 text-primary' : ''}"
							>Missions</a
						>
					</li>
					<li>
						<a
							href="/maps"
							class="font-semibold {isActive('/maps') ? 'bg-primary/15 text-primary' : ''}"
							>World Map</a
						>
					</li>
					<li>
						<details>
							<summary
								class="font-semibold"
								class:text-primary={isActive('/characters') ||
									isActive('/store') ||
									isActive('/factions') ||
									isActive('/roster') ||
									isActive('/ledger')}>Crew &amp; World</summary
							>
							<ul class="z-50 w-44 rounded-box border border-base-content/10 bg-base-200 p-2 shadow-xl">
								<li><a href="/characters" class:active={isActive('/characters', true)}>Character</a></li>
								<li><a href="/characters/inventory" class:active={isActive('/characters/inventory')}>Inventory</a></li>
								<li><a href="/store" class:active={isActive('/store')}>Store</a></li>
								<li><a href="/factions" class:active={isActive('/factions')}>Factions</a></li>
								<li><a href="/roster" class:active={isActive('/roster')}>Roster</a></li>
								<li><a href="/ledger" class:active={isActive('/ledger')}>Ledger</a></li>
							</ul>
						</details>
					</li>
					{#if $auth.user?.role === 'admin'}
						<li>
							<details>
								<summary class="font-semibold" class:text-primary={isActive('/admin')}>DM Tools</summary>
								<ul class="z-50 w-44 rounded-box border border-base-content/10 bg-base-200 p-2 shadow-xl">
									<li><a href="/admin/sessions" class:active={isActive('/admin/sessions')}>Manage Sessions</a></li>
									<li><a href="/admin/missions" class:active={isActive('/admin/missions')}>Manage Missions</a></li>
									<li><a href="/admin/maps" class:active={isActive('/admin/maps')}>Manage Maps</a></li>
									<li><a href="/admin/items" class:active={isActive('/admin/items')}>Manage Items</a></li>
									<li><a href="/admin/ship" class:active={isActive('/admin/ship')}>Ship Config</a></li>
								</ul>
							</details>
						</li>
					{/if}
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
