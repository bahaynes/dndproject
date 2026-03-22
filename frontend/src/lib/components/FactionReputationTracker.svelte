<script lang="ts">
    import { onMount } from 'svelte';
    import { auth } from '$lib/auth';
    import { get } from 'svelte/store';
    import { API_BASE_URL } from '$lib/config';

    interface FactionReputation {
        id: number;
        faction_name: string;
        level: number;
        color: string | null;
        description: string | null;
    }

    let reputations: FactionReputation[] = [];
    let loading = true;

    const LEVEL_LABELS: Record<number, string> = {
        5: 'Sworn Allies', 4: 'Trusted', 3: 'Friendly', 2: 'Cooperative',
        1: 'Cautiously Warm', 0: 'Neutral',
        '-1': 'Wary', '-2': 'Suspicious', '-3': 'Hostile', '-4': 'Enemies', '-5': 'Blood Feud',
    };

    onMount(async () => {
        const { token } = get(auth);
        const res = await fetch(`${API_BASE_URL}/factions/`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) reputations = await res.json();
        loading = false;
    });

    function levelClass(level: number): string {
        if (level >= 3) return 'text-success';
        if (level >= 1) return 'text-info';
        if (level === 0) return 'opacity-40';
        if (level >= -2) return 'text-warning';
        return 'text-error';
    }

    function factionColor(rep: FactionReputation): string {
        return rep.color ?? '#6b7280';
    }
</script>

<div class="space-y-2">
    <div class="flex justify-between items-center">
        <h2 class="text-xs font-bold uppercase tracking-wide opacity-50">Intel / Standing</h2>
        <a href="/factions" class="text-xs text-primary hover:underline">Full report →</a>
    </div>

    {#if loading}
        <div class="flex items-center gap-2 opacity-40 text-xs">
            <span class="loading loading-spinner loading-xs"></span>
            Loading...
        </div>
    {:else if reputations.length === 0}
        <p class="text-xs opacity-40">No factions on record.</p>
    {:else}
        {#each reputations as rep}
            <div class="flex items-center gap-2 text-sm">
                <span class="w-2 h-2 rounded-full flex-shrink-0" style="background-color: {factionColor(rep)}"></span>
                <span class="flex-1 font-medium truncate">{rep.faction_name}</span>
                <span class="font-mono text-xs font-bold {levelClass(rep.level)}">
                    {rep.level > 0 ? '+' : ''}{rep.level}
                </span>
                <span class="text-xs opacity-40 hidden sm:inline">{LEVEL_LABELS[rep.level] ?? ''}</span>
            </div>
        {/each}
    {/if}
</div>
