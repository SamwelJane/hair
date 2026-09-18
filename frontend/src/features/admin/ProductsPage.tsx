import { useState } from "react";
import { Link } from "react-router";
import { apiClient } from "../../lib/apiClient";
import { useQuery } from "@tanstack/react-query";

function useAdminProducts(q: string, status: string, page: number) {
  return useQuery({
    queryKey: ["admin-products", q, status, page],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/products", {
        params: { query: { q: q || undefined, status: (status || undefined) as never, page } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function AdminProductsPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAdminProducts(q, status, page);

  return (
    <div className="page">
      <div className="link-row" style={{ justifyContent: "space-between" }}>
        <h1>Products</h1>
        <Link to="/admin/products/new" className="button-link">New Product</Link>
      </div>
      <div className="filter-bar">
        <input placeholder="Search by name..." value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
      </div>

      {isLoading ? <p>Loading...</p> : (
        <table className="page-table">
          <thead><tr><th>Name</th><th>Category</th><th>Supplier</th><th>Price</th><th>Variants</th><th>Status</th><th /></tr></thead>
          <tbody>
            {data?.items.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{p.category_name}</td>
                <td>{p.supplier_name}</td>
                <td>${p.base_price_usd}</td>
                <td>{p.variant_count}</td>
                <td>{p.status}</td>
                <td><Link to={`/admin/products/${p.id}`}>Edit</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data?.items.length === 0 && <p>No products match your filters.</p>}

      {data && data.total > data.page_size && (
        <div className="pagination">
          <button type="button" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
          <span>Page {page}</span>
          <button type="button" disabled={page * data.page_size >= data.total} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}
