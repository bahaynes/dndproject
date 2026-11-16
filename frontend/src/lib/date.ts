/**
 * Parse a backend ISO datetime string as UTC when it lacks an explicit timezone offset.
 * FastAPI/SQLAlchemy often serialize naive UTC datetimes without a trailing 'Z',
 * which JS `new Date(...)` would otherwise interpret as local time.
 */
export function parseUtcDate(iso: string): Date {
	if (!iso) return new Date(NaN);
	const hasTz = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(iso);
	return new Date(hasTz ? iso : `${iso}Z`);
}

export function formatSessionDateTime(iso: string): string {
	const d = parseUtcDate(iso);
	if (Number.isNaN(d.getTime())) return iso;
	return d.toLocaleString(undefined, {
		weekday: 'short',
		month: 'short',
		day: 'numeric',
		hour: 'numeric',
		minute: '2-digit'
	});
}

/**
 * Convert a backend UTC ISO string into a `YYYY-MM-DDTHH:mm` string in the
 * browser's local timezone for `<input type="datetime-local">`.
 */
export function toLocalDateTimeInput(iso: string): string {
	const d = parseUtcDate(iso);
	if (Number.isNaN(d.getTime())) return '';
	const pad = (n: number) => String(n).padStart(2, '0');
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
