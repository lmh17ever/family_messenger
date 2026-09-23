import { request } from './client';
import type { AvatarPresignOut, TokenResponse, User } from './types';

export function getMe(): Promise<User> {
	return request<User>('/users/me');
}

/** GET /users?search=…&offset=&limit= — backend исключает текущего пользователя */
export function searchUsers(search = '', limit = 50, offset = 0): Promise<User[]> {
	const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
	const query = search.trim();
	if (query) params.set('search', query);
	return request<User[]>(`/users?${params.toString()}`);
}

/**
 * PATCH /users/me — смена ника.
 * Backend отдаёт новую пару токенов, потому что username лежит в JWT (sub).
 */
export function updateUsername(username: string): Promise<TokenResponse> {
	return request<TokenResponse>('/users/me', { method: 'PATCH', body: { username } });
}

export function presignAvatar(
	filename: string,
	contentType: string,
	size: number
): Promise<AvatarPresignOut> {
	return request<AvatarPresignOut>('/users/me/avatar/presign', {
		method: 'POST',
		body: { filename, content_type: contentType, size }
	});
}

export function confirmAvatar(avatarKey: string): Promise<User> {
	return request<User>('/users/me/avatar/confirm', {
		method: 'POST',
		body: { avatar_key: avatarKey }
	});
}
