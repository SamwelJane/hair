// Single-measure comparison across categories: one hue throughout (categorical
// slot 1, blue - dark-surface step per the dataviz palette) since color here
// doesn't distinguish identity - a rainbow per bar would be a false categorical cue.
const SERIES_COLOR = "#3987e5";

export interface BarDatum {
  label: string;
  value: number;
}

export function HorizontalBarChart({
  data,
  valueFormatter = (v) => v.toLocaleString(),
  emptyMessage = "No data yet.",
}: {
  data: BarDatum[];
  valueFormatter?: (value: number) => string;
  emptyMessage?: string;
}) {
  if (data.length === 0) {
    return <p className="text-sm text-admin-muted">{emptyMessage}</p>;
  }

  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div role="table" aria-label="Bar chart data" className="flex flex-col gap-2">
      {data.map((d) => (
        <div key={d.label} role="row" className="flex items-center gap-3 text-sm">
          <span role="cell" className="w-32 shrink-0 truncate text-admin-muted" title={d.label}>
            {d.label}
          </span>
          <div className="h-2 flex-1 rounded-full bg-admin-surface-2">
            <div
              className="h-2 rounded-full"
              style={{ width: `${Math.max((d.value / max) * 100, 2)}%`, backgroundColor: SERIES_COLOR }}
            />
          </div>
          <span role="cell" className="w-24 shrink-0 text-right font-medium text-admin-ink">
            {valueFormatter(d.value)}
          </span>
        </div>
      ))}
    </div>
  );
}
