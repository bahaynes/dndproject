<script lang="ts">
    import { auth } from '$lib/auth';
    import type { User } from '$lib/types';
    import { onMount } from 'svelte';

    let user: User | null = null;

    auth.subscribe(value => {
        user = value.user;
    });

    // In a real app, you'd fetch the user profile here if it's not already loaded
</script>

<div class="page-container space-y-8">
    <div class="panel p-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
            <p class="text-sm uppercase tracking-wide text-amber-200">Dashboard</p>
            <h1 class="text-3xl font-bold">Your command deck</h1>
            <p class="muted">Pick up quests, review signups, and keep the guild running smooth.</p>
        </div>
        {#if user?.role}
            <span class="pill">Role: {user.role}</span>
        {/if}
    </div>

    {#if user}
        <div class="card-grid">
            <div class="card panel-strong">
                <div class="card-body">
                    <p class="pill w-fit">Welcome back</p>
                    <p class="text-lg font-semibold">Greetings, {user.username}!</p>
                    <p class="muted">Head straight to your next adventure.</p>
                    <div class="card-actions">
                        <a href="/sessions" class="btn btn-primary">View sessions</a>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-body">
                    <p class="pill w-fit">Game links</p>
                    <h2 class="card-title">Quick actions</h2>
                    <ul class="space-y-2 text-sm">
                        <li><a href="/sessions" class="nav-link">Session board</a></li>
                    </ul>
                </div>
            </div>

            {#if user.role === 'admin'}
                <div class="card">
                    <div class="card-body">
                        <p class="pill w-fit">Admin tools</p>
                        <h2 class="card-title">Keep the table balanced</h2>
                        <ul class="space-y-2 text-sm">
                            <li><a href="/dashboard/admin/roster" class="nav-link">User roster</a></li>
                            <li><a href="/dashboard/admin/sessions" class="nav-link">Manage game sessions</a></li>
                        </ul>
                    </div>
                </div>
            {/if}
        </div>
    {:else}
        <div class="panel p-6">
            <p>Loading user information...</p>
        </div>
    {/if}
</div>
