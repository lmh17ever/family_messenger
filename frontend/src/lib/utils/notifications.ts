import { APP_NAME } from '$lib/config';

let unreadTotal = 0;

/** Счётчик непрочитанных в заголовке вкладки: "(3) LNG" */
export function setUnreadBadge(count: number): void {
	unreadTotal = Math.max(0, Math.trunc(count));
	if (typeof document === 'undefined') return;
	document.title = unreadTotal > 0 ? `(${unreadTotal}) ${APP_NAME}` : APP_NAME;
}

export function notificationPermission(): NotificationPermission | 'unsupported' {
	if (typeof window === 'undefined' || !('Notification' in window)) return 'unsupported';
	return Notification.permission;
}

/** Запрашиваем разрешение на системные уведомления (вызывается после входа) */
export async function requestNotificationPermission(): Promise<void> {
	if (notificationPermission() !== 'default') return;
	try {
		await Notification.requestPermission();
	} catch {
		// некоторые браузеры запрещают запрос вне пользовательского жеста
	}
}

/**
 * Системное уведомление показываем только когда вкладка скрыта —
 * иначе достаточно звука и всплывающей плашки внутри приложения.
 */
export function showSystemNotification(title: string, body: string, tag?: string): void {
	if (typeof document === 'undefined' || !document.hidden) return;
	if (notificationPermission() !== 'granted') return;
	try {
		new Notification(title, { body, tag });
	} catch {
		// мобильные браузеры требуют service worker — молча пропускаем
	}
}
