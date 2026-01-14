<script lang="ts">
    import { auth } from '$lib/auth';
</script>

<div class="hero min-h-[calc(100vh-64px)] bg-base-200 pattern-grid">
  <div class="hero-content text-center p-4 md:p-10">
    <div class="max-w-3xl">
      <h1 class="text-5xl md:text-7xl font-bold font-[var(--font-cinzel)] text-primary mb-6 drop-shadow-md tracking-tight">DnD Westmarches Hub</h1>
      <p class="py-6 text-xl md:text-2xl opacity-90 mb-8 font-light leading-relaxed max-w-2xl mx-auto">
        Manage your characters, track missions, and explore the world in a persistent multi-campaign Westmarches experience.
      </p>

      {#if $auth.isAuthenticated}
        <div class="card w-full max-w-sm mx-auto shadow-2xl bg-base-100 border-2 border-primary/20 hover:border-primary/50 transition-all duration-300">
          <div class="card-body items-center text-center">
            <h2 class="card-title font-[var(--font-cinzel)] text-2xl">Welcome Back!</h2>
            <p class="text-sm opacity-70 mb-4 font-bold">{$auth.user?.username}</p>
            <div class="card-actions flex-col w-full gap-3">
              <a href="/dashboard" class="btn btn-primary w-full shadow-lg">Enter Dashboard</a>
              <a href="/campaigns" class="btn btn-outline btn-secondary w-full">Switch Campaign</a>
            </div>
          </div>
        </div>
      {:else}
        <div class="card w-full max-w-md mx-auto shadow-2xl bg-base-100 border-2 border-primary/20 hover:border-primary/50 transition-all duration-300">
             <div class="card-body items-center text-center">
                <p class="mb-6 text-lg text-base-content/80">Join the adventure today.</p>
                <a href="/login" class="btn btn-primary btn-lg w-full gap-3 font-bold uppercase tracking-widest shadow-xl">
                    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037 2.03 2.03 0 0 0 .59 1.05 2.031 2.031 0 0 0 .589.049.073.073 0 0 0 .079-.036 19.774 19.774 0 0 0-4.885 1.516c-.05.01-.064.08-.024.11a16.142 16.142 0 0 1 1.764 2.89.076.076 0 0 0 .065.048c.026-.002.052.003.076.014a19.866 19.866 0 0 0 6.666 0 .077.077 0 0 0 .077-.062 16.16 16.16 0 0 1 1.764-2.89.073.073 0 0 0-.025-.11ZM6.3 16.48a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3Zm11.4 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3Z"/></svg>
                    Login with Discord
                </a>
             </div>
        </div>
      {/if}
    </div>
  </div>
</div>
