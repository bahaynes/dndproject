<script lang="ts">
    import { auth, type User } from '$lib/auth';

    let user: User | null = null;

    auth.subscribe(value => {
        user = value.user;
    });
</script>

<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">Dashboard</h1>
    {#if user}
        <p class="mt-4">Welcome, {user.username}!</p>
        <div class="mt-6">
            <a href="/character" class="text-lg text-blue-600 hover:underline bg-white p-4 rounded-lg shadow-md block">
                View Your Character Sheet
            </a>
        </div>
    {:else}
        <p class="mt-4">Loading user information...</p>
    {/if}
</div>
