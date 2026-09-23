import { ApiError } from '$lib/api/client';
import * as chatsApi from '$lib/api/chats';
import type { Chat, NewMessageNotification, User } from '$lib/api/types';

function lastActivity(chat: Chat): number {
	if (!chat.last_message_at) return 0;
	const timestamp = Date.parse(chat.last_message_at);
	return Number.isNaN(timestamp) ? 0 : timestamp;
}

/** Список чатов: сортировка как в backend (по последнему сообщению, затем по id) */
class ChatsState {
	items = $state<Chat[]>([]);
	loading = $state(false);
	loaded = $state(false);
	activeChatId = $state<number | null>(null);

	get totalUnread(): number {
		return this.items.reduce((sum, chat) => sum + chat.unread_count, 0);
	}

	get activeChat(): Chat | null {
		return this.items.find((chat) => chat.id === this.activeChatId) ?? null;
	}

	async load(): Promise<void> {
		this.loading = true;
		try {
			this.items = await chatsApi.getMyChats();
			this.loaded = true;
		} finally {
			this.loading = false;
		}
	}

	async refreshChat(chatId: number): Promise<void> {
		try {
			this.upsert(await chatsApi.getChat(chatId));
		} catch (error) {
			if (error instanceof ApiError && error.status === 404) {
				this.remove(chatId);
			}
		}
	}

	upsert(chat: Chat): void {
		const index = this.items.findIndex((item) => item.id === chat.id);
		if (index === -1) {
			this.items = [chat, ...this.items];
		} else {
			this.items[index] = chat;
		}
		this.sortByActivity();
	}

	remove(chatId: number): void {
		this.items = this.items.filter((chat) => chat.id !== chatId);
		if (this.activeChatId === chatId) {
			this.activeChatId = null;
		}
	}

	async openDirect(userId: number): Promise<Chat> {
		const chat = await chatsApi.openDirectChat(userId);
		this.upsert(chat);
		return chat;
	}

	async markRead(chatId: number): Promise<void> {
		const chat = this.items.find((item) => item.id === chatId);
		if (!chat || chat.unread_count === 0) return;
		try {
			this.upsert(await chatsApi.markChatRead(chatId, chat.last_message?.id ?? null));
		} catch {
			// отметка прочтения не критична
		}
	}

	async removeChat(chatId: number): Promise<void> {
		await chatsApi.deleteChat(chatId);
		this.remove(chatId);
	}

	/** Участники чата для отображения имени/аватара */
	participantsOf(chatId: number): User[] {
		return this.items.find((chat) => chat.id === chatId)?.participants ?? [];
	}

	/**
	 * Событие персонального сокета: обновляем бейдж и позицию чата сразу,
	 * точные данные подтянет событие chat.updated.
	 * Возвращает true, если пользователя стоит уведомить (чат не открыт или вкладка скрыта).
	 */
	applyNotification(event: NewMessageNotification): boolean {
		const chat = this.items.find((item) => item.id === event.chat_id);
		if (!chat) {
			void this.refreshChat(event.chat_id);
			return !document.hidden;
		}
		chat.unread_count = event.unread_count;
		chat.last_message_at = event.created_at;
		this.sortByActivity();
		return this.activeChatId !== event.chat_id || document.hidden;
	}

	private sortByActivity(): void {
		this.items.sort((a, b) => {
			const diff = lastActivity(b) - lastActivity(a);
			return diff !== 0 ? diff : b.id - a.id;
		});
	}
}

export const chats = new ChatsState();
