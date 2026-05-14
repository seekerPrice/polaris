// Polaris brand mark — compass-star with gradient fill, matched to the design's
// brand-text "Polaris · AI Agent Firewall · Veea Trust Track".
export function PolarisMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 32 32">
        <defs>
          <linearGradient id="pm-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="oklch(0.92 0.16 200)" />
            <stop offset="100%" stopColor="oklch(0.58 0.13 200)" />
          </linearGradient>
        </defs>
        <g stroke="url(#pm-grad)" strokeWidth="1.3" fill="none" strokeLinejoin="round">
          <path
            d="M16 2 L18.2 13.8 L30 16 L18.2 18.2 L16 30 L13.8 18.2 L2 16 L13.8 13.8 Z"
            fill="url(#pm-grad)"
            fillOpacity="0.18"
          />
          <circle cx="16" cy="16" r="2.4" fill="oklch(0.85 0.14 200)" stroke="none" />
        </g>
      </svg>
    </div>
  );
}
