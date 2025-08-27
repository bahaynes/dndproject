import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit()
	],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		globals: true,
		environment: 'jsdom',
		setupFiles: './src/setupTests.ts',
	},
	resolve: {
		alias: {
		  $lib: path.resolve(__dirname, './src/lib'),
		},
	},
});
