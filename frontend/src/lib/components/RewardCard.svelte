<script lang="ts">
    import type { MissionReward } from '$lib/types';
    import { createEventDispatcher } from 'svelte';

    export let reward: MissionReward;
    export let isRevealed = !reward.is_hidden;
    export let interactive = true;

    const dispatch = createEventDispatcher();

    function handleClick() {
        if (!interactive || !reward.is_hidden) return;
        isRevealed = true;
        dispatch('reveal', { reward });
    }
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div
    class="reward-card-container {interactive && reward.is_hidden && !isRevealed ? 'cursor-pointer hover:scale-105' : ''}"
    on:click={handleClick}
>
    <div class="reward-card-inner {isRevealed ? 'revealed' : ''}">
        <!-- Front: The Hint (Hidden state) -->
        <div class="reward-card-front card bg-base-300 border border-base-content/20 shadow-md">
            <div class="card-body p-3 flex flex-col items-center justify-center text-center">
                <span class="text-2xl mb-1 opacity-50">?</span>
                <span class="text-xs font-bold text-base-content/70">{reward.hint || 'Mystery Reward'}</span>
            </div>
        </div>

        <!-- Back: The Actual Reward (Revealed state) -->
        <div class="reward-card-back card border border-base-content/20 shadow-md">
            <div class="card-body p-3 flex items-center justify-center">
                {#if reward.gold}
                    <div class="badge badge-warning badge-sm">+{reward.gold} Gold</div>
                {/if}
                {#if reward.item}
                    <div class="badge badge-secondary badge-sm truncate max-w-full" title={reward.item.name}>{reward.item.name}</div>
                {/if}
            </div>
        </div>
    </div>
</div>

<style>
    .reward-card-container {
        perspective: 1000px;
        width: 120px;
        height: 60px;
        transition: transform 0.2s ease-in-out;
    }

    .reward-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: center;
        transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        transform-style: preserve-3d;
    }

    .reward-card-inner.revealed {
        transform: rotateY(180deg);
    }

    .reward-card-front, .reward-card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
    }

    .reward-card-back {
        transform: rotateY(180deg);
        background-color: var(--fallback-b1,oklch(var(--b1)/var(--tw-bg-opacity, 1)));
    }
</style>
