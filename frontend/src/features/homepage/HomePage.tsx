import { useState } from "react";
import { Link } from "react-router";
import { ProductCard } from "../catalog/ProductCard";
import { useHomepageContent } from "./hooks";

function HeroCarousel({ banners }: { banners: NonNullable<ReturnType<typeof useHomepageContent>["data"]>["banners"] }) {
  const [active, setActive] = useState(0);

  if (banners.length === 0) return null;
  const banner = banners[active];

  return (
    <div className="hero">
      {banners.map((b, i) => (
        <div
          key={b.id}
          className={`hero-slide${i === active ? " active" : ""}`}
          style={{ backgroundImage: `url(${b.image_url})` }}
        />
      ))}
      <div className="hero-content">
        <h1>{banner.headline}</h1>
        {banner.subheadline && <p>{banner.subheadline}</p>}
        {banner.cta_label && banner.cta_url && (
          <Link className="button-link" to={banner.cta_url}>{banner.cta_label}</Link>
        )}
      </div>
      {banners.length > 1 && (
        <div className="hero-dots">
          {banners.map((b, i) => (
            <button
              key={b.id}
              type="button"
              className={i === active ? "active" : ""}
              aria-label={`Show slide ${i + 1}`}
              onClick={() => setActive(i)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function HomePage() {
  const { data, isLoading } = useHomepageContent();

  if (isLoading) return <div className="page">Loading...</div>;
  if (!data) return null;

  return (
    <div>
      <HeroCarousel banners={data.banners} />

      <div className="trust-strip">
        <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
          Sourced direct from Vietnam
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
          Secure M-Pesa &amp; bank payments
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
          Tracked door-to-door to Kenya
        </span>
      </div>

      <div className="page">
        {data.featured_categories.length > 0 && (
          <section>
            <div className="rail-header">
              <h2>Shop by Category</h2>
            </div>
            <div className="category-tile-grid">
              {data.featured_categories.map((category) => (
                <Link key={category.id} className="category-tile" to={`/products?category=${category.slug}`}>
                  <div className="category-tile-image">
                    {category.image_url && <img src={category.image_url} alt={category.name} />}
                  </div>
                  <span>{category.name}</span>
                </Link>
              ))}
            </div>
          </section>
        )}

        {data.featured_products.length > 0 && (
          <section className="callout">
            <div className="rail-header">
              <h2>Featured Products</h2>
              <Link to="/products">View all</Link>
            </div>
            <div className="product-grid">
              {data.featured_products.map((product) => <ProductCard key={product.id} product={product} />)}
            </div>
          </section>
        )}

        {data.deals.length > 0 && (
          <section className="callout">
            <div className="rail-header">
              <h2>Deals</h2>
              <Link to="/products">View all</Link>
            </div>
            <div className="product-grid">
              {data.deals.map((product) => <ProductCard key={product.id} product={product} />)}
            </div>
          </section>
        )}

        {data.featured_categories.length === 0 && data.featured_products.length === 0 && data.deals.length === 0 && (
          <section className="callout" style={{ textAlign: "center" }}>
            <h2>Welcome to Hiar Business</h2>
            <p className="muted">Discover our full range of Vietnam-sourced hair products.</p>
            <Link className="button-link" to="/products">Shop Now</Link>
          </section>
        )}
      </div>
    </div>
  );
}
