import { AdminNav } from "@/components/admin/AdminNav";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-admin-bg text-admin-ink">
      <AdminNav />
      {children}
    </div>
  );
}
