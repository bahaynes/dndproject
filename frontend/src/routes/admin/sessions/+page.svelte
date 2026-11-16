<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	onMount(() => {
		goto('/sessions', { replaceState: true });
	});
</script>

<div class="flex justify-center py-20">
	<span class="loading loading-lg loading-spinner text-primary"></span>
</div>
