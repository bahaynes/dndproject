<script lang="ts">
    import { auth, type User } from '$lib/auth';
    import { onMount } from 'svelte';

    let user: User | null = null;

    auth.subscribe(value => {
        user = value.user;
    });

    // In a real app, you'd fetch the user profile here if it's not already loaded
</script>

<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">Dashboard</h1>
    {#if user}
        <p class="mt-4">Welcome, {user.username}!</p>

        <div class="mt-6">
            <h2 class="text-xl font-semibold">Game Links</h2>
            <ul class="list-disc list-inside mt-2">
                <li><a href="/sessions" class="link link-primary">View Game Sessions</a></li>
                <li><a href="/missions" class="link link-primary">View Mission Board</a></li>
            </ul>
        </div>

        {#if user.role === 'admin'}
            <div class="mt-6">
                <h2 class="text-xl font-semibold">Admin Tools</h2>
                <ul class="list-disc list-inside mt-2">
                    <li><a href="/dashboard/admin/sessions" class="link link-secondary">Manage Game Sessions</a></li>
                </ul>
            </div>
        {/if}

    {:else}
        <p class="mt-4">Loading user information...</p>
    {/if}
</div>
