<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { auth } from '$lib/auth';
  import SectionHeader from '$lib/components/SectionHeader.svelte';
  import type { Mission } from '$lib/types';
  import { fetchMission, updateMission as apiUpdateMission } from '$lib/api';

  export let params: { id: string };

  let mission: Mission | null = null;
  let loading = true;
  let error: string | null = null;
  let saving = false;

  let form = {
    title: '',
    summary: '',
    status: 'available',
    target_hex: '',
    dossier_data: '',
  };

  const isGM = () => get(auth).user?.role === 'admin';

  onMount(loadMission);

  async function loadMission() {
    loading = true;
    error = null;
    try {
      const token = get(auth).token ?? undefined;
      mission = await fetchMission(params.id, token);
      form = {
        title: mission.title,
        summary: mission.summary || '',
        status: mission.status || 'available',
        target_hex: mission.target_hex || '',
        dossier_data: mission.dossier_data ? JSON.stringify(mission.dossier_data, null, 2) : '',
      };
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load mission';
    } finally {
      loading = false;
    }
  }

  async function saveMission() {
    error = null;

    if (!isGM()) {
      error = 'GM access required to edit missions.';
      return;
    }

    const token = get(auth).token;
    if (!token) {
      error = 'Please log in to update missions.';
      return;
    }

    let dossierData: Record<string, unknown> | null = null;
    if (form.dossier_data) {
      try {
        dossierData = JSON.parse(form.dossier_data);
      } catch {
        error = 'Dossier JSON is invalid. Please fix the formatting.';
        return;
      }
    }

    saving = true;
    try {
      mission = await apiUpdateMission(
        params.id,
        {
          title: form.title,
          summary: form.summary || null,
          status: form.status || 'available',
          target_hex: form.target_hex || null,
          dossier_data: dossierData,
        },
        token,
      );
      form.dossier_data = mission.dossier_data ? JSON.stringify(mission.dossier_data, null, 2) : '';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to update mission';
    } finally {
      saving = false;
    }
  }
</script>

<div class="page-container space-y-6">
  <SectionHeader
    eyebrow="Mission Dossier"
    title={mission ? mission.title : 'Mission detail'}
    description="Target hex, dossier, and roster readiness for this mission."
  >
    <div slot="actions" class="flex gap-2">
      <a class="btn btn-ghost" href="/missions">Back to missions</a>
    </div>
  </SectionHeader>

  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}

  {#if loading}
    <div class="panel p-4">Loading mission...</div>
  {:else if mission}
    <div class="panel p-6 space-y-4">
      <div class="grid md:grid-cols-3 gap-3">
        <div class="panel panel-strong p-3 rounded-xl">
          <p class="muted text-xs uppercase tracking-wide">Status</p>
          <p class="text-xl font-semibold">{mission.status || 'available'}</p>
        </div>
        <div class="panel panel-strong p-3 rounded-xl">
          <p class="muted text-xs uppercase tracking-wide">Target Hex</p>
          <p class="text-xl font-semibold">{mission.target_hex || 'Unassigned'}</p>
        </div>
        <div class="panel panel-strong p-3 rounded-xl">
          <p class="muted text-xs uppercase tracking-wide">Rostered Characters</p>
          <p class="text-xl font-semibold">{mission.players?.length || 0}</p>
        </div>
      </div>

      <div class="space-y-2">
        <h3 class="text-lg font-semibold">Summary</h3>
        <p class="muted leading-relaxed">{mission.summary || 'No summary provided yet.'}</p>
      </div>

      {#if mission.players?.length}
        <div class="space-y-2">
          <h3 class="text-lg font-semibold">Roster</h3>
          <div class="flex flex-wrap gap-2">
            {#each mission.players as player}
              <span class="badge badge-ghost">{player.name}</span>
            {/each}
          </div>
        </div>
      {/if}
    </div>

    <div class="panel p-6 space-y-3">
      <h3 class="text-lg font-semibold">Dossier</h3>
      {#if mission.dossier_data}
        <pre class="code-block">{JSON.stringify(mission.dossier_data, null, 2)}</pre>
      {:else}
        <p class="muted text-sm">No dossier content has been added for this mission.</p>
      {/if}
    </div>

    {#if isGM()}
      <div class="panel p-6 space-y-4">
        <div class="flex items-center justify-between gap-2">
          <h3 class="text-lg font-semibold">Edit mission</h3>
          <span class="pill">GM only</span>
        </div>
        <form class="space-y-3" on:submit|preventDefault={saveMission}>
          <div class="space-y-1">
            <label class="label" for="title">Title</label>
            <input id="title" class="input-field" type="text" required bind:value={form.title} />
          </div>
          <div class="space-y-1">
            <label class="label" for="summary">Summary</label>
            <textarea
              id="summary"
              class="input-field min-h-[90px]"
              bind:value={form.summary}
              placeholder="Objective or hooks for this mission."
            ></textarea>
          </div>
          <div class="grid md:grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="label" for="status">Status</label>
              <select id="status" class="input-field" bind:value={form.status}>
                <option value="available">Available</option>
                <option value="planning">Planning</option>
                <option value="in-progress">In progress</option>
                <option value="retired">Retired</option>
              </select>
            </div>
            <div class="space-y-1">
              <label class="label" for="hex">Target hex</label>
              <input id="hex" class="input-field" type="text" bind:value={form.target_hex} />
            </div>
          </div>
          <div class="space-y-1">
            <label class="label" for="dossier">Dossier JSON</label>
            <textarea
              id="dossier"
              class="input-field font-mono text-sm min-h-[200px]"
              bind:value={form.dossier_data}
            ></textarea>
            <p class="muted text-xs">Paste structured encounters and rewards for this mission.</p>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-primary" type="submit" disabled={saving}>
              {saving ? 'Saving...' : 'Save mission'}
            </button>
            <a class="btn btn-muted" href="/dashboard/admin/sessions">Session admin</a>
          </div>
        </form>
      </div>
    {/if}
  {/if}
</div>
