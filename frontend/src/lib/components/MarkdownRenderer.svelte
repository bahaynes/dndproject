<script lang="ts">
	import snarkdown from 'snarkdown';
	import DOMPurify from 'dompurify';

	let { content = '' } = $props();

	// Sanitize and parse markdown to HTML
	let html = $derived(DOMPurify.sanitize(snarkdown(content)));
</script>

<div class="prose prose-sm max-w-none prose-neutral dark:prose-invert">
	{@html html}
</div>

<style>
	/* Subtle adjustments for RPG content if needed */
	:global(.prose h1) {
		font-family: var(--font-cinzel, serif);
	}
	:global(.prose h2) {
		font-family: var(--font-cinzel, serif);
	}
	:global(.prose h3) {
		font-family: var(--font-cinzel, serif);
	}
</style>
