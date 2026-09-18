import { createBrowserRouter, Navigate } from "react-router";
import { StorefrontLayout } from "./StorefrontLayout";
import { SupplierLayout } from "./SupplierLayout";
import { AdminLayout } from "./AdminLayout";
import { WarehouseLayout } from "./WarehouseLayout";
import { RequireAuth } from "./RequireAuth";
import { HomePage } from "../features/homepage/HomePage";
import { ProductsPage } from "../features/catalog/ProductsPage";
import { ProductDetailPage } from "../features/catalog/ProductDetailPage";
import { CartPage } from "../features/cart/CartPage";
import { CheckoutPage } from "../features/checkout/CheckoutPage";
import { ConfirmationPage } from "../features/checkout/ConfirmationPage";
import { TrackingPage } from "../features/tracking/TrackingPage";
import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";
import { AccountPage } from "../features/account/AccountPage";
import { OrdersPage } from "../features/account/OrdersPage";
import { OrderDetailPage } from "../features/account/OrderDetailPage";
import { AddressesPage } from "../features/account/AddressesPage";
import { SupplierOrdersPage } from "../features/supplier/OrdersPage";
import { SupplierProductsPage } from "../features/supplier/ProductsPage";
import { SupplierProductFormPage } from "../features/supplier/ProductFormPage";
import { AdminDashboardPage } from "../features/admin/DashboardPage";
import { AdminOrdersPage } from "../features/admin/OrdersPage";
import { AdminOrderDetailPage } from "../features/admin/OrderDetailPage";
import { AdminProductsPage } from "../features/admin/ProductsPage";
import { AdminProductFormPage } from "../features/admin/ProductFormPage";
import { AdminCategoriesPage } from "../features/admin/CategoriesPage";
import { AdminHomepageBannersPage } from "../features/admin/HomepageBannersPage";
import { AdminHomepageProductPlacementsPage } from "../features/admin/HomepageProductPlacementsPage";
import { AdminSuppliersPage } from "../features/admin/SuppliersPage";
import { AdminSupplierDetailPage } from "../features/admin/SupplierDetailPage";
import { AdminReturnsPage } from "../features/admin/ReturnsPage";
import { AdminReviewsPage } from "../features/admin/ReviewsPage";
import { AdminPaymentsPage } from "../features/admin/PaymentsPage";
import { AdminUsersPage } from "../features/admin/UsersPage";
import { AdminAnalyticsPage } from "../features/admin/AnalyticsPage";
import { AdminAuditLogsPage } from "../features/admin/AuditLogsPage";
import { AdminExchangeRatePage } from "../features/admin/settings/ExchangeRatePage";
import { AdminPricingSettingsPage } from "../features/admin/settings/PricingSettingsPage";
import { AdminShippingRulesPage } from "../features/admin/settings/ShippingRulesPage";
import { AdminDiscountCodesPage } from "../features/admin/settings/DiscountCodesPage";
import { WarehouseDashboardPage } from "../features/warehouse/DashboardPage";
import { ReceivePackagePage } from "../features/warehouse/ReceivePackagePage";
import { ExternalShipmentFormPage } from "../features/warehouse/ExternalShipmentFormPage";
import { ExternalShipmentsListPage } from "../features/warehouse/ExternalShipmentsListPage";
import { ExternalShipmentDetailPage } from "../features/warehouse/ExternalShipmentDetailPage";
import { PackageRegistryPage } from "../features/warehouse/PackageRegistryPage";
import { PackageDetailPage } from "../features/warehouse/PackageDetailPage";
import { ConsolidationQueuePage } from "../features/warehouse/ConsolidationQueuePage";
import { ConsolidationsListPage } from "../features/warehouse/ConsolidationsListPage";
import { ConsolidationDetailPage } from "../features/warehouse/ConsolidationDetailPage";
import { CustomsQueuePage } from "../features/warehouse/CustomsQueuePage";
import { CustomsDeclarationDetailPage } from "../features/warehouse/CustomsDeclarationDetailPage";

const SUPPLIER_ROLES = ["SUPPLIER"] as const;
const ADMIN_ROLES = ["ADMIN", "STAFF"] as const;
const WAREHOUSE_PORTAL_ROLES = ["WAREHOUSE", "KENYA_OPS"] as const;

