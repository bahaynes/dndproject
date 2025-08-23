<script lang="ts">
	import { auth } from '$lib/stores/auth';
</script>

<div class="container mx-auto p-8">
	<h1 class="text-2xl font-bold mb-4">Dashboard</h1>
	{#if $auth.user}
		<p>Welcome, <span class="font-semibold">{$auth.user.username}</span>!</p>
		<p>This is your protected dashboard. Only logged-in users can see this.</p>

		<div class="mt-6">
			<h2 class="text-xl font-semibold">Your Characters</h2>
			{#if $auth.user.characters && $auth.user.characters.length > 0}
				<ul>
					{#each $auth.user.characters as character}
						<li class="mt-2 p-4 border rounded-md">
							<h3 class="font-bold text-lg">{character.name}</h3>
							{#if character.description}
								<p>{character.description}</p>
							{/if}
						</li>
					{/each}
				</ul>
			{:else}
				<p>You don't have any characters yet.</p>
			{/if}
		</div>
	{:else}
		<p>Loading user data...</p>
	{/if}
</div>
