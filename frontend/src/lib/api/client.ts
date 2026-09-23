import { API_URL } from '$lib/config';
import type { PresignedUpload } from './types';

type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE';

type TokenGetter = () => string | null;
/** Обновляет access-токен. true — токен обновлён, запрос можно повторить. */
type AccessRefresher = () => Promise<boolean>;
/** Вызывается, когда сессию восстановить нельзя (нужен повторный вход). */
type AuthFailureHandler = () => void;

let getAccessToken: TokenGetter = () => null;
let refreshAccessToken: AccessRefresher = async () => false;
let handleAuthFailure: AuthFailureHandler = () => {};

/**
 * Связывает клиент с хранилищем сессии, не создавая циклических импортов.
 * Вызывается один раз из stores/session.svelte.ts.
 */
export function configureAuth(handlers: {
	getAccessToken: TokenGetter;
	refreshAccessToken: AccessRefresher;
	onAuthFailure: AuthFailureHandler;
}): void {
	getAccessToken = handlers.getAccessToken;
	refreshAccessToken = handlers.refreshAccessToken;
	handleAuthFailure = handlers.onAuthFailure;
}

/** Текущий access-токен (нужен WebSocket-клиентам для query-параметра token) */
export function currentAccessToken(): string | null {
	return getAccessToken();
}

export class ApiError extends Error {
	readonly status: number;
	readonly detail: unknown;

	constructor(status: number, message: string, detail?: unknown) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.detail = detail;
	}
}

/** Сообщения backend'а на английском — показываем их по-русски */
const KNOWN_DETAILS: Record<string, string> = {
	'Incorrect username or password': 'Неверное имя пользователя или пароль',
	'Username already registered': 'Такое имя уже занято',
	'Could not validate credentials': 'Сессия истекла, войдите заново',
	'User not found': 'Пользователь не найден',
	'Chat not found': 'Чат не найден',
	'Message not found': 'Сообщение не найдено',
	'Attachment not found': 'Вложение не найдено',
	'Cannot delete another user': 'Нельзя удалить другого пользователя',
	'Only the chat creator can manage members': 'Управлять участниками может только создатель чата',
	'unknown attachment': 'Вложение не найдено',
	'attachment not accessible': 'Нет доступа к вложению',
	'content type not allowed': 'Такой тип файла не поддерживается',
	'size not allowed': 'Файл слишком большой',
	'invalid avatar key': 'Некорректный файл аватара',
	'file not found in storage': 'Файл не найден в хранилище',
	'invalid object size': 'Некорректный размер файла'
};

const STATUS_FALLBACK: Record<number, string> = {
	400: 'Некорректный запрос',
	401: 'Сессия истекла, войдите заново',
	403: 'Недостаточно прав',
	404: 'Не найдено',
	413: 'Файл слишком большой',
	422: 'Некорректные данные',
	500: 'Ошибка сервера',
	502: 'Сервер недоступен',
	503: 'Сервер недоступен'
};

function errorMessage(status: number, detail: unknown): string {
	if (typeof detail === 'string') {
		return KNOWN_DETAILS[detail] ?? detail;
	}
	if (Array.isArray(detail)) {
		const first = detail[0] as { msg?: string; loc?: unknown[] } | undefined;
		if (first?.msg) {
			const field = first.loc?.filter((part) => part !== 'body').join('.');
			return field ? `Поле «${field}»: ${first.msg}` : first.msg;
		}
	}
	return STATUS_FALLBACK[status] ?? `Ошибка запроса (${status})`;
}

function detailOf(data: unknown): unknown {
	if (data && typeof data === 'object' && 'detail' in data) {
		return (data as { detail: unknown }).detail;
	}
	return data;
}

interface RequestOptions {
	method?: HttpMethod;
	/** JSON-тело запроса */
	body?: unknown;
	/** form-urlencoded тело (используется для /auth/token) */
	form?: Record<string, string>;
	/** Отправлять ли Authorization и обновлять ли токен при 401 */
	auth?: boolean;
	/** Разрешить одну повторную попытку после обновления токена */
	retry?: boolean;
	signal?: AbortSignal;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
	const { method = 'GET', body, form, auth = true, retry = true, signal } = options;

	const headers = new Headers();
	if (auth) {
		const token = getAccessToken();
		if (token) headers.set('Authorization', `Bearer ${token}`);
	}

	let payload: BodyInit | undefined;
	if (form) {
		headers.set('Content-Type', 'application/x-www-form-urlencoded');
		payload = new URLSearchParams(form);
	} else if (body !== undefined) {
		headers.set('Content-Type', 'application/json');
		payload = JSON.stringify(body);
	}

	const response = await fetch(`${API_URL}${path}`, { method, headers, body: payload, signal });

	if (response.status === 401 && auth && retry) {
		const refreshed = await refreshAccessToken();
		if (refreshed) {
			return request<T>(path, { ...options, retry: false });
		}
		handleAuthFailure();
	}

	if (response.status === 204) {
		return undefined as T;
	}

	const text = await response.text();
	let data: unknown = null;
	if (text) {
		try {
			data = JSON.parse(text);
		} catch {
			data = text;
		}
	}

	if (!response.ok) {
		const detail = detailOf(data);
		throw new ApiError(response.status, errorMessage(response.status, detail), detail);
	}

	return data as T;
}

/**
 * Загрузка файла напрямую в S3 по presigned POST.
 * Через XHR, потому что нужен прогресс загрузки и возможность отмены.
 * Порядок полей важен: файл отправляется последним.
 */
export function uploadToS3(
	upload: PresignedUpload,
	file: File,
	options: { onProgress?: (ratio: number) => void; signal?: AbortSignal } = {}
): Promise<void> {
	return new Promise<void>((resolve, reject) => {
		const formData = new FormData();
		for (const [key, value] of Object.entries(upload.fields)) {
			formData.append(key, value);
		}
		formData.append('file', file);

		const xhr = new XMLHttpRequest();
		xhr.open('POST', upload.url, true);

		const onAbort = () => xhr.abort();
		options.signal?.addEventListener('abort', onAbort, { once: true });
		const cleanup = () => options.signal?.removeEventListener('abort', onAbort);

		xhr.upload.addEventListener('progress', (event) => {
			if (event.lengthComputable && options.onProgress) {
				options.onProgress(event.loaded / event.total);
			}
		});

		xhr.addEventListener('load', () => {
			cleanup();
			if (xhr.status >= 200 && xhr.status < 300) {
				options.onProgress?.(1);
				resolve();
				return;
			}
			reject(
				new ApiError(
					xhr.status,
					'Не удалось загрузить файл в хранилище. Проверьте CORS-правила бакета.',
					xhr.responseText
				)
			);
		});

		xhr.addEventListener('error', () => {
			cleanup();
			reject(
				new ApiError(
					0,
					'Ошибка сети при загрузке файла. Возможно, у бакета не настроен CORS.',
					null
				)
			);
		});

		xhr.addEventListener('abort', () => {
			cleanup();
			reject(new DOMException('Загрузка отменена', 'AbortError'));
		});

		xhr.send(formData);
	});
}

