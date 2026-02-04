<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/auth';
  import { get } from 'svelte/store';
  import { API_BASE_URL } from '$lib/config';

  onMount(() => {
    const { isAuthenticated } = get(auth);
    if (isAuthenticated) {
      goto('/dashboard');
    }
  });

  function handleLogin() {
    window.location.href = `${API_BASE_URL}/auth/discord/login`;
  }
</script>

<div class="flex items-center justify-center min-h-screen bg-gray-100">
  <div class="p-8 bg-white shadow-md rounded-lg text-center">
    <h1 class="text-2xl font-bold mb-6">Login to DnD Westmarches</h1>
    <p class="mb-4 text-gray-600">Please sign in using your Discord account.</p>

    <button
      on:click={handleLogin}
      class="flex items-center justify-center w-full px-4 py-2 text-white bg-indigo-600 rounded hover:bg-indigo-700 focus:outline-none"
    >
      <!-- Discord Logo SVG -->
      <svg class="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037 2.03 2.03 0 0 0 .59 1.05 2.031 2.031 0 0 0 .589.049.073.073 0 0 0 .079-.036 19.774 19.774 0 0 0-4.885 1.516c-.05.01-.064.08-.024.11a16.142 16.142 0 0 1 1.764 2.89.076.076 0 0 0 .065.048c.026-.002.052.003.076.014a19.866 19.866 0 0 0 6.666 0 .077.077 0 0 0 .077-.062 16.16 16.16 0 0 1 1.764-2.89.073.073 0 0 0-.025-.11ZM6.3 16.48a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3Zm11.4 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3Z"/>
      </svg>
      Login with Discord
    </button>
  </div>
</div>
