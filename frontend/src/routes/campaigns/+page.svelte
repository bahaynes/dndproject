<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { API_BASE_URL } from '$lib/config';
	import { auth, login } from '$lib/auth';

	let myCampaigns: any[] = [];
	let availableCampaigns: any[] = [];
	let adminGuilds: any[] = [];
	let loading = true;
	let globalToken = '';
	let discordToken = '';
	let error = '';

	onMount(async () => {
		// Check for temp tokens (initial login flow)
		const tempGlobal = localStorage.getItem('tempGlobalToken');
		const tempDiscord = localStorage.getItem('tempDiscordToken');

		if (tempGlobal) {
			globalToken = tempGlobal;
			discordToken = tempDiscord || '';
		} else {
			// Check for existing authenticated session (switching campaigns)
			const authState = get(auth);
			if (authState.token) {
				globalToken = authState.token;
				// For authenticated users, we might not have a raw discord token anymore,
				// but the backend should know our discord ID.
				// However, the current endpoints require a discord token to hunt for guilds.
				// If we are just switching between *already joined* campaigns, we just need /campaigns/mine.
				// If we want to join *new* campaigns, we might need a re-auth flow or backend support.
				// For now, let's assume switching implies selecting from "My Campaigns" or public ones.
			} else {
				goto('/login');
				return;
			}
		}

		await loadCampaigns();
	});

	async function loadCampaigns() {
		loading = true;
		error = '';
		try {
			// 1. Fetch My Campaigns
			// Works with both temp Global Token (if scoped right) and User Token
			const myRes = await fetch(`${API_BASE_URL}/campaigns/mine`, {
				headers: { Authorization: `Bearer ${globalToken}` }
			});

			if (myRes.ok) {
				myCampaigns = await myRes.json();
			} else {
				// If my campaigns fails with 401, we might need to login again
				if (myRes.status === 401) {
					goto('/login');
					return;
				}
			}

			// 2. Fetch Available (Joinable) Campaigns
			// This endpoint requires a discord_token body.
			// If we are switching campaigns, we might not have it.
			// We should only call this if we have a discordToken (initial flow) OR if we update backend to not require it for auth'd users.
			// For now, let's only call it if we have a discordToken.
			if (discordToken) {
				const availRes = await fetch(`${API_BASE_URL}/campaigns/available`, {
					method: 'POST',
					headers: {
						Authorization: `Bearer ${globalToken}`,
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({ discord_token: discordToken })
				});
				if (availRes.ok) availableCampaigns = await availRes.json();

				// 3. Admin Guilds (also needs discord token)
				const adminRes = await fetch(`${API_BASE_URL}/campaigns/discord/guilds`, {
					method: 'POST',
					headers: {
						Authorization: `Bearer ${globalToken}`,
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({ discord_token: discordToken })
				});
				if (adminRes.ok) adminGuilds = await adminRes.json();
			}
		} catch (e) {
			console.error(e);
			error = 'Failed to load campaigns.';
		} finally {
			loading = false;
		}
	}

	async function selectCampaign(campaignId: number) {
		try {
			const res = await fetch(`${API_BASE_URL}/campaigns/login`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${globalToken}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ campaign_id: campaignId })
			});

			if (res.ok) {
				const data = await res.json();
				const token = data.access_token;

				// Fetch User Profile with new Token
				const userRes = await fetch(`${API_BASE_URL}/auth/me`, {
					headers: { Authorization: `Bearer ${token}` }
				});
				const user = await userRes.json();

				// Final Login
				login(user, token, user.campaign);

				// Cleanup temp
				localStorage.removeItem('tempGlobalToken');
				localStorage.removeItem('tempDiscordToken');

				goto('/dashboard');
			} else {
				error = 'Failed to login to campaign.';
			}
		} catch (e) {
			error = 'Error selecting campaign.';
		}
	}

	async function joinCampaign(guildId: string) {
		try {
			const res = await fetch(`${API_BASE_URL}/campaigns/join`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${globalToken}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ discord_guild_id: guildId, discord_access_token: discordToken })
			});

			if (res.ok) {
				const data = await res.json();
				// Login directly
				const token = data.access_token;
				const userRes = await fetch(`${API_BASE_URL}/auth/me`, {
					headers: { Authorization: `Bearer ${token}` }
				});
				const user = await userRes.json();
				login(user, token, data.campaign);

				localStorage.removeItem('tempGlobalToken');
				localStorage.removeItem('tempDiscordToken');
				goto('/dashboard');
			} else {
				const err = await res.json();
				error = err.detail || 'Failed to join campaign.';
			}
		} catch (e) {
			error = 'Error joining campaign.';
		}
	}

	async function setupCampaign(guildId: string, name: string) {
		try {
			const res = await fetch(`${API_BASE_URL}/campaigns/setup`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${globalToken}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ discord_guild_id: guildId, name: name })
			});

			if (res.ok) {
				const data = await res.json();
				const token = data.access_token;
				const user = data.user;

				// Login directly
				login(user, token, data.campaign);

				// Cleanup temp
				localStorage.removeItem('tempGlobalToken');
				localStorage.removeItem('tempDiscordToken');

				goto('/dashboard');
			} else {
				const err = await res.json();
				error = err.detail || 'Setup failed';
			}
		} catch (e) {
			error = 'Error setting up campaign';
		}
	}
