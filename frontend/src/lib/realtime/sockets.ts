import type { ChatRealtimeEvent, UserRealtimeEvent } from '$lib/api/types';
import { RealtimeSocket } from './socket';

/** Персональный сокет пользователя: новые сообщения и изменения чатов */
export const userSocket = new RealtimeSocket<UserRealtimeEvent>({
	path: () => '/users/me/ws'
});

let currentChatId: number | null = null;

/** Сокет активного чата: создание/правка/удаление сообщений */
export const chatSocket = new RealtimeSocket<ChatRealtimeEvent>({
	path: () => (currentChatId === null ? null : `/chats/${currentChatId}/ws`)
});

export function openChatSocket(chatId: number): void {
	currentChatId = chatId;
	chatSocket.start();
}

export function closeChatSocket(): void {
	currentChatId = null;
	chatSocket.stop();
}
