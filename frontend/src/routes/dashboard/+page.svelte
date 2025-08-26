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
    {:else}
        <p class="mt-4">Loading user information...</p>
    {/if}
</div>
