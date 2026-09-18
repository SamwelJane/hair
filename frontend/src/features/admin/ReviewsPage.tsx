import { useAdminReviews, useModerateReview } from "./hooks";

export function AdminReviewsPage() {
  const { data: reviews, isLoading } = useAdminReviews();
  const moderate = useModerateReview();

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Reviews</h1>
      <div className="address-list">
        {reviews?.map((r) => (
          <div key={r.id} className="address-card">
            <div className="link-row">
              <strong>{r.product_name}</strong>
              <span>{r.user_name}</span>
              <span className="rating">{"★".repeat(r.rating)}</span>
              <span className="badge">{r.status}</span>
            </div>
            <p className="muted">{r.body}</p>
            {r.status === "pending" && (
              <div className="link-row">
                <button type="button" onClick={() => moderate.mutate({ reviewId: r.id, status: "approved" })}>Approve</button>
                <button type="button" className="danger" onClick={() => moderate.mutate({ reviewId: r.id, status: "rejected" })}>Reject</button>
              </div>
            )}
          </div>
        ))}
        {reviews?.length === 0 && <p>No reviews yet.</p>}
      </div>
    </div>
  );
}
