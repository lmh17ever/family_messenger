/**
 * Форматирование дат и времени.
 * Формат даты — строго ДД.ММ.ГГГГ (без «сегодня/вчера»).
 */

const DATE_FORMATTER = new Intl.DateTimeFormat('ru-RU', {
	day: '2-digit',
	month: '2-digit',
	year: 'numeric'
});

const TIME_FORMATTER = new Intl.DateTimeFormat('ru-RU', {
	hour: '2-digit',
	minute: '2-digit'
});

/**
 * Backend хранит время в timestamptz и обычно отдаёт ISO с зоной.
 * Если зона не указана — считаем значение UTC, иначе браузер примет его за локальное.
 */
export function parseDate(value: string): Date {
	const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
	return new Date(hasTimezone ? value : `${value}Z`);
}

export function formatDate(value: string): string {
	return DATE_FORMATTER.format(parseDate(value));
}

export function formatTime(value: string): string {
	return TIME_FORMATTER.format(parseDate(value));
}

/** Ключ дня для разделителей в ленте сообщений (локальная дата) */
export function dayKey(value: string): string {
	const date = parseDate(value);
	const month = String(date.getMonth() + 1).padStart(2, '0');
	const day = String(date.getDate()).padStart(2, '0');
	return `${date.getFullYear()}-${month}-${day}`;
}

export function formatBytes(size: number): string {
	if (!Number.isFinite(size) || size <= 0) return '0 Б';
	const units = ['Б', 'КБ', 'МБ', 'ГБ'];
	const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
	const value = size / 1024 ** index;
	const rounded = index === 0 ? String(size) : value.toFixed(value >= 10 ? 0 : 1);
	return `${rounded.replace('.', ',')} ${units[index]}`;
}

/** ISO-строка для атрибута datetime у <time> */
export function toIso(value: string): string {
	return parseDate(value).toISOString();
}
