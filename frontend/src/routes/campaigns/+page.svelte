<script lang="ts">
  import { onMount } from 'svelte';
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
    globalToken = localStorage.getItem('tempGlobalToken') || '';
    discordToken = localStorage.getItem('tempDiscordToken') || '';

    if (!globalToken) {
      goto('/login');
      return;
    }

    await loadCampaigns();
  });

  async function loadCampaigns() {
    loading = true;
    error = '';
    try {
      // 1. Fetch My Campaigns
      const myRes = await fetch(`${API_BASE_URL}/campaigns/mine`, {
        headers: { Authorization: `Bearer ${globalToken}` }
      });
      if (myRes.ok) myCampaigns = await myRes.json();

      // 2. Fetch Available (Joinable) Campaigns
      // Need to send discord_token in body
      const availRes = await fetch(`${API_BASE_URL}/campaigns/available`, {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${globalToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ discord_token: discordToken })
      });
      if (availRes.ok) availableCampaigns = await availRes.json();

      // 3. (Optional) Fetch Admin Guilds for Setup
      // Only if user is admin (we can try, if 403 ignore)
      const adminRes = await fetch(`${API_BASE_URL}/campaigns/discord/guilds`, {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${globalToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ discord_token: discordToken })
      });
      if (adminRes.ok) adminGuilds = await adminRes.json();

    } catch (e) {
      console.error(e);
      error = "Failed to load campaigns.";
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
        error = "Failed to login to campaign.";
      }
    } catch (e) {
        error = "Error selecting campaign.";
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
        error = err.detail || "Failed to join campaign.";
      }
    } catch (e) {
      error = "Error joining campaign.";
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

          if(res.ok) {
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
              error = err.detail || "Setup failed";
          }
      } catch(e) {
          error = "Error setting up campaign";
      }
  }
</script>

<div class="container mx-auto p-8">
  <h1 class="text-3xl font-bold mb-8">Select Campaign</h1>

  {#if error}
    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {error}
    </div>
  {/if}

  {#if loading}
    <p>Loading...</p>
  {:else}
    <!-- My Campaigns -->
    <div class="mb-8">
      <h2 class="text-xl font-semibold mb-4">My Campaigns</h2>
      {#if myCampaigns.length === 0}
        <p class="text-gray-500">You are not part of any campaigns yet.</p>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          {#each myCampaigns as camp}
            <button
              on:click={() => selectCampaign(camp.id)}
              class="block w-full p-6 bg-white rounded shadow hover:shadow-md text-left transition"
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
      <h2 class="text-xl font-semibold mb-4">Available to Join</h2>
      {#if availableCampaigns.length === 0}
        <p class="text-gray-500">No new campaigns found that match your Discord servers.</p>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          {#each availableCampaigns as camp}
            <button
                on:click={() => joinCampaign(camp.discord_guild_id)}
                class="block w-full p-6 bg-blue-50 rounded shadow hover:shadow-md text-left transition border border-blue-200"
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
        <h2 class="text-xl font-semibold mb-4">Setup New Campaign</h2>
        <p class="text-sm text-gray-600 mb-4">You have admin rights on these Discord servers.</p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          {#each adminGuilds as guild}
             <!-- Filter out already setup guilds -->
             {#if !myCampaigns.find(c => c.discord_guild_id === guild.id) && !availableCampaigns.find(c => c.discord_guild_id === guild.id)}
                <button
                    on:click={() => setupCampaign(guild.id, guild.name)}
                    class="block w-full p-6 bg-gray-50 rounded shadow hover:shadow-md text-left transition border border-gray-200 dashed"
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
