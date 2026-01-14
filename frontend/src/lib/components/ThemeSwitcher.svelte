<script lang="ts">
  import { onMount } from 'svelte';

  const themes = [
    { name: 'Dark (Forest)', value: 'forest' },
    { name: 'Abyss (Halloween)', value: 'halloween' },
    { name: 'Neutral (Business)', value: 'business' },
    { name: 'Light (Fantasy)', value: 'fantasy' }
  ];

  let currentTheme = 'forest';

  onMount(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme && themes.some(t => t.value === savedTheme)) {
      currentTheme = savedTheme;
    } else {
        currentTheme = 'forest';
    }
    applyTheme(currentTheme);
  });

  function applyTheme(theme: string) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    currentTheme = theme;
  }
</script>

<div class="dropdown dropdown-end">
  <div tabindex="0" role="button" class="btn btn-ghost">
    Theme
    <svg width="12px" height="12px" class="h-2 w-2 fill-current opacity-60 inline-block ml-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2048 2048"><path d="M1799 349l242 241-1017 1017L7 590l242-241 775 775 775-775z"></path></svg>
  </div>
  <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-300 rounded-box w-52">
    {#each themes as theme}
      <li><button class:active={currentTheme === theme.value} on:click={() => applyTheme(theme.value)}>{theme.name}</button></li>
    {/each}
  </ul>
</div>
