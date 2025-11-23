<script lang="ts">
  export let eyebrow: string | undefined = undefined;
  export let title: string;
  export let description: string | undefined = undefined;
</script>

<div class="section-header">
  <div class="space-y-1">
    {#if eyebrow}
      <p class="pill w-fit text-xs uppercase tracking-wide">{eyebrow}</p>
    {/if}
    <h2 class="text-2xl font-bold">{title}</h2>
    {#if description}
      <p class="muted max-w-2xl text-sm sm:text-base">{description}</p>
    {/if}
  </div>
  <div class="flex flex-wrap items-center gap-2">
    <slot name="actions" />
  </div>
</div>
