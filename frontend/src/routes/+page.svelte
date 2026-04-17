<script lang="ts">
    import { auth } from '$lib/auth';
    import { goto } from '$app/navigation';
    import { API_BASE_URL } from '$lib/config';

    $: if ($auth.isAuthenticated && $auth.campaign) {
        goto('/dashboard');
    }
</script>

<div class="hero min-h-[calc(100vh-64px)] bg-base-200">
  <div class="hero-content text-center p-4 md:p-10">
    <div class="max-w-3xl">
      <h1 class="text-5xl md:text-7xl font-bold font-[var(--font-cinzel)] text-primary mb-6 drop-shadow-md tracking-tight">
        DnD Westmarches Hub
      </h1>
      <p class="py-6 text-xl md:text-2xl opacity-90 mb-8 font-light leading-relaxed max-w-2xl mx-auto">
        Manage your characters, track missions, and explore the world in a persistent multi-campaign Westmarches experience.
      </p>
      <div class="card w-full max-w-md mx-auto shadow-2xl bg-base-100 border-2 border-primary/20">
        <div class="card-body items-center text-center">
          <p class="mb-6 text-lg text-base-content/80">Join the adventure today.</p>
          <a href="{API_BASE_URL}/auth/discord/login" data-sveltekit-reload class="btn btn-lg w-full gap-3 font-bold shadow-xl text-white" style="background-color: #5865F2; border-color: #5865F2;">
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 127.14 96.36" xmlns="http://www.w3.org/2000/svg">
              <path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/>
            </svg>
            Login with Discord
          </a>
        </div>
      </div>
    </div>
  </div>
</div>
