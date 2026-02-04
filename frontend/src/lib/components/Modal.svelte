<script lang="ts">
	export let show = false;
	export let title = '';
	export let onClose: () => void;
</script>

{#if show}
	<div class="modal modal-open">
		<div class="modal-box border-primary/20 bg-base-100 relative border shadow-2xl">
			<button class="btn btn-sm btn-circle absolute right-2 top-2" on:click={onClose}>✕</button>
			{#if title}
				<h3 class="mb-4 text-lg font-[var(--font-cinzel)] font-bold">{title}</h3>
			{/if}
			<div class="py-4">
				<slot />
			</div>
			<div class="modal-action">
				<slot name="action" />
			</div>
		</div>
		<div
			class="modal-backdrop bg-black/50"
			on:click={onClose}
			on:keypress={onClose}
			role="button"
			tabindex="0"
			aria-label="Close modal"
		></div>
	</div>
{/if}
