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
        // We received a Global Token.
        // We can't "login" fully yet because we haven't selected a campaign.
        // We store these temporarily (e.g., in sessionStorage or just pass via state)
        // For simplicity, let's put them in localStorage but mark as 'incomplete' or handle in /campaigns

        localStorage.setItem('tempGlobalToken', token);
        localStorage.setItem('tempDiscordToken', discordToken);

        goto('/campaigns');
      } else {
        // Error or missing token
        goto('/login');
      }
    }
  });
</script>

<div class="flex items-center justify-center min-h-screen">
  <p class="text-xl">Authenticating...</p>
</div>
