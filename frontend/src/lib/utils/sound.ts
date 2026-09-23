/**
 * Звук нового сообщения — синтез через WebAudio, без бинарных файлов.
 */

let context: AudioContext | null = null;

type AudioContextConstructor = typeof AudioContext;

/** webkit-префикс нужен для старых Safari */
type WindowWithAudioContext = Window &
	typeof globalThis & {
		webkitAudioContext?: AudioContextConstructor;
	};

function audioContextConstructor(): AudioContextConstructor | null {
	if (typeof window === 'undefined') return null;
	const scoped = window as unknown as WindowWithAudioContext;
	return scoped.AudioContext ?? scoped.webkitAudioContext ?? null;
}

function getContext(): AudioContext | null {
	const Constructor = audioContextConstructor();
	if (!Constructor) return null;
	if (!context) {
		try {
			context = new Constructor();
		} catch {
			return null;
		}
	}
	return context;
}

/**
 * Браузеры разрешают звук только после действия пользователя.
 * Вызывается при первом клике/вводе.
 */
export function unlockAudio(): void {
	const ctx = getContext();
	if (ctx && ctx.state === 'suspended') {
		void ctx.resume();
	}
}

/** Короткий двухтоновый сигнал (используется для новых сообщений) */
export function playNotificationSound(): void {
	const ctx = getContext();
	if (!ctx || ctx.state !== 'running') return;

	const now = ctx.currentTime;
	const master = ctx.createGain();
	master.gain.value = 0.14;
	master.connect(ctx.destination);

	const tones: Array<{ frequency: number; offset: number }> = [
		{ frequency: 880, offset: 0 },
		{ frequency: 1320, offset: 0.11 }
	];

	for (const tone of tones) {
		const oscillator = ctx.createOscillator();
		const gain = ctx.createGain();
		oscillator.type = 'sine';
		oscillator.frequency.value = tone.frequency;
		gain.gain.setValueAtTime(0, now + tone.offset);
		gain.gain.linearRampToValueAtTime(1, now + tone.offset + 0.01);
		gain.gain.exponentialRampToValueAtTime(0.0001, now + tone.offset + 0.18);
		oscillator.connect(gain).connect(master);
		oscillator.start(now + tone.offset);
		oscillator.stop(now + tone.offset + 0.2);
	}
}
