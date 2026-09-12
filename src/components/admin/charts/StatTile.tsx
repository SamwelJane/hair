export function StatTile({
  label,
  value,
  sublabel,
}: {
  label: string;
  value: string;
  sublabel?: string;
}) {
  return (
    <div className="rounded border border-admin-border bg-admin-surface p-4">
      <p className="text-xs text-admin-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-admin-ink" style={{ fontVariantNumeric: "proportional-nums" }}>
        {value}
      </p>
      {sublabel && <p className="mt-1 text-xs text-admin-muted">{sublabel}</p>}
    </div>
  );
}
