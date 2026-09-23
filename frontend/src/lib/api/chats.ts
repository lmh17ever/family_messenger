import { request } from './client';
import type { Chat } from './types';

/** GET /chats/my — отсортировано по последнему сообщению */
export function getMyChats(offset = 0, limit = 100): Promise<Chat[]> {
	const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
	return request<Chat[]>(`/chats/my?${params.toString()}`);
}

export function getChat(chatId: number): Promise<Chat> {
	return request<Chat>(`/chats/${chatId}`);
}

/** POST /chats/{user_id} — открыть или создать личный чат (идемпотентно) */
export function openDirectChat(userId: number): Promise<Chat> {
	return request<Chat>(`/chats/${userId}`, { method: 'POST' });
}

/** POST /chats/{chat_id}/read — отмечает чат прочитанным */
export function markChatRead(chatId: number, messageId: number | null = null): Promise<Chat> {
	return request<Chat>(`/chats/${chatId}/read`, {
		method: 'POST',
		body: { message_id: messageId }
	});
}

/** DELETE /chats/{chat_id} — удаляет чат у всех участников */
export function deleteChat(chatId: number): Promise<void> {
	return request<void>(`/chats/${chatId}`, { method: 'DELETE' });
}
