<script lang="ts">
    import { auth } from '$lib/auth';
</script>

<div class="flex flex-col items-center justify-center min-h-[80vh] text-center px-4">
    <h1 class="text-5xl font-extrabold text-gray-800 mb-6">DnD Westmarches Hub</h1>
    <p class="text-xl text-gray-600 mb-8 max-w-2xl">
        Manage your characters, track missions, and explore the world in a persistent multi-campaign Westmarches experience.
    </p>

    {#if $auth.isAuthenticated}
        <div class="space-y-4">
            <p class="text-lg font-medium">Welcome back, {$auth.user?.username}!</p>
            <div class="flex gap-4 justify-center">
                <a href="/dashboard" class="px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-semibold shadow-lg transition">
                    Go to Dashboard
                </a>
                 <a href="/campaigns" class="px-8 py-3 bg-white text-indigo-600 border border-indigo-600 rounded-lg hover:bg-indigo-50 font-semibold shadow transition">
                    Switch Campaign
                </a>
            </div>
        </div>
    {:else}
        <div class="space-y-4">
            <p class="text-lg text-gray-500">Login with Discord to get started.</p>
            <a href="/login" class="inline-flex items-center px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-semibold shadow-lg transition">
                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037 2.03 2.03 0 0 0 .59 1.05 2.031 2.031 0 0 0 .589.049.073.073 0 0 0 .079-.036 19.774 19.774 0 0 0-4.885 1.516c-.05.01-.064.08-.024.11a16.142 16.142 0 0 1 1.764 2.89.076.076 0 0 0 .065.048c.026-.002.052.003.076.014a19.866 19.866 0 0 0 6.666 0 .077.077 0 0 0 .077-.062 16.16 16.16 0 0 1 1.764-2.89.073.073 0 0 0-.025-.11ZM6.3 16.48a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3Zm11.4 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3Z"/></svg>
                Login with Discord
            </a>
        </div>
    {/if}
</div>
