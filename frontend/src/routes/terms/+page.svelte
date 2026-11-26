<script lang="ts">
	import PageHeader from '$lib/components/PageHeader.svelte';
	import { LAST_UPDATED, CONTACT_LABEL, CONTACT_URL } from '$lib/legal';
</script>

<svelte:head>
	<title>Terms of Service · West Marches</title>
</svelte:head>

<div class="page-container">
	<PageHeader title="Terms of Service" subtitle="Last updated {LAST_UPDATED}" />

	<article
		class="panel mx-auto max-w-3xl space-y-6 p-6 text-sm leading-relaxed text-base-content/80"
	>
		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">The service</h2>
			<p>
				West Marches is a free hobby tool for running D&amp;D campaigns organised on Discord. It is
				provided as-is, with no guarantee of uptime, and data could be lost. Keep your own copy of
				anything you can't afford to lose.
			</p>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Who can use it</h2>
			<p>
				You sign in with Discord and can join a campaign only if you are a member of that campaign's
				Discord server with the required role. Discord's
				<a href="https://discord.com/terms" class="text-primary hover:underline" rel="noopener"
					>Terms of Service</a
				>
				and
				<a href="https://discord.com/guidelines" class="text-primary hover:underline" rel="noopener"
					>Community Guidelines</a
				>
				also apply to your use of this site.
			</p>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Acceptable use</h2>
			<p>
				Don't post anything illegal, harassing or hateful, don't try to access other campaigns' data
				or break the site, and don't use it to spam. GMs can remove content and sign-ups in their
				campaign and control who can join through their Discord server's roles. We can remove
				accounts or content that break these rules.
			</p>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Your content</h2>
			<p>
				You keep ownership of what you post. By posting it, you allow the site to store it and show
				it to the members of your campaign, as long as it is part of that campaign.
			</p>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Connected apps</h2>
			<p>
				A GM may connect an AI assistant or another app to their campaign. The GM is responsible for
				that choice, and that app's own terms apply to it. What data it receives is described in the
				<a href="/privacy" class="text-primary hover:underline">Privacy Policy</a>.
			</p>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Changes and ending the service</h2>
			<p>
				The site may change or shut down at any time. If these terms change, the date at the top
				will change, and significant changes will be announced in the campaign Discord servers.
				Continuing to use the site after a change means you accept the new terms.
			</p>
		</section>

		<section class="space-y-2">
			<h2 class="text-lg font-semibold text-base-content">Privacy and contact</h2>
			<p>
				How we handle your data is described in the
				<a href="/privacy" class="text-primary hover:underline">Privacy Policy</a>. For questions,
				<a href={CONTACT_URL} class="text-primary hover:underline">{CONTACT_LABEL}</a>.
			</p>
		</section>
	</article>
</div>
