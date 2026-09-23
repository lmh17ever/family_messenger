import { request, uploadToS3 } from './client';
import type { Attachment, AttachmentPresignOut } from './types';

export function presignAttachment(chatId: number, file: File): Promise<AttachmentPresignOut> {
	return request<AttachmentPresignOut>(`/chats/${chatId}/attachments/presign`, {
		method: 'POST',
		body: {
			filename: file.name,
			content_type: file.type || 'application/octet-stream',
			size: file.size
		}
	});
}

export function confirmAttachment(attachmentId: number): Promise<Attachment> {
	return request<Attachment>(`/attachments/${attachmentId}/confirm`, { method: 'POST' });
}

/** Свежая presigned-ссылка на скачивание (URL из MessageOut живёт 300 секунд) */
export async function getAttachmentUrl(attachmentId: number): Promise<string> {
	const result = await request<{ url: string }>(`/attachments/${attachmentId}/url`);
	return result.url;
}

/**
 * Полный цикл загрузки: presign → загрузка в S3 → confirm.
 * Возвращает id вложения, который передаётся в MessageCreate.attachment_ids.
 */
export async function uploadAttachment(
	chatId: number,
	file: File,
	options: { onProgress?: (ratio: number) => void; signal?: AbortSignal } = {}
): Promise<number> {
	const created = await presignAttachment(chatId, file);
	await uploadToS3(created.upload, file, options);
	const confirmed = await confirmAttachment(created.attachment_id);
	return confirmed.id;
}
