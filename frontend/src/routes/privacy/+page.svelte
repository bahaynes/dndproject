<script lang="ts">
	import PageHeader from '$lib/components/PageHeader.svelte';
	import { LAST_UPDATED, CONTACT_LABEL, CONTACT_URL } from '$lib/legal';
</script>

<svelte:head>
	<title>Privacy Policy · West Marches</title>
</svelte:head>

<div class="page-container">
	<PageHeader title="Privacy Policy" subtitle="Last updated {LAST_UPDATED}" />

	<article
		class="panel mx-auto max-w-3xl space-y-6 p-6 text-sm leading-relaxed text-base-content/80"
	>
		<p>
			West Marches is a hobby tool for running Discord-based D&amp;D campaigns. This page says what
			data the site collects, where it is kept, who can see it, and how to have it removed. It
			covers what <em>we</em> do with your data, not what other campaign members do with things they
			can see.
		</p>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">What we collect</h2>
			<ul class="list-disc space-y-1.5 pl-5">
				<li>
					<strong>From Discord, when you log in:</strong> your Discord user ID, username and avatar.
					We ask Discord for the <code>identify</code> and <code>guilds</code> permissions only. We do
					not receive your email address.
				</li>
				<li>
					<strong>Server membership and roles:</strong> when you join a campaign, we check which Discord
					servers you are in and which roles you hold in the campaign's server, to decide whether you
					are a player or a GM. We store the result (your campaign role), not your server list or role
					list.
				</li>
				<li>
					<strong>What you create on the site:</strong> characters, mission and session sign-ups, and
					anything you or other members write on the campaign board, maps or ledger.
				</li>
				<li>
					<strong>Request logs:</strong> our hosting provider records standard request logs (such as
					IP address, time and page requested). Our application logs also record your Discord ID and
					username when you log in. These are used for troubleshooting.
				</li>
			</ul>
			<p>We do not use analytics, advertising trackers or tracking cookies.</p>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Your Discord access token</h2>
			<p>
				When you log in, Discord gives us a short-lived access token. It is passed to your browser
				and held in session storage only while you choose a campaign, and is used only to ask
				Discord which servers you are in. It is cleared once you pick a campaign or close the tab,
				and we do not save it on our servers. After that, the site uses its own login token, kept in
				your browser's local storage until you log out.
			</p>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Where it is kept</h2>
			<ul class="list-disc space-y-1.5 pl-5">
				<li>The database is PostgreSQL hosted by Neon.</li>
				<li>The site runs on Google Cloud Run; map images are stored in Google Cloud Storage.</li>
				<li>
					Test versions of the site, created while changes are being reviewed, use a temporary copy
					of the production database. Each copy is deleted when the change is closed, or after 14
					days.
				</li>
			</ul>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Who can see it</h2>
			<ul class="list-disc space-y-1.5 pl-5">
				<li>
					Other members of the same campaign can see your username, avatar, characters and what you
					post in that campaign. Campaigns cannot see each other's data.
				</li>
				<li>
					Your browser loads avatars from Discord and fonts from Google Fonts, so those services see
					your IP address when the page loads.
				</li>
				<li>
					<strong>Connected apps:</strong> if a GM connects an AI assistant or another app to their campaign,
					campaign data that GM can see, including what players have posted, is sent to that app's provider
					and handled under that provider's terms. This is not limited to one AI company.
				</li>
				<li>We do not sell your data or share it with anyone else.</li>
			</ul>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">How long we keep it, and deletion</h2>
			<p>
				Data is kept for as long as the campaign exists on the site. A GM can remove content from
				their campaign at any time. To have your own data removed, or for any privacy question, <a
					href={CONTACT_URL}
					class="text-primary hover:underline">{CONTACT_LABEL}</a
				>. We will delete your account records and anything only you created; posts that are part of
				shared campaign history may be kept with your name removed.
			</p>
			<p>
				You can also revoke the site's access at any time in Discord under User Settings →
				Authorized Apps.
			</p>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Changes</h2>
			<p>
				If this policy changes, the date at the top will change. Significant changes will also be
				announced in the campaign Discord servers. See also the
				<a href="/terms" class="text-primary hover:underline">Terms of Service</a>.
			</p>
		</section>
	</article>
</div>
