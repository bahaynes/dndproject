<script lang="ts">
    import { auth } from '$lib/auth';
</script>

<div class="page-container space-y-14">
    <section class="grid items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div class="space-y-6">
            <div class="pill w-fit">Westmarches Command</div>
            <h1 class="text-4xl sm:text-5xl font-bold leading-tight">
                Rally your adventurers. Track every quest. Conquer the frontier.
            </h1>
            <p class="text-lg muted max-w-2xl">
                A hub built for sprawling Westmarches campaigns—organize sessions, wrangle players, and keep your
                story threads from slipping into the void.
            </p>
            <div class="flex flex-wrap gap-3">
                {#if $auth.isAuthenticated}
                    <a href="/dashboard" class="btn btn-primary">Enter your dashboard</a>
                    <a href="/sessions" class="btn btn-ghost">Browse sessions</a>
                {:else}
                    <a href="/register" class="btn btn-primary">Join the realm</a>
                    <a href="/login" class="btn btn-ghost">I already carry a sigil</a>
                {/if}
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div class="panel p-4">
                    <div class="text-sm text-amber-200 uppercase tracking-wide">Session roster</div>
                    <div class="text-2xl font-semibold mt-1">Live & upcoming</div>
                </div>
                <div class="panel p-4">
                    <div class="text-sm text-red-200 uppercase tracking-wide">Attendance</div>
                    <div class="text-2xl font-semibold mt-1">Instant signups</div>
                </div>
                <div class="panel p-4">
                    <div class="text-sm text-amber-200 uppercase tracking-wide">Admins</div>
                    <div class="text-2xl font-semibold mt-1">Full control</div>
                </div>
            </div>
        </div>

        <div class="panel glow-border parchment p-6 space-y-5">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-amber-200">Quest board</p>
                    <h2 class="text-2xl font-semibold mt-1">Tonight's hook</h2>
                </div>
                <span class="badge">Sanctuary Seal</span>
            </div>
            <p class="leading-relaxed">
                Rumors of a fallen star have the guild restless. Veteran guides want extra scouts, while the archivist
                demands samples before dawn. Assemble a balanced party and mark your intent on the ledger below.
            </p>
            <div class="faded-line"></div>
            <div class="card-grid">
                <div class="card panel-strong">
                    <div class="card-body">
                        <p class="text-sm text-amber-100 uppercase tracking-wide">Hooks</p>
                        <p class="text-lg font-semibold">Northern Wilds</p>
                        <p class="muted">Hexed obelisk, possible hag coven, bring cold iron.</p>
                    </div>
                </div>
                <div class="card panel-strong">
                    <div class="card-body">
                        <p class="text-sm text-amber-100 uppercase tracking-wide">Needs</p>
                        <p class="text-lg font-semibold">Seeker & Scout</p>
                        <p class="muted">Lightfooted eyes to trace the meteor's trail before rivals arrive.</p>
                    </div>
                </div>
            </div>
            <div class="flex gap-3 flex-wrap">
                <a href="/sessions" class="btn btn-primary">View session board</a>
                <a href="/dashboard" class="btn btn-muted">Open roster</a>
            </div>
        </div>
    </section>

    <section class="space-y-4">
        <div class="faded-line"></div>
        <div class="card-grid">
            <div class="card">
                <div class="card-body">
                    <div class="pill w-fit">Session Ledger</div>
                    <h3 class="card-title">Keep every expedition aligned</h3>
                    <p class="muted">
                        Schedule, track attendance, and ensure your Westmarches stay fair with transparent player slots.
                    </p>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="pill w-fit">Player View</div>
                    <h3 class="card-title">Players see what matters</h3>
                    <p class="muted">
                        Clean sign-up flow with instant feedback on status, timing, and what to bring to the table.
                    </p>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="pill w-fit">Admin Tools</div>
                    <h3 class="card-title">Hosts stay in control</h3>
                    <p class="muted">
                        Manage rosters, review your adventurers, and keep the campaign's pulse steady across sessions.
                    </p>
                </div>
            </div>
        </div>
    </section>
</div>
