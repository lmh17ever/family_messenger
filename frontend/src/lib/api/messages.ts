import { request } from './client';
import type { Message, MessageCreate } from './types';

/** GET /chats/{chat_id}/messages — backend отдаёт сообщения в порядке «сначала новые» */
export function getMessages(
	chatId: number,
	options: { offset?: number; limit?: number; search?: string } = {}
): Promise<Message[]> {
	const params = new URLSearchParams({
		offset: String(options.offset ?? 0),
		limit: String(options.limit ?? 50)
	});
	const query = options.search?.trim();
	if (query) params.set('search', query);
	return request<Message[]>(`/chats/${chatId}/messages?${params.toString()}`);
}

export function createMessage(chatId: number, payload: MessageCreate): Promise<Message> {
	return request<Message>(`/chats/${chatId}/messages`, { method: 'POST', body: payload });
}

export function updateMessage(chatId: number, messageId: number, text: string): Promise<Message> {
	return request<Message>(`/chats/${chatId}/messages/${messageId}`, {
		method: 'PATCH',
		body: { text }
	});
}

export function deleteMessage(chatId: number, messageId: number): Promise<void> {
	return request<void>(`/chats/${chatId}/messages/${messageId}`, { method: 'DELETE' });
}
