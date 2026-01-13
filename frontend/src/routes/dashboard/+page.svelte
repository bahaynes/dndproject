<script lang="ts">
    import { auth } from '$lib/auth';
    import type { User } from '$lib/auth';
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';

    let user: User | null = null;
    let campaign = null;

    auth.subscribe(value => {
        user = value.user;
        campaign = value.campaign;
    });

    onMount(() => {
        // If not authenticated, the layout should handle it, but double check
        // Also if no campaign selected, redirect to campaigns
        if (!user && !localStorage.getItem('accessToken')) {
             goto('/login');
        } else if (user && !campaign) {
             goto('/campaigns');
        }
    });
</script>

<div class="container mx-auto p-4">
    <div class="flex justify-between items-center mb-6">
         <h1 class="text-3xl font-bold">Dashboard</h1>
         {#if campaign}
             <div class="bg-gray-100 px-4 py-2 rounded-lg">
                 <span class="text-sm text-gray-500 uppercase font-semibold">Campaign</span>
                 <p class="font-bold text-indigo-700">{campaign.name}</p>
             </div>
         {/if}
    </div>

    {#if user}
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">Your Profile</h2>
            <div class="flex items-center space-x-4">
                {#if user.avatar_url}
                    <img src={user.avatar_url} alt="Avatar" class="w-16 h-16 rounded-full" />
                {:else}
                    <div class="w-16 h-16 bg-gray-300 rounded-full flex items-center justify-center text-xl font-bold text-gray-600">
                        {user.username.slice(0, 1).toUpperCase()}
                    </div>
                {/if}
                <div>
                    <p class="text-lg font-bold">{user.username}</p>
                    <p class="text-gray-600 capitalize">Role: {user.role}</p>
                    <p class="text-xs text-gray-400">ID: {user.id}</p>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">Characters & Inventory</h2>
                <ul class="space-y-2">
                     <li><a href="/characters" class="block p-2 hover:bg-gray-50 rounded text-indigo-600 font-medium">My Character</a></li>
                     <li><a href="/characters/inventory" class="block p-2 hover:bg-gray-50 rounded text-indigo-600 font-medium">Inventory</a></li>
                </ul>
            </div>

             <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">Activities</h2>
                <ul class="space-y-2">
                     <li><a href="/missions" class="block p-2 hover:bg-gray-50 rounded text-indigo-600 font-medium">Missions Board</a></li>
                     <li><a href="/sessions" class="block p-2 hover:bg-gray-50 rounded text-indigo-600 font-medium">Game Sessions</a></li>
                     <li><a href="/store" class="block p-2 hover:bg-gray-50 rounded text-indigo-600 font-medium">Store</a></li>
                </ul>
            </div>
        </div>

        {#if user.role === 'admin'}
            <div class="mt-6 bg-red-50 border border-red-100 rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4 text-red-800">Dungeon Master Tools</h2>
                <ul class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <li><a href="/admin/sessions" class="block p-3 bg-white rounded shadow hover:shadow-md text-red-700 font-medium text-center">Manage Sessions</a></li>
                    <li><a href="/admin/missions" class="block p-3 bg-white rounded shadow hover:shadow-md text-red-700 font-medium text-center">Manage Missions</a></li>
                    <li><a href="/admin/items" class="block p-3 bg-white rounded shadow hover:shadow-md text-red-700 font-medium text-center">Manage Items</a></li>
                </ul>
            </div>
        {/if}

    {:else}
        <p class="mt-4">Loading user information...</p>
    {/if}
</div>
