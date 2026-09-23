/**
 * Отметка «изменено» для сообщений.
 * В API нет поля о правке, поэтому помним изменённые за сессию id:
 * свои правки и события message.updated от других участников.
 */
class EditedMessagesState {
	ids = $state<number[]>([]);

	mark(messageId: number): void {
		if (!this.ids.includes(messageId)) {
			this.ids = [...this.ids, messageId];
		}
	}

	has(messageId: number): boolean {
		return this.ids.includes(messageId);
	}
}

export const editedMessages = new EditedMessagesState();
