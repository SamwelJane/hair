import { Link } from "react-router";
import { useSupplierProducts } from "./hooks";

export function SupplierProductsPage() {
  const { data: products, isLoading } = useSupplierProducts();

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <div className="link-row" style={{ justifyContent: "space-between" }}>
        <h1>My Products</h1>
        <Link to="/supplier/products/new" className="button-link">Add Product</Link>
      </div>
      <table className="page-table">
        <thead>
          <tr><th>Name</th><th>Category</th><th>Variants</th><th>Price (USD)</th><th>Status</th><th /></tr>
        </thead>
        <tbody>
          {products?.map((p) => (
            <tr key={p.id}>
              <td>{p.name}</td>
              <td>{p.hair_category.replaceAll("_", " ")}</td>
              <td>{p.variants?.length ?? 0}</td>
              <td>${p.base_price_usd}</td>
              <td>{p.status}</td>
              <td><Link to={`/supplier/products/${p.id}`}>Edit</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
      {products?.length === 0 && <p>No products yet.</p>}
    </div>
  );
}
