<script lang="ts">
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let stats: any = null;
	let loading = true;
	let error: string | null = null;

	onMount(async () => {
		try {
			stats = await api('GET', '/campaigns/stats');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load statistics.';
		} finally {
			loading = false;
		}
	});

    function formatDate(dateStr: string) {
        if (!dateStr) return 'Never';
        return new Date(dateStr).toLocaleDateString(undefined, { 
            weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' 
        });
    }
</script>

<div class="container mx-auto p-4 max-w-5xl">
	<div class="mb-8 flex items-center justify-between border-b border-base-content/10 pb-4">
		<h1 class="text-3xl font-[var(--font-cinzel)] font-bold tracking-tight text-primary">📊 Campaign Statistics</h1>
		<a href="/dashboard" class="btn btn-ghost btn-sm">← Back to Dashboard</a>
	</div>

	{#if loading}
		<div class="flex justify-center py-20">
			<LoadingSpinner />
		</div>
	{:else if error}
		<div class="alert alert-error">
			<span>{error}</span>
		</div>
	{:else if stats}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
			<!-- Mission Summary -->
			<div class="stats shadow bg-base-100 border border-base-content/5">
				<div class="stat">
					<div class="stat-title">Missions</div>
					<div class="stat-value text-primary">{stats.total_missions}</div>
					<div class="stat-desc">{stats.completed_missions} completed / {stats.failed_missions} failed</div>
				</div>
			</div>

			<!-- Character Summary -->
			<div class="stats shadow bg-base-100 border border-base-content/5">
				<div class="stat">
					<div class="stat-title">Characters</div>
					<div class="stat-value text-secondary">{stats.total_characters}</div>
					<div class="stat-desc">{stats.active_characters} active / {stats.dead_characters} deceased</div>
				</div>
			</div>

			<!-- Resource Summary -->
			<div class="stats shadow bg-base-100 border border-base-content/5">
				<div class="stat">
					<div class="stat-title">Total Gold Earned</div>
					<div class="stat-value text-warning">🪙 {stats.total_gold_earned}</div>
					<div class="stat-desc">Lifetime war chest earnings</div>
				</div>
			</div>

            <!-- Activity Summary -->
			<div class="stats shadow bg-base-100 border border-base-content/5">
				<div class="stat">
					<div class="stat-title">Last Session</div>
					<div class="stat-value text-sm whitespace-normal mt-2">{formatDate(stats.last_session_date)}</div>
					<div class="stat-desc">{stats.total_sessions} total operations logged</div>
				</div>
			</div>
		</div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="card bg-base-100 border border-base-content/10 shadow-sm">
                <div class="card-body">
                    <h3 class="card-title text-sm font-bold uppercase tracking-widest opacity-60">Mission Success Rate</h3>
                    <div class="flex items-center gap-4 py-4">
                        {#let successRate = stats.total_missions > 0 ? Math.round((stats.completed_missions / stats.total_missions) * 100) : 0}
                            <div class="radial-progress text-primary" style="--value:{successRate}; --size:8rem; --thickness: 1rem;" role="progressbar">
                                {successRate}%
                            </div>
                            <div>
                                <p class="text-sm opacity-80">Of all attempted missions, {stats.completed_missions} were successful.</p>
                            </div>
                        {/let}
                    </div>
                </div>
            </div>

            <div class="card bg-base-100 border border-base-content/10 shadow-sm">
                <div class="card-body">
                    <h3 class="card-title text-sm font-bold uppercase tracking-widest opacity-60">Resource Accumulation</h3>
                    <div class="space-y-4 py-2">
                        <div>
                            <div class="flex justify-between text-xs mb-1">
                                <span>⚡ Total Essence Recovered</span>
                                <span class="font-bold">{stats.total_essence_earned}</span>
                            </div>
                            <progress class="progress progress-primary w-full" value={stats.total_essence_earned} max={stats.total_essence_earned > 1000 ? stats.total_essence_earned : 1000}></progress>
                        </div>
                        <div>
                            <div class="flex justify-between text-xs mb-1">
                                <span>🪙 Total Gold Earnings</span>
                                <span class="font-bold">{stats.total_gold_earned} GP</span>
                            </div>
                            <progress class="progress progress-warning w-full" value={stats.total_gold_earned} max={stats.total_gold_earned > 5000 ? stats.total_gold_earned : 5000}></progress>
                        </div>
                    </div>
                </div>
            </div>
        </div>
	{/if}
</div>
