import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';
import path from 'path';
import { svelteTesting } from '@testing-library/svelte/vite';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit(),
        svelteTesting(),
	],
	server: {
		host: true,
		proxy: {
			'/api': {
				target: 'http://127.0.0.1:8000',
				changeOrigin: true,
			}
		},
		allowedHosts: [
			'dndproject.bahaynes.com',
		]
	},
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		globals: true,
		reporters: process.env.CI ? ['default', 'junit'] : ['default'],
		outputFile: process.env.CI ? 'reports/junit.xml' : undefined,
		environment: 'jsdom',
		setupFiles: './src/setupTests.ts',
	},
	resolve: {
		alias: {
		  $lib: path.resolve(__dirname, './src/lib'),
		},
	},
});
