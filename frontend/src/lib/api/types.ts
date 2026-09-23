/** Типы данных backend'а (/api/v1). Соответствуют app/schemas в backend. */

export type ChatType = 'direct' | 'group';

export interface User {
	id: number;
	username: string;
	avatar_url: string | null;
}

export interface Attachment {
	id: number;
	filename: string;
	content_type: string;
	size: number;
	/** presigned GET-ссылка (живёт 300 секунд) */
	url: string | null;
}

export interface Message {
	id: number;
	chat_id: number;
	sender_id: number | null;
	text: string | null;
	created_at: string;
	sender: User | null;
	attachments: Attachment[];
}

export interface Chat {
	id: number;
	type: ChatType;
	creator_id: number | null;
	title: string | null;
	avatar_key: string | null;
	created_at: string;
	last_message_at: string | null;
	participants: User[];
	last_message: Message | null;
	unread_count: number;
}

export interface TokenResponse {
	access_token: string;
	refresh_token: string;
	token_type: string;
}

export interface MessageCreate {
	text?: string | null;
	attachment_ids?: number[];
}

export interface PresignRequest {
	filename: string;
	content_type: string;
	size: number;
}

/** Ответ presign: url + поля, которые нужно приложить к multipart-форме */
export interface PresignedUpload {
	url: string;
	fields: Record<string, string>;
}

export interface AttachmentPresignOut {
	attachment_id: number;
	upload: PresignedUpload;
}

export interface AvatarPresignOut {
	upload: PresignedUpload;
	avatar_key: string;
}

/** События персонального сокета /users/me/ws */
export interface ConnectedEvent {
	type: 'connected';
	chat_id?: number;
}

export interface PongEvent {
	type: 'pong';
}

export interface ErrorEvent {
	type: 'error';
	detail: unknown;
}

export interface ChatUpdatedEvent {
	type: 'chat.updated';
	chat_id: number;
}

export interface NewMessageNotification {
	type: 'notification.new_message';
	chat_id: number;
	message_id: number;
	sender_id: number;
	sender: User | null;
	text: string | null;
	created_at: string;
	unread_count: number;
}

/** События сокета чата /chats/{id}/ws */
export interface MessageCreatedEvent {
	type: 'message.created';
	message: Message;
}

export interface MessageUpdatedEvent {
	type: 'message.updated';
	message: Message;
}

export interface MessageDeletedEvent {
	type: 'message.deleted';
	message_id: number;
	chat_id: number;
}

export type UserRealtimeEvent =
	| ConnectedEvent
	| PongEvent
	| ChatUpdatedEvent
	| NewMessageNotification
	| ErrorEvent;

export type ChatRealtimeEvent =
	| ConnectedEvent
	| PongEvent
	| MessageCreatedEvent
	| MessageUpdatedEvent
	| MessageDeletedEvent
	| ErrorEvent;
