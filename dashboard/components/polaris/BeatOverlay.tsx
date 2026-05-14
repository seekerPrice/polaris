// BeatOverlay — small floating pill at the top of the screen showing which
// of the 12 demo beats is currently active. Driven by the replay engine.
import { BEAT_LABELS } from "@/lib/replay";

export function BeatOverlay({ beat }: { beat: number }) {
  if (beat === 0 || !BEAT_LABELS[beat]) return null;
  return (
    <div key={beat} className="beat-overlay">
      <span className="beat-overlay__num">{beat}</span>
      <span>{BEAT_LABELS[beat]}</span>
    </div>
  );
}
