export type ToastKind = 'info' | 'success' | 'error';

export interface Toast {
	id: number;
	kind: ToastKind;
	text: string;
}

class UiState {
	toasts = $state<Toast[]>([]);
	private nextId = 1;

	push(text: string, kind: ToastKind = 'info', timeout = 4000): number {
		const id = this.nextId++;
		this.toasts = [...this.toasts, { id, kind, text }];
		if (timeout > 0) {
			setTimeout(() => this.dismiss(id), timeout);
		}
		return id;
	}

	info(text: string, timeout = 4000): number {
		return this.push(text, 'info', timeout);
	}

	success(text: string, timeout = 4000): number {
		return this.push(text, 'success', timeout);
	}

	error(text: string, timeout = 6000): number {
		return this.push(text, 'error', timeout);
	}

	dismiss(id: number): void {
		this.toasts = this.toasts.filter((toast) => toast.id !== id);
	}
}

export const ui = new UiState();