</script>

<div class="container mx-auto p-8">
	<h1 class="mb-8 text-3xl font-bold">Select Campaign</h1>

	{#if error}
		<div class="mb-4 rounded border border-red-400 bg-red-100 px-4 py-3 text-red-700">
			{error}
		</div>
	{/if}

	{#if loading}
		<p>Loading...</p>
	{:else}
		<!-- My Campaigns -->
		<div class="mb-8">
			<h2 class="mb-4 text-xl font-semibold">My Campaigns</h2>
			{#if myCampaigns.length === 0}
				<p class="text-gray-500">You are not part of any campaigns yet.</p>
			{:else}
				<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
					{#each myCampaigns as camp}
						<button
							on:click={() => selectCampaign(camp.id)}
							class="block w-full rounded bg-white p-6 text-left shadow transition hover:shadow-md"
						>
							<h3 class="text-lg font-bold">{camp.name}</h3>
							<p class="text-sm text-gray-500">Click to Play</p>
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Joinable Campaigns -->
		<div class="mb-8">
			<h2 class="mb-4 text-xl font-semibold">Available to Join</h2>
			{#if availableCampaigns.length === 0}
				<p class="text-gray-500">No new campaigns found that match your Discord servers.</p>
			{:else}
				<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
					{#each availableCampaigns as camp}
						<button
							on:click={() => joinCampaign(camp.discord_guild_id)}
							class="block w-full rounded border border-blue-200 bg-blue-50 p-6 text-left shadow transition hover:shadow-md"
						>
							<h3 class="text-lg font-bold text-blue-800">{camp.name}</h3>
							<p class="text-sm text-blue-600">Click to Join</p>
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Setup New Campaign (Admin Only) -->
		{#if adminGuilds.length > 0}
			<div class="mb-8 border-t pt-8">
				<h2 class="mb-4 text-xl font-semibold">Setup New Campaign</h2>
				<p class="mb-4 text-sm text-gray-600">You have admin rights on these Discord servers.</p>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
					{#each adminGuilds as guild}
						<!-- Filter out already setup guilds -->
						{#if !myCampaigns.find((c) => c.discord_guild_id === guild.id) && !availableCampaigns.find((c) => c.discord_guild_id === guild.id)}
							<button
								on:click={() => setupCampaign(guild.id, guild.name)}
								class="dashed block w-full rounded border border-gray-200 bg-gray-50 p-6 text-left shadow transition hover:shadow-md"
							>
								<h3 class="text-lg font-bold text-gray-700">{guild.name}</h3>
								<p class="text-sm text-gray-500">Initialize Campaign</p>
							</button>
						{/if}
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>
