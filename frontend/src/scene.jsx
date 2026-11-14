import { Link } from "react-router-dom";

export function Brand({ light = false }) {
  return (
    <Link to="/" className={light ? "brand light" : "brand"}>
      <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">
        <path className="br" d="M3 8V3h5M16 3h5v5M21 16v5h-5M8 21H3v-5" fill="none" strokeWidth="2.4" strokeLinecap="square" />
        <circle cx="12" cy="12" r="3.6" fill="currentColor" />
      </svg>
      FaceFind
    </Link>
  );
}

// x, y = head centre, r = head radius, s = similarity score shown on the box
const PEOPLE = [
  { x: 60, y: 118, r: 15, s: "0.09" },
  { x: 140, y: 108, r: 16, s: "0.17" },
  { x: 330, y: 112, r: 15, s: "0.12" },
  { x: 420, y: 120, r: 16, s: "0.21" },
  { x: 95, y: 188, r: 23, s: "0.14" },
  { x: 205, y: 178, r: 24, s: "0.08" },
  { x: 385, y: 190, r: 23, s: "0.19" },
  { x: 150, y: 275, r: 34, s: "0.11" },
  { x: 300, y: 262, r: 38, s: "0.86", you: true },
  { x: 430, y: 285, r: 32, s: "0.13" },
];

function corners(x, y, w, h, c) {
  return `M${x} ${y + c}V${y}H${x + c}M${x + w - c} ${y}H${x + w}V${y + c}M${x + w} ${y + h - c}V${y + h}H${x + w - c}M${x + c} ${y + h}H${x}V${y + h - c}`;
}

export function Scene() {
  return (
    <svg className="scene" viewBox="0 0 480 360" aria-hidden="true">
      <defs>
        <linearGradient id="trail" x1="0" x2="1">
          <stop offset="0" stopColor="#FFD93D" stopOpacity="0" />
          <stop offset="1" stopColor="#FFD93D" stopOpacity="0.3" />
        </linearGradient>
      </defs>

      {PEOPLE.map((p, i) => (
        <g key={`p${i}`}>
          <ellipse className="torso" cx={p.x} cy={p.y + p.r * 2.2} rx={p.r * 1.7} ry={p.r * 1.5} />
          <circle className="face" cx={p.x} cy={p.y} r={p.r} />
        </g>
      ))}

      {PEOPLE.map((p, i) => {
        const w = p.r * 2.5;
        const h = p.r * 2.9;
        const x0 = p.x - w / 2;
        const y0 = p.y - h / 2;
        const d = 0.25 + (p.x / 480) * 1.5; // box appears when the scan line reaches it
        return (
          <g key={`b${i}`} className={p.you ? "box you" : "box"} style={{ "--d": `${d.toFixed(2)}s` }}>
            {p.you && <rect className="lock lockfill" x={x0} y={y0} width={w} height={h} />}
            <path className="corners" d={corners(x0, y0, w, h, Math.max(5, p.r * 0.55))} />
            {p.you ? (
              <g className="lock tag">
                <rect x={x0} y={y0 - 24} width="78" height="19" rx="4" />
                <text x={x0 + 8} y={y0 - 10}>you  {p.s}</text>
              </g>
            ) : (
              <text className="sc" x={x0} y={y0 + h + 13}>{p.s}</text>
            )}
          </g>
        );
      })}

      <g className="scan">
        <rect x="-90" y="0" width="90" height="360" fill="url(#trail)" />
        <rect x="0" y="0" width="2.5" height="360" fill="#FFD93D" />
      </g>
    </svg>
  );
}