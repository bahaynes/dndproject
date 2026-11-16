import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';
import { svelteTesting } from '@testing-library/svelte/vite';

const isCI = Boolean((globalThis as { process?: { env?: { CI?: string } } }).process?.env?.CI);

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
				// rewrite: (path) => path.replace(/^\/api/, ''), // Removed rewrite to support backend expecting /api
			}
		},
		allowedHosts: [
			'dndproject.bahaynes.com',
		]
	},
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		globals: true,
		reporters: isCI ? ['default', 'junit'] : ['default'],
		outputFile: isCI ? 'reports/junit.xml' : undefined,
		environment: 'jsdom',
		setupFiles: './src/setupTests.ts',
	},
	resolve: {
		alias: {
		  $lib: new URL('./src/lib', import.meta.url).pathname,
		},
	},
});
