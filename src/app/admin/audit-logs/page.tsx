import { db } from "@/lib/db";
import { requireAdminSession } from "@/lib/auth/require-admin";

export default async function AdminAuditLogsPage() {
  await requireAdminSession();
  const logs = await db.auditLog.findMany({
    include: { user: true },
    orderBy: { createdAt: "desc" },
    take: 200,
  });

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="text-2xl font-semibold text-admin-ink">Audit Logs</h1>
      <p className="mt-1 text-sm text-admin-muted">Most recent 200 admin actions.</p>

      <table className="mt-6 w-full text-left text-sm text-admin-ink">
        <thead>
          <tr className="border-b border-admin-border text-admin-muted">
            <th className="py-2">When</th>
            <th>Actor</th>
            <th>Action</th>
            <th>Entity</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr
              key={log.id}
              className={`border-b border-admin-border/60 ${log.action.startsWith("FRAUD_FLAG") ? "bg-admin-critical-soft" : ""}`}
            >
              <td className="py-2 whitespace-nowrap">{log.createdAt.toLocaleString()}</td>
              <td>{log.user?.email ?? "system"}</td>
              <td>{log.action}</td>
              <td>
                {log.entityType}:{log.entityId.slice(0, 8)}
              </td>
              <td className="max-w-xs truncate text-admin-muted">
                {log.metadata ? JSON.stringify(log.metadata) : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {logs.length === 0 && <p className="mt-4 text-sm text-admin-muted">No audit log entries yet.</p>}
    </div>
  );
}
