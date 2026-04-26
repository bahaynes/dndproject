import { get } from 'svelte/store';
import { auth } from '$lib/auth';
import { API_BASE_URL } from '$lib/config';

export async function api(method: string, path: string, body?: unknown): Promise<any> {
	const token = get(auth).token;
	const headers: Record<string, string> = {};
	if (token) headers['Authorization'] = `Bearer ${token}`;
	if (body !== undefined) headers['Content-Type'] = 'application/json';

	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

	try {
		const res = await fetch(`${API_BASE_URL}${path}`, {
			method,
			headers,
			signal: controller.signal,
			...(body !== undefined && { body: JSON.stringify(body) })
		});

		clearTimeout(timeoutId);

		if (!res.ok) {
			const err = await res.json().catch(() => ({}));
			throw new Error(err.detail ?? `HTTP ${res.status}`);
		}

		const text = await res.text();
		return text ? JSON.parse(text) : undefined;
	} catch (e) {
		clearTimeout(timeoutId);
		throw e;
	}
}
