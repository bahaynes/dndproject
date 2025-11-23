<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { auth } from '$lib/auth';
  import SectionHeader from '$lib/components/SectionHeader.svelte';
  import MissionList from '$lib/components/MissionList.svelte';
  import type { Mission } from '$lib/types';
  import { fetchMissions, createMission as apiCreateMission } from '$lib/api';

  let missions: Mission[] = [];
  let loading = true;
  let error: string | null = null;
  let creating = false;
  let feedback: string | null = null;

  let missionForm = {
    title: '',
    summary: '',
    status: 'available',
    target_hex: '',
  };

  const isGM = () => get(auth).user?.role === 'admin';

  onMount(loadMissions);

  async function loadMissions() {
    loading = true;
    error = null;
    try {
      const token = get(auth).token ?? undefined;
      missions = await fetchMissions(token);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load missions';
    } finally {
      loading = false;
    }
  }

  async function createMission() {
    feedback = null;

    if (!isGM()) {
      feedback = 'Only GMs can create missions.';
      return;
    }

    if (!missionForm.title) {
      feedback = 'Title is required.';
      return;
    }

    const token = get(auth).token;
    if (!token) {
      feedback = 'Log in with GM credentials to add missions.';
      return;
    }

    creating = true;
    try {
      await apiCreateMission(
        {
          title: missionForm.title,
          summary: missionForm.summary || null,
          status: missionForm.status || 'available',
          target_hex: missionForm.target_hex || null,
        },
        token,
      );
      feedback = 'Mission created and added to the dossier list.';
      missionForm = { title: '', summary: '', status: 'available', target_hex: '' };
      await loadMissions();
    } catch (err) {
      feedback = err instanceof Error ? err.message : 'Failed to create mission';
    } finally {
      creating = false;
    }
  }
</script>

<div class="page-container space-y-8">
  <SectionHeader
    eyebrow="Mission Control"
    title="Mission dossiers"
    description="Organize every target hex and dossier so any GM can pick up the thread."
  >
    <div slot="actions" class="flex gap-2">
      <a class="btn btn-ghost" href="/">Back to hub</a>
    </div>
  </SectionHeader>

  <MissionList missions={missions} isLoading={loading} error={error} />

  <div class="panel p-6 space-y-4">
    <div class="flex items-center justify-between gap-2">
      <h3 class="text-lg font-semibold">Create mission</h3>
      <span class="pill">GM only</span>
    </div>
    {#if !isGM()}
      <p class="muted text-sm">Log in as a GM to add new missions and dossiers.</p>
    {:else}
      <form class="space-y-3" on:submit|preventDefault={createMission}>
        <div class="space-y-1">
          <label class="label" for="title">Title</label>
          <input
            id="title"
            class="input-field"
            type="text"
            required
            bind:value={missionForm.title}
            placeholder="Escort the archivist to A3"
          />
        </div>
        <div class="space-y-1">
          <label class="label" for="summary">Summary</label>
          <textarea
            id="summary"
            class="input-field min-h-[90px]"
            placeholder="Objective, risk posture, or hooks for this mission."
            bind:value={missionForm.summary}
          ></textarea>
        </div>
        <div class="grid md:grid-cols-2 gap-3">
          <div class="space-y-1">
            <label class="label" for="status">Status</label>
            <select id="status" class="input-field" bind:value={missionForm.status}>
              <option value="available">Available</option>
              <option value="planning">Planning</option>
              <option value="in-progress">In progress</option>
              <option value="retired">Retired</option>
            </select>
          </div>
          <div class="space-y-1">
            <label class="label" for="hex">Target hex</label>
            <input
              id="hex"
              class="input-field"
              type="text"
              bind:value={missionForm.target_hex}
              placeholder="B2"
            />
          </div>
        </div>
        {#if feedback}
          <p class="text-sm text-amber-200">{feedback}</p>
        {/if}
        <div class="flex gap-2">
          <button class="btn btn-primary" type="submit" disabled={creating}>
            {creating ? 'Creating...' : 'Add mission'}
          </button>
          <a class="btn btn-muted" href="/dashboard/admin/sessions">Session scheduling</a>
        </div>
      </form>
    {/if}
  </div>
</div>
