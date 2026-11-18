<script lang="ts">
	import '../app.css';
	import { auth, login, logout } from '$lib/auth';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { API_BASE_URL } from '$lib/config';

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

	$: pathname = $page?.url?.pathname ?? '/';

	function isActive(prefixes: string[]): boolean {
		return prefixes.some((p) => pathname === p || pathname.startsWith(p + '/'));
	}
</script>

<div class="flex min-h-screen flex-col bg-base-100 text-base-content">
	<nav class="sticky top-0 z-30 border-b border-base-content/10 bg-base-200/95 backdrop-blur">
		<div class="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
			<!-- Left: Mobile menu + Brand -->
			<div class="flex shrink-0 items-center gap-2">
				<div class="dropdown lg:hidden">
					<button tabindex="0" class="btn btn-ghost btn-sm btn-square" aria-label="Mobile Menu">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 6h16M4 12h8m-8 6h16"
							/>
						</svg>
					</button>
					<ul
						class="dropdown-content menu z-40 mt-2 w-56 rounded-lg border border-base-content/10 bg-base-200 p-2 shadow-lg"
					>
						{#if $auth.isAuthenticated}
							<li><a href="/dashboard" class:active={isActive(['/dashboard'])}>Dashboard</a></li>
							<li><a href="/town" class:active={isActive(['/town'])}>Town</a></li>
							<li><a href="/maps" class:active={isActive(['/maps'])}>World Map</a></li>
							<li><a href="/missions" class:active={isActive(['/missions', '/sessions'])}>Quests &amp; Schedule</a></li>
							<li><a href="/characters" class:active={isActive(['/characters', '/roster'])}>Party</a></li>
							<li><a href="/factions" class:active={isActive(['/factions', '/ledger'])}>Chronicle</a></li>
							<li><a href="/docs" class:active={isActive(['/docs'])}>Guide</a></li>
							{#if $auth.user?.role === 'admin'}
								<li><a href="/admin/sessions" class:active={isActive(['/admin'])}>DM Console</a></li>
							{/if}
							<li><hr class="my-1 border-base-content/10" /></li>
							<li><a href="/campaigns">Switch Campaign</a></li>
							<li><button on:click={handleLogout} class="text-error">Logout</button></li>
						{:else}
							<li><a href="/docs" class:active={isActive(['/docs'])}>Guide</a></li>
						{/if}
					</ul>
				</div>

				<a
					href={$auth.isAuthenticated ? '/dashboard' : '/'}
					class="flex items-center gap-2 whitespace-nowrap font-[var(--font-cinzel)] text-base font-semibold tracking-wider text-primary sm:text-lg"
				>
					West Marches
				</a>
			</div>

			<!-- Center: Primary Workspace Nav (Desktop) -->
			{#if $auth.isAuthenticated}
				<div class="hidden items-center gap-0.5 lg:flex">
					<a
						href="/dashboard"
						class="whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors {isActive(['/dashboard'])
							? 'bg-primary/15 text-primary'
							: 'text-base-content/70 hover:bg-base-300 hover:text-base-content'}"
					>
						Dashboard
					</a>
					<a
						href="/town"
						class="whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors {isActive(['/town'])
							? 'bg-primary/15 text-primary'
							: 'text-base-content/70 hover:bg-base-300 hover:text-base-content'}"
					>
						Town
					</a>
					<a
						href="/maps"
						class="whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors {isActive(['/maps'])
							? 'bg-primary/15 text-primary'
							: 'text-base-content/70 hover:bg-base-300 hover:text-base-content'}"
					>
						World Map
					</a>
					<a
						href="/missions"
						class="whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors {isActive(['/missions', '/sessions'])
							? 'bg-primary/15 text-primary'
							: 'text-base-content/70 hover:bg-base-300 hover:text-base-content'}"
					>
						Quests
					</a>
					<a
						href="/characters"
						class="whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors {isActive(['/characters', '/roster'])
							? 'bg-primary/15 text-primary'
							: 'text-base-content/70 hover:bg-base-300 hover:text-base-content'}"
					>
						Party
					</a>
					<a
						href="/factions"
						class="whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors {isActive(['/factions', '/ledger'])
							? 'bg-primary/15 text-primary'
							: 'text-base-content/70 hover:bg-base-300 hover:text-base-content'}"
					>
						Chronicle
					</a>
					<a
						href="/docs"
						class="whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors {isActive(['/docs'])
							? 'bg-primary/15 text-primary'
							: 'text-base-content/70 hover:bg-base-300 hover:text-base-content'}"
					>
						Guide
					</a>
					{#if $auth.user?.role === 'admin'}
						<a
							href="/admin/sessions"
							class="whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors {isActive(['/admin'])
								? 'bg-primary/15 text-primary'
								: 'text-base-content/70 hover:bg-base-300 hover:text-base-content'}"
						>
							DM Console
						</a>
					{/if}
				</div>
			{/if}

			<!-- Right: Campaign + User Menu -->
			<div class="flex shrink-0 items-center gap-2.5">
				{#if $auth.isAuthenticated}
					{#if $auth.campaign}
						<a
							href="/campaigns"
							class="hidden max-w-[120px] truncate whitespace-nowrap rounded border border-primary/30 bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary hover:bg-primary/20 md:inline-block"
							title="Switch Campaign"
						>
							{$auth.campaign.name}
						</a>
					{/if}

					<div class="hidden min-w-0 flex-col items-end leading-tight md:flex">
						<span class="max-w-[150px] truncate whitespace-nowrap text-xs font-medium text-base-content">{$auth.user?.username}</span>
						{#if $auth.user?.active_character}
							<span class="max-w-[150px] truncate whitespace-nowrap text-[11px] text-base-content/55">
								{$auth.user.active_character.name} · Lvl {$auth.user.active_character.level}
							</span>
						{/if}
					</div>

					<div class="dropdown dropdown-end">
						<button
							tabindex="0"
							class="btn btn-ghost btn-circle btn-sm avatar overflow-hidden border border-base-content/15"
							aria-label="User Menu"
						>
							<div class="w-8 rounded-full">
								{#if $auth.user?.avatar_url}
									<img alt="Avatar" src={$auth.user.avatar_url} />
								{:else}
									<div
										class="flex h-full items-center justify-center bg-base-300 text-sm font-semibold text-primary"
									>
										{$auth.user?.username?.charAt(0).toUpperCase()}
									</div>
								{/if}
							</div>
						</button>
						<ul
							class="dropdown-content menu z-40 mt-2 w-52 rounded-lg border border-base-content/10 bg-base-200 p-2 shadow-lg"
						>
							<li class="menu-title text-xs md:hidden">{$auth.user?.username}</li>
							<li><a href="/characters">My Characters</a></li>
							<li><a href="/campaigns">Switch Campaign</a></li>
							<li><hr class="my-1 border-base-content/10" /></li>
							<li><button on:click={handleLogout} class="font-medium text-error">Logout</button></li>
						</ul>
					</div>
				{/if}
			</div>
		</div>
	</nav>

	<main class="flex-grow">
		<slot />
	</main>
</div>
