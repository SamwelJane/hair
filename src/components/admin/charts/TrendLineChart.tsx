const SERIES_COLOR = "#3987e5";
const GRIDLINE = "#2e3238";
const AXIS = "#454a52";

export interface TrendPoint {
  label: string;
  value: number;
}

export function TrendLineChart({ data, height = 160 }: { data: TrendPoint[]; height?: number }) {
  if (data.length === 0) {
    return <p className="text-sm text-admin-muted">No data yet.</p>;
  }

  const width = 600;
  const padding = 24;
  const max = Math.max(...data.map((d) => d.value), 1);
  const stepX = data.length > 1 ? (width - padding * 2) / (data.length - 1) : 0;

  const points = data.map((d, i) => {
    const x = padding + i * stepX;
    const y = height - padding - (d.value / max) * (height - padding * 2);
    return { x, y, ...d };
  });

  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label="Trend over time">
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke={AXIS} strokeWidth={1} />
        <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke={GRIDLINE} strokeWidth={1} strokeDasharray="4 4" />
        <path d={path} fill="none" stroke={SERIES_COLOR} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        {points.map((p) => (
          <circle key={p.label} cx={p.x} cy={p.y} r={3.5} fill={SERIES_COLOR}>
            <title>{`${p.label}: ${p.value}`}</title>
          </circle>
        ))}
      </svg>

      <details className="mt-2 text-xs text-admin-muted">
        <summary className="cursor-pointer">View as table</summary>
        <table className="mt-2 w-full text-left text-admin-ink">
          <thead>
            <tr>
              <th className="pr-4">Date</th>
              <th>Orders</th>
            </tr>
          </thead>
          <tbody>
            {data.map((d) => (
              <tr key={d.label}>
                <td className="pr-4">{d.label}</td>
                <td>{d.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
