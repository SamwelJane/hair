import { Link } from "react-router";
import { useCart, useRemoveCartItem, useUpdateCartItem } from "./hooks";

export function CartPage() {
  const { data: cart, isLoading } = useCart();
  const updateItem = useUpdateCartItem();
  const removeItem = useRemoveCartItem();

  if (isLoading) return <div className="page">Loading cart...</div>;
  if (!cart || cart.items.length === 0) {
    return (
      <div className="page">
        <h1>Your Cart</h1>
        <p>Your cart is empty. <Link to="/products">Continue shopping</Link></p>
      </div>
    );
  }

  const total = cart.items.reduce((sum, item) => sum + Number(item.unit_price_usd) * item.quantity, 0);

  return (
    <div className="page">
      <h1>Your Cart</h1>
      <ul className="cart-list">
        {cart.items.map((item) => (
          <li key={item.id} className="cart-item">
            {item.image_url && <img src={item.image_url} alt={item.name} />}
            <div className="cart-item-info">
              <Link to={`/products/${item.slug}`}>{item.name}</Link>
              {item.variant_label && <p className="muted">{item.variant_label}</p>}
              <p>${item.unit_price_usd} each</p>
            </div>
            <input
              type="number"
              min={1}
              max={50}
              value={item.quantity}
              onChange={(e) => updateItem.mutate({ itemId: item.id, quantity: Number(e.target.value) || 1 })}
            />
            <button type="button" onClick={() => removeItem.mutate(item.id)}>Remove</button>
          </li>
        ))}
      </ul>
      <p className="cart-total">Total: ${total.toFixed(2)}</p>
      <Link to="/checkout" className="button-link">Proceed to Checkout</Link>
    </div>
  );
}
