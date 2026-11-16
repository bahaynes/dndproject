<script lang="ts">
	import { page } from '$app/stores';

	export let items: { label: string; href: string }[] = [];

	$: currentPath = $page?.url?.pathname ?? '';
</script>

<nav aria-label="Section navigation" class="mb-6 border-b border-base-content/10">
	<div class="flex gap-1 overflow-x-auto">
		{#each items as item}
			{@const active = currentPath === item.href || (item.href !== '/' && currentPath.startsWith(item.href + '/'))}
			<a
				href={item.href}
				class="whitespace-nowrap border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors {active
					? 'border-primary text-primary'
					: 'border-transparent text-base-content/65 hover:border-base-content/20 hover:text-base-content'}"
			>
				{item.label}
			</a>
		{/each}
	</div>
</nav>
