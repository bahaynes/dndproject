<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { get } from 'svelte/store';
	import { API_BASE_URL } from '$lib/config';
	import type { Mission } from '$lib/types';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let missions: Mission[] = [];
	let loading = true;
	let error = '';
	let myCharacterId: number | undefined;

	// Reactive update for character ID
	$: myCharacterId = $auth.user?.active_character?.id;

	onMount(async () => {
		await fetchMissions();
	});

	async function fetchMissions() {
		loading = true;
		error = '';
		try {
			const authState = get(auth);
			const res = await fetch(`${API_BASE_URL}/missions/`, {
				headers: {
					Authorization: `Bearer ${authState.token}`
				}
			});

			if (res.ok) {
				missions = await res.json();
			} else {
				error = 'Failed to load missions.';
			}
		} catch (e) {
			error = 'An error occurred while loading missions.';
		} finally {
			loading = false;
		}
	}

	async function handleSignup(missionId: number) {
		error = '';
		try {
			const authState = get(auth);
			const res = await fetch(`${API_BASE_URL}/missions/${missionId}/signup`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${authState.token}`
				}
			});

			if (res.ok) {
				await fetchMissions();
			} else {
				const errData = await res.json();
				error = errData.detail || 'Failed to sign up for mission.';
			}
		} catch (e) {
			error = 'An error occurred during signup.';
		}
	}

	function isUserInMission(mission: Mission) {
		if (!myCharacterId) return false;
		return mission.players.some((p) => p.id === myCharacterId);
	}
</script>

<div class="container mx-auto max-w-5xl p-4">
	<div class="border-base-content/10 mb-8 flex items-center justify-between border-b pb-4">
		<h1 class="text-primary text-4xl font-[var(--font-cinzel)] font-bold">Mission Board</h1>
		<button class="btn btn-ghost btn-sm" on:click={fetchMissions}>Refresh</button>
	</div>

	{#if error}
		<div class="alert alert-error mb-6 shadow-lg">
			<div>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-6 w-6 flex-shrink-0 stroke-current"
					fill="none"
					viewBox="0 0 24 24"
					><path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
					/></svg
				>
				<span>{error}</span>
			</div>
		</div>
	{/if}

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else if missions.length === 0}
		<div class="card bg-base-200 p-12 text-center opacity-70">
			<h2 class="text-xl font-bold">The board is currently empty.</h2>
			<p>Check back later for new adventurous opportunities from the guild.</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
			{#each missions as mission}
				<div class="card bg-base-100 border-base-content/10 flex h-full flex-col border shadow-xl">
					<div class="card-body">
						<div class="mb-2 flex items-start justify-between">
							<h2 class="card-title font-[var(--font-cinzel)]">{mission.name}</h2>
							<div
								class="badge {mission.status === 'Available'
									? 'badge-success'
									: 'badge-warning'} badge-sm"
							>
								{mission.status}
							</div>
						</div>

						<p class="mb-4 line-clamp-3 text-sm">
							{mission.description || 'No mission brief available.'}
						</p>

						<!-- Rewards section -->
						<div class="bg-base-200 mb-4 rounded-lg p-3">
							<span class="mb-2 block text-[10px] font-bold uppercase opacity-50"
								>Potential Rewards</span
							>
							<div class="flex flex-wrap gap-2">
								{#each mission.rewards as reward}
									{#if reward.xp}
										<div class="badge badge-outline badge-xs">+{reward.xp} XP</div>
									{/if}
									{#if reward.scrip}
										<div class="badge badge-outline badge-primary badge-xs">
											+{reward.scrip} Scrip
										</div>
									{/if}
									{#if reward.item}
										<div class="badge badge-secondary badge-xs">{reward.item.name}</div>
									{/if}
								{/each}
							</div>
						</div>

						<div class="mt-auto">
							<div class="mb-4 flex items-center gap-2">
								<div class="avatar-group -space-x-3 rtl:space-x-reverse">
									{#each mission.players.slice(0, 3) as player}
										<div class="avatar placeholder border-base-100">
											<div
												class="bg-primary text-primary-content w-6 rounded-full text-[8px] font-bold"
											>
												{player.name.charAt(0)}
											</div>
										</div>
									{/each}
									{#if mission.players.length > 3}
										<div class="avatar placeholder border-base-100">
											<div
												class="bg-neutral text-neutral-content w-6 rounded-full text-[8px] font-bold"
											>
												+{mission.players.length - 3}
											</div>
										</div>
									{/if}
								</div>
								<span class="text-xs opacity-60">
									{mission.players.length === 0
										? 'Seeking members'
										: `${mission.players.length} members signed up`}
								</span>
							</div>

							<div class="card-actions justify-end">
								{#if isUserInMission(mission)}
									<button class="btn btn-sm btn-disabled w-full">Already Signed Up</button>
								{:else if mission.status === 'Available'}
									<button
										class="btn btn-sm btn-primary w-full"
										on:click={() => handleSignup(mission.id)}
										disabled={!myCharacterId}
									>
										{!myCharacterId ? 'No Character Found' : 'Sign Up'}
									</button>
								{:else}
									<button class="btn btn-sm btn-disabled w-full">Mission {mission.status}</button>
								{/if}
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
