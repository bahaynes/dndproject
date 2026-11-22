<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { Ship, TownLocation } from '$lib/types';
	import { safeInternalPath } from '$lib/utils/url';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let hub: Ship | null = null;
	let locations: TownLocation[] = [];
	let selectedId: string | null = null;
	let loading = true;
	let error = '';

	const LINK_LABELS: Record<string, string> = {
		'/sessions': 'View Expeditions & Schedule',
		'/maps': 'Open Fjord Map',
		'/store': 'Browse Quartermaster Stock',
		'/factions': 'View Factions',
		'/roster': 'View Party Roster',
		'/characters': 'Manage Characters',
		'/missions': 'View Quest Board'
	};

	onMount(async () => {
		try {
			hub = await api('GET', '/ship/');
			locations = hub?.town_locations ?? [];
			if (locations.length > 0) {
				selectedId = locations[0].id;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load town map.';
		} finally {
			loading = false;
		}
	});

	$: selected = locations.find((l) => l.id === selectedId) ?? locations[0] ?? null;
	$: safeLinkPath = safeInternalPath(selected?.link_path);

	function linkLabel(path: string | null | undefined): string {
		if (!path) return 'Go';
		return LINK_LABELS[path] ?? 'Open';
	}
</script>

<PageHeader
	title={hub?.name ? `${hub.name} — Town Map` : 'Town Map'}
	subtitle="Places to visit, partners to meet, and rumors to chase before stepping past the braziers."
/>

{#if loading}
	<LoadingSpinner size="lg" />
{:else if error}
	<div class="alert alert-error text-sm">{error}</div>
{:else if locations.length === 0}
	<div class="panel p-6 text-center space-y-2">
		<p class="text-sm font-medium text-base-content">No town districts configured yet.</p>
		<p class="text-xs text-base-content/60">
			A DM can seed a starter world preset in Campaign Settings or import a WorldBundle with
			<code>town_locations</code>.
		</p>
	</div>
{:else}
	<div class="grid grid-cols-1 gap-6 lg:grid-cols-12">
		<!-- Interactive Town Map -->
		<div class="lg:col-span-7 xl:col-span-8 space-y-3">
			<div class="panel overflow-hidden p-3">
				<svg
					viewBox="0 0 800 500"
					class="w-full h-auto rounded-lg bg-base-300/80 border border-base-content/10"
					role="img"
					aria-label="Interactive town map of {hub?.name || 'Town'}"
				>
					<defs>
						<radialGradient id="brazierGlow" cx="50%" cy="50%" r="50%">
							<stop offset="0%" stop-color="rgba(245, 158, 11, 0.55)" />
							<stop offset="100%" stop-color="rgba(245, 158, 11, 0)" />
						</radialGradient>
					</defs>

					<!-- Northern Cliff Ridge -->
					<path
						d="M 0 0 L 800 0 L 800 115 Q 620 140 440 105 Q 240 80 0 125 Z"
						fill="rgba(100, 116, 139, 0.28)"
						stroke="rgba(148, 163, 184, 0.3)"
						stroke-width="2"
					/>
					<text
						x="24"
						y="36"
						fill="rgba(226, 232, 240, 0.45)"
						font-size="12"
						font-weight="600"
						letter-spacing="2"
					>
						HIGH RIDGE CLIFF WALL
					</text>

					<!-- Fjord River Channel along the bottom -->
					<path
						d="M 0 430 Q 220 395 430 435 Q 640 470 800 410 L 800 500 L 0 500 Z"
						fill="rgba(59, 130, 246, 0.22)"
						stroke="rgba(96, 165, 250, 0.35)"
						stroke-width="2"
					/>
					<text
						x="24"
						y="480"
						fill="rgba(147, 197, 253, 0.55)"
						font-size="12"
						font-weight="600"
						letter-spacing="2"
					>
						FJORD WATERWAY
					</text>

					<!-- Town Perimeter Brazier Wall -->
					<path
						d="M 90 150 L 700 140 L 735 375 L 110 385 Z"
						fill="rgba(255, 255, 255, 0.02)"
						stroke="rgba(245, 158, 11, 0.25)"
						stroke-width="2"
						stroke-dasharray="6 6"
					/>

					<!-- Roads connecting locations -->
					{#each locations as loc, idx}
						{#if idx > 0}
							<line
								x1={locations[0].x * 8}
								y1={locations[0].y * 5}
								x2={loc.x * 8}
								y2={loc.y * 5}
								stroke="rgba(255, 255, 255, 0.12)"
								stroke-width="2"
								stroke-dasharray="4 4"
							/>
						{/if}
					{/each}

					<!-- Perimeter Warding Braziers -->
					{#each [[95, 155], [400, 145], [695, 145], [730, 370], [420, 380], [115, 380]] as [bx, by]}
						<circle cx={bx} cy={by} r="22" fill="url(#brazierGlow)" />
						<circle cx={bx} cy={by} r="4" fill="#f59e0b" />
					{/each}

					<!-- Clickable Town Location Pins -->
					{#each locations as loc, idx}
						{@const px = Math.max(60, Math.min(740, loc.x * 8))}
						{@const py = Math.max(55, Math.min(430, loc.y * 5))}
						{@const isSelected = selected?.id === loc.id}
						<g
							transform="translate({px}, {py})"
							class="cursor-pointer"
							role="button"
							tabindex="0"
							aria-label={loc.name}
							on:click={() => (selectedId = loc.id)}
							on:keydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									selectedId = loc.id;
								}
							}}
						>
							{#if isSelected}
								<circle r="24" fill="rgba(245, 158, 11, 0.2)" stroke="#f59e0b" stroke-width="2" />
							{/if}
							<circle
								r="15"
								fill={isSelected ? '#f59e0b' : '#1e293b'}
								stroke={isSelected ? '#fef3c7' : '#f59e0b'}
								stroke-width="2"
							/>
							<text
								text-anchor="middle"
								dy="5"
								font-size="13"
								font-weight="700"
								fill={isSelected ? '#0f172a' : '#fef3c7'}
							>
								{idx + 1}
							</text>
							<rect
								x="-82"
								y="20"
								width="164"
								height="22"
								rx="5"
								fill="rgba(15, 23, 42, 0.88)"
								stroke={isSelected ? 'rgba(245, 158, 11, 0.7)' : 'rgba(255, 255, 255, 0.12)'}
							/>
							<text
								y="34"
								text-anchor="middle"
								font-size="10.5"
								font-weight="600"
								fill={isSelected ? '#fde68a' : '#e2e8f0'}
							>
								{loc.name.length > 26 ? loc.name.slice(0, 24) + '…' : loc.name}
							</text>
						</g>
					{/each}
				</svg>
			</div>

			<!-- Quick Select Strip -->
			<div class="flex flex-wrap gap-2">
				{#each locations as loc, idx}
					<button
						class="btn btn-xs {selected?.id === loc.id ? 'btn-primary' : 'btn-outline border-base-content/20'}"
						on:click={() => (selectedId = loc.id)}
					>
						{idx + 1}. {loc.name}
					</button>
				{/each}
			</div>
		</div>

		<!-- Selected Location Detail Panel -->
		<div class="lg:col-span-5 xl:col-span-4">
			{#if selected}
				<div class="panel p-5 space-y-4">
					<div>
						{#if selected.role}
							<span class="badge badge-primary badge-outline badge-xs mb-2">{selected.role}</span>
						{/if}
						<h2 class="text-lg font-bold text-base-content">{selected.name}</h2>
						{#if selected.npc}
							<p class="text-xs text-base-content/65 mt-0.5">
								Hosted by <strong class="text-base-content/90">{selected.npc}</strong>
							</p>
						{/if}
					</div>

					<p class="text-sm leading-relaxed text-base-content/85">{selected.description}</p>

					{#if selected.services && selected.services.length > 0}
						<div class="space-y-1.5">
							<h3 class="text-xs font-semibold uppercase tracking-wider text-base-content/55">
								Before You Head Out
							</h3>
							<ul class="space-y-1 text-xs text-base-content/80">
								{#each selected.services as service}
									<li class="flex items-start gap-2">
										<span class="text-primary font-bold">•</span>
										<span>{service}</span>
									</li>
								{/each}
							</ul>
						</div>
					{/if}

					{#if selected.rumor}
						<div class="rounded-lg border border-warning/30 bg-warning/10 p-3 text-xs space-y-1">
							<div class="font-semibold uppercase tracking-wider text-warning">Word Around Town</div>
							<p class="leading-relaxed text-base-content/85 italic">"{selected.rumor}"</p>
						</div>
					{/if}

					{#if safeLinkPath}
						<div class="pt-1">
							<a href={safeLinkPath} class="btn btn-primary btn-sm w-full">
								{linkLabel(safeLinkPath)}
							</a>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
{/if}
