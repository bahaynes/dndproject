<script lang="ts">
  export let show = false;
  export let title = "";
  export let onClose: () => void;
</script>

{#if show}
  <div class="modal modal-open">
    <div class="modal-box relative border border-primary/20 bg-base-100 shadow-2xl">
      <button 
        class="btn btn-sm btn-circle absolute right-2 top-2" 
        on:click={onClose}
      >✕</button>
      {#if title}
        <h3 class="text-lg font-bold font-[var(--font-cinzel)] mb-4">{title}</h3>
      {/if}
      <div class="py-4">
        <slot />
      </div>
      <div class="modal-action">
        <slot name="action" />
      </div>
    </div>
    <div class="modal-backdrop bg-black/50" on:click={onClose} />
  </div>
{/if}
