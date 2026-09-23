/**
 * Единая точка конфигурации фронтенда.
 *
 * Значения берутся из frontend/.env (префикс PUBLIC_ обязателен для Vite).
 * Если переменная не задана, используется адрес локального backend'а.
 */

const FALLBACK_API_BASE_URL = 'http://localhost:8000';

function trimTrailingSlash(value: string): string {
	return value.replace(/\/+$/, '');
}

export const APP_NAME = 'LNG';

/** Базовый адрес backend'а, без суффикса /api/v1 */
export const API_BASE_URL = trimTrailingSlash(
	import.meta.env?.VITE_API_BASE_URL || FALLBACK_API_BASE_URL
);

export const API_PREFIX = '/api/v1';

/** REST-база: http://localhost:8000/api/v1 */
export const API_URL = `${API_BASE_URL}${API_PREFIX}`;

/** WebSocket-база: ws://localhost:8000/api/v1 */
export const WS_URL = `${API_BASE_URL.replace(/^http/, 'ws')}${API_PREFIX}`;

const S3_BASE_URL = trimTrailingSlash(import.meta.env?.PUBLIC_S3_BASE_URL ?? '');
const S3_PUBLIC_BUCKET = import.meta.env?.PUBLIC_S3_PUBLIC_BUCKET ?? '';

/** Сколько сообщений подгружаем за раз (при входе в чат и при подгрузке истории) */
export const MESSAGE_PAGE_SIZE = 50;

/** Максимальная длина сообщения из бэкенда (MessageCreate.text) */
export const MESSAGE_MAX_LENGTH = 10_000;

/** Интервал ping для WebSocket-соединений, мс */
export const WS_PING_INTERVAL = 25_000;

/**
 * Публичный URL файла из публичного бакета (аватарки групп).
 * Для аватарок пользователей backend уже отдаёт готовый avatar_url.
 */
export function publicFileUrl(key: string | null | undefined): string | null {
	if (!key || !S3_BASE_URL || !S3_PUBLIC_BUCKET) return null;
	return `${S3_BASE_URL}/${S3_PUBLIC_BUCKET}/${key}`;
}
