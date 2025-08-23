import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter({
			// default options are fine
			pages: 'build',
			assets: 'build',
			fallback: 'index.html',
			precompress: false
		}),

		// This is important to make relative paths work correctly
		// since we will be serving from the backend root.
		paths: {
			base: ''
		}
	}
};

export default config;
