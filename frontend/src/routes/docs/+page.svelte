<script lang="ts">
	import PageHeader from '$lib/components/PageHeader.svelte';
</script>

<div class="page-container">
	<PageHeader
		title="Player Guide & Docs"
		subtitle="What is West Marches, and how do you use this hub to play?"
	>
		<div slot="actions">
			<a href="/dashboard" class="btn btn-primary btn-sm">Back to Dashboard</a>
		</div>
	</PageHeader>

	<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
		<section class="panel p-6 space-y-3">
			<p class="section-label">The Format</p>
			<h2 class="text-lg font-semibold text-base-content">What is West Marches?</h2>
			<p class="text-sm text-base-content/80 leading-relaxed">
				West Marches is an open-table D&amp;D 5e campaign with no fixed weekly party. Anyone can play
				when their schedule lines up, and every expedition happens in the same persistent world.
			</p>
			<ul class="list-disc pl-5 space-y-1.5 text-sm text-base-content/75">
				<li><strong>Drop-in, drop-out:</strong> Play when you're free; skip weeks without holding up the table.</li>
				<li><strong>Player-driven exploration:</strong> The party chooses which quest or map hex to tackle.</li>
				<li><strong>Persistent consequences:</strong> Time passes, hexes get discovered, and your GP &amp; XP stay with your character.</li>
			</ul>
		</section>

		<section class="panel p-6 space-y-3">
			<p class="section-label">How To Play</p>
			<h2 class="text-lg font-semibold text-base-content">Using This Hub</h2>
			<ol class="list-decimal pl-5 space-y-2.5 text-sm text-base-content/80">
				<li>
					<strong>Create your character:</strong> Add your character's name, class, and external sheet link
					(D&amp;D Beyond or Foundry) on <a href="/characters" class="text-primary hover:underline">My Characters</a>.
				</li>
				<li>
					<strong>Claim a seat ("I'm Playing"):</strong> Pick an upcoming session on the
					<a href="/dashboard" class="text-primary hover:underline">Dashboard</a> to reserve your spot. If you have
					alts, you can swap characters right on the session card up until game time.
				</li>
				<li>
					<strong>Vote on what to run:</strong> Once seated, propose or vote on a
					<a href="/missions" class="text-primary hover:underline">Posted Quest</a> or a
					<a href="/maps" class="text-primary hover:underline">Discovered Hex</a>—or decide together night-of.
				</li>
				<li>
					<strong>Collect loot &amp; gear up:</strong> After the DM logs the session, check your recap on
					<a href="/sessions" class="text-primary hover:underline">Sessions</a>, write a field report, and spend your
					GP at the <a href="/store" class="text-primary hover:underline">Quartermaster Store</a>.
				</li>
			</ol>
		</section>
	</div>
</div>
