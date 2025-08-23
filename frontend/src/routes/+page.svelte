<script lang="ts">
    import { auth } from '$lib/stores/auth';
</script>

<div class="container mx-auto p-8 text-center">
    <h1 class="text-4xl font-bold">Welcome to the DnD Westmarches Hub</h1>

    {#if $auth.isAuthenticated}
        <p class="mt-4 text-lg">You are logged in. Head to your dashboard to manage your character and missions.</p>
        <a href="/dashboard" class="mt-6 inline-block px-6 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-900">
            Go to Dashboard
        </a>
    {:else}
        <p class="mt-4 text-lg">Your adventure awaits! Join a campaign or manage your own.</p>
        <div class="mt-6">
            <a href="/login" class="inline-block px-6 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-900 mr-4">
                Login
            </a>
            <a href="/register" class="inline-block px-6 py-3 text-white bg-gray-600 rounded-lg hover:bg-gray-900">
                Register
            </a>
        </div>
    {/if}
</div>
