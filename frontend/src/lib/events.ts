import { browser } from '$app/environment';
import { writable } from 'svelte/store';

function createEventStore() {
	const { subscribe, set } = writable<{ type: string; data: unknown } | null>(null);

	let eventSource: EventSource | null = null;

	function init() {
		if (!browser) return;
		if (eventSource) return;

		eventSource = new EventSource('/api/events/');

		eventSource.addEventListener('mission_update', (event) => {
			set({ type: 'mission_update', data: event.data ? JSON.parse(event.data) : {} });
		});

		eventSource.addEventListener('session_update', (event) => {
			set({ type: 'session_update', data: event.data ? JSON.parse(event.data) : {} });
		});

		eventSource.onerror = () => {
			// EventSource automatically attempts to reconnect
			console.log('EventSource connection lost/error.');
		};
	}

	function close() {
		if (eventSource) {
			eventSource.close();
			eventSource = null;
		}
	}

	return {
		subscribe,
		init,
		close
	};
}

export const serverEvents = createEventStore();
