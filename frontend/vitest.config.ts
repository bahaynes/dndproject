import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

export default defineConfig({
  plugins: [
    // Disable HMR when running Vitest to avoid SSR issues
    svelte({ hot: false })
  ],
  test: {
    globals: true,                // Allows using test globals like `describe`, `it`
    environment: 'jsdom',         // Simulate browser environment
    setupFiles: './src/setupTests.ts', // Optional setup file
    conditions: ['browser'],      // SSR-safe fix
    include: ['src/**/*.{test,spec}.{ts,js}'], // Pick up test files
  },
  resolve: {
    alias: {
      $lib: path.resolve(__dirname, './src/lib'), // Your project alias
    },
  },
});
