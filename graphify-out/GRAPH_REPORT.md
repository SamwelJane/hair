# Graph Report - hair  (2026-09-16)

## Corpus Check
- 399 files · ~147,103 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2307 nodes · 6194 edges · 130 communities (93 shown, 26 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 645 edges (avg confidence: 0.94)
- Token cost: 506,548 input · 0 output

## Community Hubs (Navigation)
- Admin Product Schemas
- Admin Settings & Users Schemas
- Authentication Schemas
- Backend Integration Tests
- Returns & Reviews Domain
- Legacy Admin Pages (Next.js)
- Pricing & Cart Breakdown Engine
- Backend Config & Migrations
- SQLAlchemy Catalog Models
- Account Export & Addresses
- Notifications & Order UI (Legacy)
- Web Admin Hooks & Pages
- Legacy Account Pages (Next.js)
- Cart API (FastAPI)
- Analytics & Audit Schemas
- Public Product Catalog API
- apps/web Package Config
- Legacy Cart Context (Next.js)
- Legacy Admin Analytics (Next.js)
- Web Auth & Cart Pages
- Web Admin Dashboard Pages
- Orders & Checkout API
- Order State Machine & Notifications
- Legacy Supplier Product Pages (Next.js)
- Admin Order Schemas
- Legacy Storefront Pages (Next.js)
- Admin Payments API
- M-Pesa & Legacy Payments Admin
- Payments API (Bank & M-Pesa)
- apps/mobile Package Config
- Mobile Orders & Checkout Screens
- Web Auth Context & Token Store
- Legacy Order/Checkout Routes (Next.js)
- Data Privacy & Compliance Doc
- Mobile Cart & Checkout Screens
- Generated API Client Package
- Legacy Next.js Package Config
- Legacy Pricing API (Next.js)
- Expo App Config
- Web Admin Product Form
- apps/web TS Config
- UI Mockup: Order Dashboard
- Admin Suppliers API
- Web Supplier Portal Pages
- Legacy Next.js Dependencies
- Legacy Next.js TS Config
- Reviews & Public Catalog Tests
- Auth Integration Tests
- FastAPI Auth Dependencies
- Admin Analytics Service
- Supplier Order Service Logic
- Mobile Auth Token Store
- apps/web Node TS Config
- Supplier Orders API
- apps/mobile Dependencies
- Web Account Order Detail Page
- Legacy Supplier Portal (Next.js)
- Legacy Payment Provider Adapters
- Mobile Login & Register Screens
- Admin Orders API Tests
- Admin Products API Tests
- Mobile App Root Layout & Auth
- Web Account & Addresses Pages
- Legacy i18n & Supplier Nav
- Legacy NextAuth & RBAC
- Mobile Shop & Product Screens
- Mobile Account Screen
- Legacy Next.js Dev Tooling
- Shared Types Package
- UI Mockup: Storefront Homepage
- Legacy npm Scripts
- Backend Test Fixtures
- Order & Tracking Number Generation
- Address Book API Tests
- UI Mockup: Homepage Variant
- Monorepo CI & Docs
- UI Mockup: Product Detail Page
- UI Mockup: Admin & Product Pages
- FastAPI Backend Architecture
- Web Icon Sprite Sheet
- Web Admin Categories Page
- Web Admin Variants & Images
- shared-types Package Config
- Legacy Prisma Seed Script
- Audit Log API Tests
- Web Lint Config
- Legacy NextAuth Types
- UI Mockup: Order Stepper
- apps/mobile TS Config
- design-tokens Package Config
- Legacy Next.js README
- Legacy Admin Nav (Next.js)
- Admin Test Fixture
- Mobile App Icon Assets
- apps/web Root TS Config
- Legacy Forgot Password Page
- Legacy Register Page
- Legacy Reset Password Page
- API CI & README
- Postgres Service Config
- Redis Service Config
- Legacy ESLint Config
- Legacy PostCSS Config
- Legacy Vercel Cron Config
- Core Module Description
- Android Icon Foreground Asset
- Android Icon Monochrome Asset
- Mobile App Favicon Asset
- Mobile App Icon Asset
- Mobile Splash Icon Asset
- Web Favicon Asset
- Web Hero Image Asset
- Vite Logo Asset
- API Project Name
- Generic File Icon Asset
- Next.js Logo Asset
- Vercel Logo Asset
- Generic Window Icon Asset
- Next.js Route Handlers Export

## God Nodes (most connected - your core abstractions)
1. `User` - 125 edges
2. `Order` - 92 edges
3. `requireAdminSession()` - 58 edges
4. `logAudit()` - 58 edges
5. `db` - 57 edges
6. `Product` - 54 edges
7. `checkout_payload()` - 51 edges
8. `log_audit()` - 47 edges
9. `UserRole` - 43 edges
10. `OrderStatus` - 42 edges

## Surprising Connections (you probably didn't know these)
- `Next.js Agent Rules Notice` --semantically_similar_to--> `Data Privacy Notice`  [INFERRED] [semantically similar]
  AGENTS.md → docs/DATA_PRIVACY.md
- `api CI Workflow` --references--> `Hiar Business API README`  [INFERRED]
  .github/workflows/api.yml → apps/api/README.md
- `docker-compose Postgres Service (postgres:16-alpine, hiar_business)` --shares_data_with--> `api.yml Postgres Service (postgres:16-alpine, hiar_business_test)`  [INFERRED]
  docker-compose.yml → .github/workflows/api.yml
- `docker-compose Redis Service (redis:7-alpine)` --shares_data_with--> `api.yml Redis Service (redis:7-alpine)`  [INFERRED]
  docker-compose.yml → .github/workflows/api.yml
- `mobile CI Workflow` --references--> `apps/mobile AGENTS.md (Expo version-pinned docs rule)`  [INFERRED]
  .github/workflows/mobile.yml → apps/mobile/AGENTS.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Third-Party Data Sharing Flow** — docs_data_privacy_notice, docs_data_privacy_mpesa_daraja_api, docs_data_privacy_cloudinary, docs_data_privacy_resend, docs_data_privacy_twilio [EXTRACTED 1.00]
- **Personal Data Storage Tables** — docs_data_privacy_users_table, docs_data_privacy_orders_table, docs_data_privacy_order_items_table, docs_data_privacy_payments_table, docs_data_privacy_reviews_table, docs_data_privacy_audit_logs_table, docs_data_privacy_order_status_history_table [EXTRACTED 1.00]
- **Security Measures** — docs_data_privacy_bcrypt_hashing, docs_data_privacy_rbac, src_lib_security_rate_limit_rate_limiting_module, src_lib_security_audit_audit_log_module [EXTRACTED 1.00]
- **Order Fulfillment Progress Tracker** — whatsapp_image_2026_09_06_at_21_39_29_order_received, whatsapp_image_2026_09_06_at_21_39_29_payment_confirmed, whatsapp_image_2026_09_06_at_21_39_29_processing, whatsapp_image_2026_09_06_at_21_39_29_in_warehouse, whatsapp_image_2026_09_06_at_21_39_29_shipping, whatsapp_image_2026_09_06_at_21_39_29_out_for_delivery [EXTRACTED 1.00]
- **Hair Attribute Taxonomy (Type, Texture, Length, Color) Used Across Filters, Info Cards and Products** — whatsapp_image_2026_09_06_at_21_39_29_filter_bar, whatsapp_image_2026_09_06_at_21_39_29_info_cards, whatsapp_image_2026_09_06_at_21_39_29_featured_products [INFERRED 0.75]
- **Wig Product Purchase Flow (Variants → Pricing → Checkout)** — cu_luxury_body_wave_human_hair_wig, cu_product_variants, cu_pricing_shipping_customs, cu_add_to_cart_button [INFERRED 0.85]
- **End-to-End Order Fulfillment Flow (Customer Purchase to Supplier Production)** — docs_mockups_1_customer_product_page, docs_mockups_1_order_management_dashboard, docs_mockups_1_order_10238, docs_mockups_1_supplier_concept [INFERRED 0.75]
- **Hair Attribute Discovery Flow (filter, educate, browse)** — docs_mockups_2_filter_bar, docs_mockups_2_info_cards, docs_mockups_2_all_products [INFERRED 0.75]
- **Post-Purchase Order Visibility Flow** — docs_mockups_2_navigation, docs_mockups_2_order_tracking, docs_mockups_2_footer [INFERRED 0.65]
- **Order #10238 Fulfillment Detail** — mgm_order_10238, mgm_customer_david_lee, mgm_supplier_b, mgm_product_hair_extension [EXTRACTED 1.00]
- **Dashboard Navigation and Actions** — mgm_order_management_dashboard, mgm_orders_overview_table, mgm_update_status_action [INFERRED 0.85]
- **Order Status Progression Flow** — mgm_order_10238, mgm_order_status_workflow, mgm_update_status_action [EXTRACTED 1.00]
- **FastAPI Layered Architecture (apps/api)** — apps_api_readme_core, apps_api_readme_db, apps_api_readme_models, apps_api_readme_schemas, apps_api_readme_services, apps_api_readme_integrations, apps_api_readme_routers, apps_api_readme_worker [INFERRED 0.85]
- **Per-App Path-Filtered CI Workflow Pattern** — _github_workflows_api_ci_workflow, _github_workflows_mobile_ci_workflow, _github_workflows_web_ci_workflow [INFERRED 0.85]
- **Shared Package Consumption for Web/Mobile Parity** — packages_api_client_readme_doc, packages_design_tokens_readme_doc, apps_web_readme_doc, apps_mobile_agents_doc [INFERRED 0.85]

## Communities (130 total, 26 thin omitted)

### Community 0 - "Admin Product Schemas"
Cohesion: 0.05
Nodes (114): delete_image(), _ensure_configured(), Returns (secure_url, public_id). Raises if Cloudinary isn't configured or the…, New vs. the old app: deleting a ProductImage row there never cleaned up the…, upload_image(), AttachmentType, DrawnType, HairCategory (+106 more)

### Community 1 - "Admin Settings & Users Schemas"
Cohesion: 0.06
Nodes (78): create_discount_code(), delete_shipping_rule(), _discount_status(), _discount_to_out(), get_exchange_rate(), get_pricing(), list_discount_codes(), list_shipping_rules() (+70 more)

### Community 2 - "Authentication Schemas"
Cohesion: 0.07
Nodes (74): get_client_ip(), create_access_token(), decode_access_token(), generate_refresh_token(), hash_password(), hash_refresh_token(), is_admin_role(), is_strict_admin() (+66 more)

### Community 3 - "Backend Integration Tests"
Cohesion: 0.06
Nodes (62): checkout_payload(), UUID, _register(), test_deactivate_own_account_locks_out_subsequent_requests(), test_export_includes_own_orders_addresses_reviews(), _deliver_order(), _login(), _register() (+54 more)

### Community 4 - "Returns & Reviews Domain"
Cohesion: 0.07
Nodes (57): ReturnStatus, Return, list_returns(), AsyncSession, get, post, UUID, resolve_return() (+49 more)

### Community 5 - "Legacy Admin Pages (Next.js)"
Cohesion: 0.08
Nodes (45): AdminAuditLogsPage(), AdminCategoriesPage(), createCategory(), deleteCategory(), slugify(), AdminOrderDetailPage(), addMilestone(), createShipment() (+37 more)

### Community 6 - "Pricing & Cart Breakdown Engine"
Cohesion: 0.11
Nodes (50): calculate_single_product_price(), checkout_summary(), AsyncSession, post, Single product/variant price preview (not a full cart) - used by the product…, _to_breakdown_out(), CartItemIn, CheckoutSummaryRequest (+42 more)

### Community 7 - "Backend Config & Migrations"
Cohesion: 0.06
Nodes (39): do_run_migrations(), run_migrations_online(), get_settings(), Central app configuration, replacing the scattered process.env reads across the…, Settings, bank_transfer_details(), initiate_bank_transfer(), Bank transfer is manual: we just record that the customer intends to pay this… (+31 more)

### Community 8 - "SQLAlchemy Catalog Models"
Cohesion: 0.18
Nodes (38): Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin, CartItem, Category, HairColor, HairLength (+30 more)

### Community 9 - "Account Export & Addresses"
Cohesion: 0.11
Nodes (41): Address, deactivate_my_account(), export_my_account_data(), AsyncSession, get, post, create_my_address(), delete_my_address() (+33 more)

### Community 10 - "Notifications & Order UI (Legacy)"
Cohesion: 0.08
Nodes (35): resend, twilio, AccountOrderDetailPage(), cancelOrder(), requestReturn(), ALL_STATUSES, AdminOrdersPage(), ALL_STATUSES (+27 more)

### Community 11 - "Web Admin Hooks & Pages"
Cohesion: 0.09
Nodes (33): AdminAnalyticsPage(), AdminAuditLogsPage(), downloadAnalyticsExport(), downloadAuditLogExport(), useAddMilestone(), useAdminOrder(), useAdminPayments(), useAdminReturns() (+25 more)

### Community 12 - "Legacy Account Pages (Next.js)"
Cohesion: 0.12
Nodes (12): OrderConfirmationPage(), ProductDetailPage(), TrackingPage(), SiteFooter(), SiteHeader(), adapter, db, globalForPrisma (+4 more)

### Community 13 - "Cart API (FastAPI)"
Cohesion: 0.14
Nodes (38): Cart, New vs. the old app, per an explicit scope decision: the old CartProvider was…, add_cart_item(), clear_cart(), get_cart(), merge_guest_cart(), AsyncSession, delete (+30 more)

### Community 14 - "Analytics & Audit Schemas"
Cohesion: 0.12
Nodes (34): AuditLog, export_analytics(), get_dashboard_kpis(), get_finance(), get_operations(), get_revenue(), AsyncSession, get (+26 more)

### Community 15 - "Public Product Catalog API"
Cohesion: 0.11
Nodes (38): get_product(), get_product_facets(), list_categories(), _list_item(), list_products(), list_suppliers(), AsyncSession, CategoryOut (+30 more)

### Community 16 - "apps/web Package Config"
Cohesion: 0.05
Nodes (38): dependencies, @hiar-business/api-client, @hiar-business/shared-types, react, react-dom, react-router, @tanstack/react-query, devDependencies (+30 more)

### Community 17 - "Legacy Cart Context (Next.js)"
Cohesion: 0.08
Nodes (23): nextConfig, withNextIntl, next, geistMono, geistSans, metadata, CartPageClient(), CartContext (+15 more)

### Community 18 - "Legacy Admin Analytics (Next.js)"
Cohesion: 0.13
Nodes (24): FinanceAnalyticsPage(), OperationsAnalyticsPage(), AdminAnalyticsPage(), RevenueAnalyticsPage(), AdminHomePage(), QUICK_LINKS, GET(), GET() (+16 more)

### Community 19 - "Web Auth & Cart Pages"
Cohesion: 0.15
Nodes (26): LoginPage(), handleSubmit(), RegisterPage(), handleSubmit(), CartPage(), captureGuestToken(), CART_QUERY_KEY, guestHeaders() (+18 more)

### Community 20 - "Web Admin Dashboard Pages"
Cohesion: 0.12
Nodes (19): AdminDashboardPage(), useAdminOrders(), useDashboardKpis(), AdminOrdersPage(), AdminProductsPage(), useAdminProducts(), AdminDiscountCodesPage(), AdminExchangeRatePage() (+11 more)

### Community 21 - "Orders & Checkout API"
Cohesion: 0.13
Nodes (28): create_guest_order_access_token(), Replaces the old app's httpOnly `hb_guest_orders` cookie (a comma-joined list…, verify_guest_order_access_token(), cancel_order(), checkout(), get_order(), list_my_orders(), _order_item_to_out() (+20 more)

### Community 22 - "Order State Machine & Notifications"
Cohesion: 0.12
Nodes (28): Port of src/lib/notifications/email.ts. No-ops with a log warning if…, Returns (subject, html). Port of src/lib/notifications/email.ts…, Internal ops notification (not sent to the supplier or customer) whenever a…, send_email(), send_password_reset_email(), supplier_order_email(), supplier_order_status_change_email(), customer_order_status_whatsapp_message() (+20 more)

### Community 23 - "Legacy Supplier Product Pages (Next.js)"
Cohesion: 0.15
Nodes (22): createProduct(), NewProductPage(), slugify(), assertOwnsProduct(), SupplierProductEditPage(), createVariant(), deleteProductImage(), deleteVariant() (+14 more)

### Community 24 - "Admin Order Schemas"
Cohesion: 0.24
Nodes (26): OrderStatus, add_milestone(), create_shipment(), get_order_detail(), list_orders(), _load_order_detail(), _order_to_detail_out(), AsyncSession (+18 more)

### Community 25 - "Legacy Storefront Pages (Next.js)"
Cohesion: 0.15
Nodes (22): next-intl, HomePage(), ProductsPage(), ProductsPageProps, FilterBar(), FilterBarOptions, FilterBarValues, PRICE_BANDS (+14 more)

### Community 26 - "Admin Payments API"
Cohesion: 0.17
Nodes (23): PaymentProviderType, PaymentStatus, Payment, list_admin_payments(), AsyncSession, get, Three independently-filtered views over the same Payment table, matching the…, _to_out() (+15 more)

### Community 27 - "M-Pesa & Legacy Payments Admin"
Cohesion: 0.13
Nodes (20): ioredis, AdminPaymentsPage(), confirmPayment(), rejectPayment(), POST(), schema, POST(), DarajaCallbackBody (+12 more)

### Community 28 - "Payments API (Bank & M-Pesa)"
Cohesion: 0.16
Nodes (24): rate_limit(), Fixed-window counter, direct port of src/lib/security/rate-limit.ts. Fails OPEN…, BankTransferConfirmRequest, confirm_bank_transfer(), mpesa_callback(), Any, AsyncSession, BaseModel (+16 more)

### Community 29 - "apps/mobile Package Config"
Cohesion: 0.08
Nodes (25): devDependencies, @types/react, typescript, @hiar-business/api-client, @hiar-business/shared-types, react, react-dom, @tanstack/react-query (+17 more)

### Community 30 - "Mobile Orders & Checkout Screens"
Cohesion: 0.16
Nodes (16): CheckoutConfirmationScreen(), styles, CANCELLABLE_STATUSES, OrderDetailScreen(), styles, OrdersScreen(), styles, styles (+8 more)

### Community 31 - "Web Auth Context & Token Store"
Cohesion: 0.13
Nodes (21): downloadAuthenticated(), onResponse(), AuthContext, AuthContextValue, AuthProvider(), applyTokenPair(), AuthState, clearSession() (+13 more)

### Community 32 - "Legacy Order/Checkout Routes (Next.js)"
Cohesion: 0.13
Nodes (15): bcryptjs, zod, schema, POST(), GUEST_ORDER_COOKIE, generateOrderNumber(), BANK_TRANSFER_DETAILS, convertUsdToKes() (+7 more)

### Community 33 - "Data Privacy & Compliance Doc"
Cohesion: 0.09
Nodes (23): Next.js Agent Rules Notice, CLAUDE.md Include Directive, audit_logs table, bcrypt Password Hashing, Cloudinary, GDPR, Hiar Business, Kenya Data Protection Act (+15 more)

### Community 34 - "Mobile Cart & Checkout Screens"
Cohesion: 0.19
Nodes (18): CheckoutScreen(), handleSubmit(), styles, CartScreen(), styles, captureGuestToken(), CART_QUERY_KEY, guestHeaders() (+10 more)

### Community 35 - "Generated API Client Package"
Cohesion: 0.10
Nodes (19): dependencies, openapi-fetch, devDependencies, openapi-typescript, main, name, private, scripts (+11 more)

### Community 36 - "Legacy Next.js Package Config"
Cohesion: 0.09
Nodes (21): react, react-dom, @types/node, @types/react, @types/react-dom, typescript, name, private (+13 more)

### Community 37 - "Legacy Pricing API (Next.js)"
Cohesion: 0.18
Nodes (17): PricingSettingsPage(), POST(), SummaryRequestBody, CalculateRequestBody, POST(), calculateCartBreakdown(), CartLineInput, resolveCartLines() (+9 more)

### Community 38 - "Expo App Config"
Cohesion: 0.10
Nodes (20): backgroundColor, backgroundImage, foregroundImage, monochromeImage, adaptiveIcon, predictiveBackGestureEnabled, expo, android (+12 more)

### Community 39 - "Web Admin Product Form"
Cohesion: 0.18
Nodes (14): AdminImage, AdminProductDetail, AdminProductFormPage(), AdminVariant, HAIR_CATEGORIES, useAdminProduct(), ProductFilters, useCategories() (+6 more)

### Community 40 - "apps/web TS Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 41 - "UI Mockup: Order Dashboard"
Cohesion: 0.13
Nodes (20): Order Management Dashboard Screenshot, David Lee (Customer), Fatima Ali (Customer), Gardy Lainrre (Customer), Mark Chen (Customer), Sarah Johnson (Customer), Order #10227, Order #10231 (+12 more)

### Community 42 - "Admin Suppliers API"
Cohesion: 0.28
Nodes (17): Supplier, advance_supplier_order(), create_supplier(), get_supplier_detail(), list_suppliers(), AsyncSession, get, post (+9 more)

### Community 43 - "Web Supplier Portal Pages"
Cohesion: 0.15
Nodes (11): useSupplierOrders(), useSupplierProduct(), useSupplierProducts(), useUpdateSupplierOrderStatus(), NEXT_STATUS, SupplierOrdersPage(), HAIR_CATEGORIES, SupplierProductFormPage() (+3 more)

### Community 44 - "Legacy Next.js Dependencies"
Cohesion: 0.11
Nodes (19): dependencies, bcryptjs, cloudinary, dotenv, ioredis, next, next-auth, next-intl (+11 more)

### Community 45 - "Legacy Next.js TS Config"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 46 - "Reviews & Public Catalog Tests"
Cohesion: 0.18
Nodes (12): ReviewStatus, Review, AsyncSession, post, submit_review(), CreateReviewRequest, MyReviewOut, BaseModel (+4 more)

### Community 47 - "Auth Integration Tests"
Cohesion: 0.18
Nodes (14): The whole point of the live-DB lookup in core/deps.get_current_user: a still-…, Best-effort: only meaningfully exercised when Redis is reachable, but should…, _register(), test_admin_role_not_grantable_via_public_register(), test_deactivated_user_is_rejected_immediately_even_with_valid_token(), test_login_with_correct_password_succeeds(), test_login_with_wrong_password_rejected(), test_logout_revokes_refresh_token() (+6 more)

### Community 48 - "FastAPI Auth Dependencies"
Cohesion: 0.17
Nodes (14): get_current_supplier(), get_current_user(), get_current_user_optional(), _load_active_user(), AsyncSession, Live DB lookup for role/is_active on every request - see…, For guest-allowed endpoints (checkout, cart) that behave differently when a…, ADMIN only (excludes STAFF) - gates payment confirmation, pricing/exchange-rate… (+6 more)

### Community 49 - "Admin Analytics Service"
Cohesion: 0.24
Nodes (16): OrderItem, BestSellingProduct, CountryRevenue, FinanceSummary, get_finance_summary(), get_operations_summary(), get_revenue_summary(), list_current_month_orders() (+8 more)

### Community 50 - "Supplier Order Service Logic"
Cohesion: 0.24
Nodes (15): advance_supplier_order(), create_supplier(), ForbiddenSupplierOrderError, get_supplier_performance(), InvalidTransitionError, NoNextStatusError, AsyncSession, Decimal (+7 more)

### Community 51 - "Mobile Auth Token Store"
Cohesion: 0.21
Nodes (14): clearRefreshToken(), getRefreshToken(), saveRefreshToken(), applyTokenPair(), AuthState, clearSession(), initialize(), listeners (+6 more)

### Community 52 - "apps/web Node TS Config"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 53 - "Supplier Orders API"
Cohesion: 0.32
Nodes (14): SupplierOrderStatus, SupplierOrder, list_my_orders(), AsyncSession, get, post, UUID, _supplier_order_select() (+6 more)

### Community 54 - "apps/mobile Dependencies"
Cohesion: 0.12
Nodes (16): dependencies, expo, expo-constants, expo-linking, expo-router, expo-secure-store, expo-status-bar, @hiar-business/api-client (+8 more)

### Community 55 - "Web Account Order Detail Page"
Cohesion: 0.23
Nodes (10): CANCELLABLE_STATUSES, OrderDetailPage(), OrdersPage(), ConfirmationPage(), ConfirmationState, useCancelOrder(), useMyOrders(), useOrder() (+2 more)

### Community 56 - "Legacy Supplier Portal (Next.js)"
Cohesion: 0.26
Nodes (10): SUPPLIER_TRANSITIONS, SupplierOrdersPage(), updateSupplierOrder(), SupplierDashboardPage(), SupplierProductsPage(), requireRole(), requireSupplierSession(), requireSupplierWithRecord() (+2 more)

### Community 57 - "Legacy Payment Provider Adapters"
Cohesion: 0.22
Nodes (10): bankTransferProvider, mpesaProvider, buildTimestamp(), getAccessToken(), stkPush(), StkPushInput, StkPushResponse, InitiatePaymentInput (+2 more)

### Community 58 - "Mobile Login & Register Screens"
Cohesion: 0.27
Nodes (10): LoginScreen(), handleSubmit(), styles, RegisterScreen(), handleSubmit(), styles, useMergeGuestCartOnLogin(), AuthRequestError (+2 more)

### Community 59 - "Admin Orders API Tests"
Cohesion: 0.44
Nodes (11): Order, _create_order(), _login(), test_add_milestone_fails_without_shipment(), test_admin_can_list_orders_with_filters(), test_admin_can_transition_order_status(), test_admin_can_view_order_detail_with_next_statuses(), test_create_shipment_and_add_milestone() (+3 more)

### Community 60 - "Admin Products API Tests"
Cohesion: 0.32
Nodes (12): _login_admin(), _product_payload(), test_create_and_delete_category(), test_create_product_slugifies_name_and_defaults_to_published(), test_delete_category_in_use_by_product_rejected(), test_delete_category_with_children_rejected(), test_list_products_filters_by_query_and_status(), test_non_admin_cannot_create_product() (+4 more)

### Community 61 - "Mobile App Root Layout & Auth"
Cohesion: 0.22
Nodes (9): queryClient, apiClient, onResponse(), AuthContext, AuthContextValue, AuthProvider(), getState(), tokenStore (+1 more)

### Community 62 - "Web Account & Addresses Pages"
Cohesion: 0.31
Nodes (8): AccountPage(), AddressesPage(), downloadAccountExport(), useAddresses(), useCreateAddress(), useDeactivateAccount(), useDeleteAddress(), useSetDefaultAddress()

### Community 63 - "Legacy i18n & Supplier Nav"
Cohesion: 0.26
Nodes (6): LocaleSwitcher(), SupplierNav(), DEFAULT_LOCALE, Locale, LOCALE_COOKIE, SUPPORTED_LOCALES

### Community 64 - "Legacy NextAuth & RBAC"
Cohesion: 0.23
Nodes (6): next-auth, authConfig, ADMIN_ROLES, SUPPLIER_ROLES, { auth }, config

### Community 65 - "Mobile Shop & Product Screens"
Cohesion: 0.25
Nodes (7): ProductDetailScreen(), styles, ShopScreen(), styles, ProductFilters, useProductDetail(), useProducts()

### Community 66 - "Mobile Account Screen"
Cohesion: 0.36
Nodes (7): AccountScreen(), styles, useAddresses(), useCreateAddress(), useDeactivateAccount(), useDeleteAddress(), useSetDefaultAddress()

### Community 67 - "Legacy Next.js Dev Tooling"
Cohesion: 0.18
Nodes (11): devDependencies, eslint, eslint-config-next, tailwindcss, @tailwindcss/postcss, tsx, @types/node, @types/pg (+3 more)

### Community 68 - "Shared Types Package"
Cohesion: 0.18
Nodes (6): CLIENT_STEPPER_GROUPS, ORDER_STATUS_VALUES, OrderStatus, ADMIN_ROLES, SUPPLIER_ROLES, UserRole

### Community 69 - "UI Mockup: Storefront Homepage"
Cohesion: 0.31
Nodes (10): Hair Products Homepage Mockup, All Hair Products Section, Featured Products Section, Product Filter Bar (Supplier, Hair Type, Length, Texture, Color, Price), Site Footer, Hero Banner: Discover Your Perfect Hair, Hair Guide Info Cards (Length/Texture/Color Charts), Site Navigation Bar (+2 more)

### Community 70 - "Legacy npm Scripts"
Cohesion: 0.20
Nodes (10): scripts, build, db:generate, db:migrate, db:seed, db:studio, dev, lint (+2 more)

### Community 71 - "Backend Test Fixtures"
Cohesion: 0.31
Nodes (8): _redis_client(), _clean_database(), client(), db(), AsyncSession, fixture, AsyncClient, Redis

### Community 72 - "Order & Tracking Number Generation"
Cohesion: 0.33
Nodes (7): generate_order_number(), random_suffix(), generate_tracking_number(), AsyncSession, Exception, Generates a unique HB-YYYYMMDD-XXXXX tracking number, retrying on collision -…, TrackingNumberGenerationError

### Community 73 - "Address Book API Tests"
Cohesion: 0.50
Nodes (7): _address_payload(), _register(), test_cannot_delete_or_set_default_on_someone_elses_address(), test_create_and_list_addresses(), test_creating_default_address_unsets_previous_default(), test_delete_own_address(), test_set_default_address()

### Community 74 - "UI Mockup: Homepage Variant"
Cohesion: 0.36
Nodes (9): Hair Products E-commerce Homepage Screenshot, Featured Products Section (Brazilian Body Wave, Indian Straight, Curly Bundles, Blonde Lace Wig), Filter Bar (Supplier, Hair Type, Length, Texture, Color, Price), Footer (About Us, FAQs, Support, Payment Icons, Contact Info), Hero Banner: 'Discover Your Perfect Hair', Educational Info Cards (Hair Length Chart, Textures & Styles, Hair Color Chart), Top Navigation Bar (Home, Shop, Track Order, Contact, Search, Cart), All Hair Products Grid (Deep Wave, Kinky Curly, Curly, Ombre Body Wave, Water Wave) (+1 more)

### Community 75 - "Monorepo CI & Docs"
Cohesion: 0.43
Nodes (8): mobile CI Workflow, web CI Workflow, apps/mobile AGENTS.md (Expo version-pinned docs rule), apps/mobile CLAUDE.md, apps/web index.html entry point (mounts src/main.tsx, title Hiar Business), apps/web README (React + TypeScript + Vite template), @hiar-business/api-client README, @hiar-business/design-tokens README

### Community 77 - "UI Mockup: Product Detail Page"
Cohesion: 0.29
Nodes (8): Product Detail Page Screenshot (cu.jpeg), Add to Cart Action, Customer / Product Management UI Module, Luxury Body Wave Human Hair Wig (Product), Made-to-Order / 7-10 Day Processing Time, Pricing, International Shipping & Customs Estimate, Product Variant Selectors (Length, Density, Color), Shipping Destination Flags (US, UK, Kenya)

### Community 78 - "UI Mockup: Admin & Product Pages"
Cohesion: 0.32
Nodes (8): Hair Business UI Mockup (Customer Page + Order Dashboard), Customer Product Detail Page (UI Screen), International Shipping & Customs Pricing Breakdown, Luxury Body Wave Human Hair Wig (Product), Order #10238 (David Lee, Supplier B), Order Management Dashboard (UI Screen), Order Status Workflow (Created > Sent to Supplier > In Production > Pending QC > Ready for Dispatch), Supplier Assignment (Supplier A/B/C)

### Community 79 - "FastAPI Backend Architecture"
Cohesion: 0.29
Nodes (7): db/ (SQLAlchemy session), integrations/ (third-party clients), models/ (ORM models), routers/ (HTTP endpoints), schemas/ (Pydantic schemas), services/ (business logic: pricing, orders, payments, notifications), worker/ (arq background jobs)

### Community 80 - "Web Icon Sprite Sheet"
Cohesion: 0.29
Nodes (7): Bluesky Social Icon, Discord Social Icon, Documentation Icon, GitHub Social Icon, Icon Sprite (icons.svg), Community/Social Group Icon, X (Twitter) Social Icon

### Community 81 - "Web Admin Categories Page"
Cohesion: 0.43
Nodes (4): AdminCategoriesPage(), useAdminCategories(), useCreateCategory(), useDeleteCategory()

### Community 82 - "Web Admin Variants & Images"
Cohesion: 0.52
Nodes (7): VariantsAndImages(), addVariant(), deleteImage(), deleteVariant(), invalidate(), updateStock(), uploadImage()

### Community 83 - "shared-types Package Config"
Cohesion: 0.29
Nodes (6): main, name, private, type, types, version

### Community 84 - "Legacy Prisma Seed Script"
Cohesion: 0.29
Nodes (4): adapter, db, dotenv, @prisma/adapter-pg

### Community 85 - "Audit Log API Tests"
Cohesion: 0.53
Nodes (4): _login(), test_export_audit_logs_returns_csv(), test_filter_by_action_and_entity_type(), test_list_audit_logs_includes_actor_email_and_entity_types()

### Community 86 - "Web Lint Config"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 87 - "Legacy NextAuth Types"
Cohesion: 0.33
Nodes (5): JWT, next-auth, next-auth/jwt, Session, User

### Community 88 - "UI Mockup: Order Stepper"
Cohesion: 0.33
Nodes (6): Order Fulfillment Step: In Warehouse, Order Fulfillment Step: Order Received, Order Fulfillment Step: Out for Delivery, Order Fulfillment Step: Payment Confirmed, Order Fulfillment Step: Processing, Order Fulfillment Step: Shipping

### Community 89 - "apps/mobile TS Config"
Cohesion: 0.40
Nodes (4): compilerOptions, strict, extends, expo/tsconfig.base

### Community 90 - "design-tokens Package Config"
Cohesion: 0.40
Nodes (4): main, name, private, version

### Community 91 - "Legacy Next.js README"
Cohesion: 0.40
Nodes (5): create-next-app, Geist Font, next/font, Hair Project README (Next.js create-next-app), Vercel Platform (deployment)

### Community 93 - "Admin Test Fixture"
Cohesion: 0.50
Nodes (4): admin_user(), AsyncSession, fixture, User

### Community 94 - "Mobile App Icon Assets"
Cohesion: 0.50
Nodes (4): Android Adaptive Icon, Adaptive Icon Safe-Zone Guide Template, Android Icon Background, Expo Mobile App Scaffold

## Ambiguous Edges - Review These
- `Order Management Dashboard Screenshot` → `Garbled/Misspelled UI Text Artifacts`  [AMBIGUOUS]
  mgm.jpeg · relation: references
- `Order #10227` → `Supplier C`  [AMBIGUOUS]
  mgm.jpeg · relation: references

## Knowledge Gaps
- **426 isolated node(s):** `hiar-business-api`, `name`, `slug`, `version`, `orientation` (+421 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 685 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Order Management Dashboard Screenshot` and `Garbled/Misspelled UI Text Artifacts`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Order #10227` and `Supplier C`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `User` connect `SQLAlchemy Catalog Models` to `Admin Product Schemas`, `Admin Settings & Users Schemas`, `Authentication Schemas`, `Backend Integration Tests`, `Returns & Reviews Domain`, `Account Export & Addresses`, `Cart API (FastAPI)`, `Orders & Checkout API`, `Admin Order Schemas`, `Admin Payments API`, `Payments API (Bank & M-Pesa)`, `Admin Suppliers API`, `Reviews & Public Catalog Tests`, `Auth Integration Tests`, `FastAPI Auth Dependencies`, `Supplier Order Service Logic`, `Supplier Orders API`, `Admin Orders API Tests`, `Admin Test Fixture`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `Order` connect `Admin Orders API Tests` to `Admin Settings & Users Schemas`, `Authentication Schemas`, `Backend Integration Tests`, `Returns & Reviews Domain`, `Backend Config & Migrations`, `SQLAlchemy Catalog Models`, `Account Export & Addresses`, `Admin Suppliers API`, `Reviews & Public Catalog Tests`, `Admin Analytics Service`, `Orders & Checkout API`, `Supplier Orders API`, `Order State Machine & Notifications`, `Admin Order Schemas`, `Admin Payments API`, `Payments API (Bank & M-Pesa)`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `checkout_payload()` connect `Backend Integration Tests` to `Authentication Schemas`, `Returns & Reviews Domain`, `SQLAlchemy Catalog Models`, `Admin Payments API`, `Admin Orders API Tests`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Are the 72 inferred relationships involving `User` (e.g. with `get_current_supplier()` and `get_current_user()`) actually correct?**
  _`User` has 72 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Order` (e.g. with `OrderStatus` and `add_milestone()`) actually correct?**
  _`Order` has 59 INFERRED edges - model-reasoned connections that need verification._