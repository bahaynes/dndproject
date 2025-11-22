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
				target: 'http://backend:8000',
				changeOrigin: true,
				// Keep the /api prefix so requests reach FastAPI routes mounted at /api/*
				rewrite: (path) => path, 
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
