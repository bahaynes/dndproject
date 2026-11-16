<script lang="ts">
	export let title: string;
	export let subtitle: string = '';
</script>

<header class="mb-6 flex flex-col justify-between gap-4 border-b border-base-content/10 pb-5 sm:flex-row sm:items-end">
	<div class="min-w-0">
		<h1 class="text-2xl font-semibold tracking-wide text-base-content sm:text-3xl">
			{title}
		</h1>
		{#if subtitle}
			<p class="mt-1 text-sm text-base-content/65">{subtitle}</p>
		{/if}
	</div>
	{#if $$slots.actions}
		<div class="flex flex-wrap items-center gap-2 shrink-0">
			<slot name="actions" />
		</div>
	{/if}
</header>
