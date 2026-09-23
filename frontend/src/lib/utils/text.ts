import type { Attachment, Chat, Message, User } from '$lib/api/types';

/** Отображаемое имя чата: для личного — собеседник, для группы — название или участники */
export function chatTitle(chat: Chat, currentUserId: number | null): string {
	if (chat.type === 'group') {
		if (chat.title?.trim()) return chat.title;
		const names = chat.participants
			.filter((user) => user.id !== currentUserId)
			.map((user) => user.username);
		return names.length ? names.join(', ') : 'Групповой чат';
	}
	return chatPartner(chat, currentUserId)?.username ?? 'Чат';
}

/** Собеседник в личном чате (для аватара) */
export function chatPartner(chat: Chat, currentUserId: number | null): User | null {
	if (chat.type === 'group') return null;
	return chat.participants.find((user) => user.id !== currentUserId) ?? null;
}

/** Пользователь для аватара и подписи сообщения */
export function userById(chat: Chat | null, userId: number | null | undefined): User | null {
	if (!chat || userId == null) return null;
	return chat.participants.find((user) => user.id === userId) ?? null;
}

export function initials(name: string): string {
	const parts = name.trim().split(/\s+/).filter(Boolean);
	if (!parts.length) return '?';
	if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
	return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

export function isImage(contentType: string | null | undefined): boolean {
	return Boolean(contentType && contentType.startsWith('image/'));
}

export function isPreviewableImage(attachment: Attachment): boolean {
	return isImage(attachment.content_type) && Boolean(attachment.url);
}

/** Короткое описание последнего сообщения для списка чатов */
export function describeMessage(message: Message | null, currentUserId: number | null): string {
	if (!message) return 'Нет сообщений';
	const prefix = message.sender_id === currentUserId ? 'Вы: ' : '';
	const attachments = message.attachments ?? [];
	const text = message.text?.trim() ?? '';

	if (text) return `${prefix}${text}`;
	if (!attachments.length) return `${prefix}сообщение`;

	const [first] = attachments;
	const label = isImage(first.content_type)
		? 'фото'
		: `файл: ${first.filename}`;
	const rest = attachments.length > 1 ? ` (+${attachments.length - 1})` : '';
	return `${prefix}${label}${rest}`;
}

/** Текст сообщения без учёта вложений */
export function messageText(message: Message): string {
	return message.text?.trim() ?? '';
}