export const router = createBrowserRouter([
  {
    element: <StorefrontLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "products", element: <ProductsPage /> },
      { path: "products/:slug", element: <ProductDetailPage /> },
      { path: "cart", element: <CartPage /> },
      { path: "checkout", element: <CheckoutPage /> },
      { path: "checkout/confirmation/:orderNumber", element: <ConfirmationPage /> },
      { path: "track/:trackingNumber", element: <TrackingPage /> },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      { path: "account", element: <RequireAuth><AccountPage /></RequireAuth> },
      { path: "account/orders", element: <RequireAuth><OrdersPage /></RequireAuth> },
      { path: "account/orders/:orderNumber", element: <RequireAuth><OrderDetailPage /></RequireAuth> },
      { path: "account/addresses", element: <RequireAuth><AddressesPage /></RequireAuth> },
      { path: "*", element: <NotFound /> },
    ],
  },
  {
    path: "supplier",
    element: <RequireAuth roles={SUPPLIER_ROLES}><SupplierLayout /></RequireAuth>,
    children: [
      { index: true, element: <Navigate to="orders" replace /> },
      { path: "orders", element: <SupplierOrdersPage /> },
      { path: "products", element: <SupplierProductsPage /> },
      { path: "products/new", element: <SupplierProductFormPage /> },
      { path: "products/:productId", element: <SupplierProductFormPage /> },
    ],
  },
  {
    path: "admin",
    element: <RequireAuth roles={ADMIN_ROLES}><AdminLayout /></RequireAuth>,
    children: [
      { index: true, element: <AdminDashboardPage /> },
      { path: "orders", element: <AdminOrdersPage /> },
      { path: "orders/:orderId", element: <AdminOrderDetailPage /> },
      { path: "products", element: <AdminProductsPage /> },
      { path: "products/new", element: <AdminProductFormPage /> },
      { path: "products/:productId", element: <AdminProductFormPage /> },
      { path: "categories", element: <AdminCategoriesPage /> },
      { path: "homepage/banners", element: <AdminHomepageBannersPage /> },
      { path: "homepage/products", element: <AdminHomepageProductPlacementsPage /> },
      { path: "suppliers", element: <AdminSuppliersPage /> },
      { path: "suppliers/:supplierId", element: <AdminSupplierDetailPage /> },
      { path: "returns", element: <AdminReturnsPage /> },
      { path: "reviews", element: <AdminReviewsPage /> },
      { path: "payments", element: <AdminPaymentsPage /> },
      { path: "users", element: <AdminUsersPage /> },
      { path: "analytics", element: <AdminAnalyticsPage /> },
      { path: "audit-logs", element: <AdminAuditLogsPage /> },
      { path: "settings/exchange-rate", element: <AdminExchangeRatePage /> },
      { path: "settings/pricing", element: <AdminPricingSettingsPage /> },
      { path: "settings/shipping-rules", element: <AdminShippingRulesPage /> },
      { path: "settings/discount-codes", element: <AdminDiscountCodesPage /> },
    ],
  },
  {
    path: "warehouse",
    element: <RequireAuth roles={WAREHOUSE_PORTAL_ROLES}><WarehouseLayout /></RequireAuth>,
    children: [
      { index: true, element: <WarehouseDashboardPage /> },
      { path: "receive", element: <ReceivePackagePage /> },
      { path: "external-shipments/new", element: <ExternalShipmentFormPage /> },
      { path: "external-shipments", element: <ExternalShipmentsListPage /> },
      { path: "external-shipments/:shipmentId", element: <ExternalShipmentDetailPage /> },
      { path: "packages", element: <PackageRegistryPage /> },
      { path: "packages/:packageId", element: <PackageDetailPage /> },
      { path: "consolidation-queue", element: <ConsolidationQueuePage /> },
      { path: "consolidations", element: <ConsolidationsListPage /> },
      { path: "consolidations/:consolidationId", element: <ConsolidationDetailPage /> },
      { path: "customs", element: <CustomsQueuePage /> },
      { path: "customs/:declarationId", element: <CustomsDeclarationDetailPage /> },
    ],
  },
]);

function NotFound() {
  return <div className="page">Page not found.</div>;
}
