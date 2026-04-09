# Shopline Open API — Endpoint Inventory

> **Source**: https://open-api.docs.shoplineapp.com
> **Scanned**: 2026-04-09
> **Purpose**: Complete endpoint catalog of Shopline Open API v1, used as the source of truth for planning MCP tool coverage.

This file enumerates every endpoint discovered across all resource sections of the Shopline Open API documentation sidebar. It is grouped by resource section, with HTTP method, path, one-line description, and read/write classification.

Use this document together with `reference/shopline.md` (which defines the project goal of complete API coverage) when planning new tools.

---

## Orders
- GET /v1/orders — List orders sorted by time [read]
- GET /v1/orders/{id} — Get single order details [read]
- GET /v1/orders/search — Search orders with advanced criteria [read]
- GET /v1/orders/{id}/labels — Get order delivery labels [read]
- GET /v1/orders/{id}/tags — Get order tags [read]
- GET /v1/orders/{id}/action-logs — Get order action logs [read]
- GET /v1/orders/{id}/transactions — Get order transactions [read]
- GET /v1/orders/archived — Get archived orders [read]
- POST /v1/orders — Create order [write]
- POST /v1/orders/{id}/shipment — Execute shipment for order [write]
- POST /v1/orders/shipment/bulk — Bulk execute shipment [write]
- POST /v1/orders/{id}/split — Split order into multiple shipments [write]
- POST /v1/orders/{id}/cancel — Cancel order [write]
- PATCH /v1/orders/{id} — Update order [write]
- PATCH /v1/orders/{id}/status — Modify order status [write]
- PATCH /v1/orders/{id}/delivery-status — Update delivery status [write]
- PATCH /v1/orders/{id}/payment-status — Update payment status [write]
- PATCH /v1/orders/{id}/tags — Modify order tags [write]

## Customer
- GET /v1/customers — List customers sorted by time [read]
- GET /v1/customers/{id} — Get single customer details [read]
- GET /v1/customers/search — Search customers [read]
- GET /v1/customers/{id}/store-credit-history — Get store credit history [read]
- GET /v1/customers/{id}/member-points — Get member points history [read]
- GET /v1/customers/{id}/promotions — Get customer promotions [read]
- POST /v1/customers — Create customer [write]
- POST /v1/customers/{id}/tags — Add or remove customer tags [write]
- PUT /v1/customers/{id} — Update customer [write]
- PUT /v1/customers/{id}/tags — Modify customer tags [write]
- PUT /v1/customers/{id}/store-credits — Update store credits [write]
- PUT /v1/customers/{id}/member-points — Adjust member points [write]
- DELETE /v1/customers/{id} — Delete customer [write]

## Category
- GET /v1/categories — List categories [read]
- GET /v1/categories/{id} — Get single category [read]
- POST /v1/categories — Create category [write]
- PUT /v1/categories/{id} — Update category [write]
- DELETE /v1/categories/{id} — Delete category [write]

## Products
- GET /v1/products — List products sorted by creation time [read]
- GET /v1/products/{id} — Get single product [read]
- GET /v1/products/search — Search products [read]
- GET /v1/products/locked-inventory — Get locked inventory counts [read]
- POST /v1/products — Create product [write]
- POST /v1/products/{id}/images — Add product images [write]
- POST /v1/products/{id}/variations — Create product variation [write]
- POST /v1/products/{id}/tags — Add/remove product tags [write]
- POST /v1/products/bulk-assign-categories — Bulk assign categories [write]
- PUT /v1/products/{id} — Update product [write]
- PUT /v1/products/{id}/quantity — Update product quantity [write]
- PUT /v1/products/{id}/price — Update product price [write]
- PUT /v1/products/{id}/variations/{variation_id} — Update variation [write]
- PUT /v1/products/{id}/variations/{variation_id}/quantity — Update variation quantity [write]
- PUT /v1/products/{id}/variations/{variation_id}/price — Update variation price [write]
- PUT /v1/products/bulk-update-quantities — Bulk update quantities by SKU [write]
- DELETE /v1/products/{id} — Delete product [write]
- DELETE /v1/products/{id}/images — Delete product images [write]
- DELETE /v1/products/{id}/variations/{variation_id} — Delete variation [write]

## Promotions
- GET /v1/promotions — Get promotions [read]
- GET /v1/promotions/{id} — Get promotion details [read]
- GET /v1/promotions/search — Search promotions [read]
- POST /v1/promotions — Create promotion [write]
- POST /v1/coupons/send — Send coupon [write]
- POST /v1/coupons/redeem — Redeem coupon [write]
- POST /v1/coupons/claim — Claim coupon [write]
- PUT /v1/promotions/{id} — Update promotion [write]
- DELETE /v1/promotions/{id} — Delete promotion [write]

## Warehouse
- GET /v1/warehouses — Get warehouse information [read]

## Return Order
- GET /v1/return_orders — Get return orders [read]
- GET /v1/return_orders/{id} — Get return order by ID [read]
- POST /v1/return_orders — Create return order [write]
- PUT /v1/return_orders/{id} — Update return order [write]

## Channel
- GET /v1/channels — Get channels (staff/merchant wise) [read]
- GET /v1/channels/{id} — Get specific channel [read]

## Token
- GET /v1/token/info — Get access token information [read]

## Customer Group
- GET /v1/customer-groups — Get customer groups [read]
- GET /v1/customer-groups/search — Search customer groups [read]
- GET /v1/customer-groups/{id}/customers — Get customer IDs in group [read]

## Customers Store Credits
- GET /v1/user_credits — Get customer store credits [read]

## CustomFields
- GET /v1/custom_fields — Get customer custom fields [read]

## MembershipTiers
- GET /v1/membership_tiers — Get membership tiers [read]
- GET /v1/customers/{id}/membership-tier-history — Get tier history [read]

## Member Point Rules
- GET /v1/member_point_rules — Get member point rules [read]

## Conversations
- GET /v1/conversations — Get conversations by platform [read]
- GET /v1/conversations/{id}/messages — Get conversation messages [read]
- POST /v1/conversations/order-messages — Create order message [write]
- POST /v1/conversations/shop-messages — Create shop message [write]

## Gifts
- GET /v1/gifts — Get gifts [read]
- GET /v1/gifts/search — Search gifts [read]
- POST /v1/gifts — Create gift [write]
- PATCH /v1/gifts/{id} — Update gift [write]
- PATCH /v1/gifts/quantity-by-sku — Update gift quantity by SKU [write]

## Addon Products
- GET /v1/addon_products — Get addon products [read]
- GET /v1/addon_products/search — Search addon products [read]
- POST /v1/addon_products — Create addon product [write]
- PUT /v1/addon_products/{id} — Update addon product [write]
- PUT /v1/addon_products/{id}/quantity — Update addon quantity [write]
- PUT /v1/addon_products/sku/quantity — Update addon quantity by SKU [write]

## Settings
- GET /v1/settings/app — Get app settings (deprecated) [read]

## Payment
- GET /v1/payments — Get payment methods [read]

## Delivery Options
- GET /v1/delivery_options — Get delivery options [read]
- GET /v1/delivery_options/{id} — Get delivery option details [read]
- GET /v1/delivery_options/{id}/time_slots — Get delivery time slots [read]
- PUT /v1/delivery_options/{id}/pickup_store — Update pickup store [write]

## Merchant
- GET /v1/merchants — Get merchants for current token [read]
- GET /v1/merchants/{id} — Get merchant details [read]
- PUT /v1/merchants/{id} — Update merchant [write]

## Staff
- GET /v1/staffs/{staff_id}/permissions — Get staff permissions [read]

## Tax
- GET /v1/taxes — Get tax configuration [read]

## Product Review Comments
- GET /v1/product_review_comments — Get review comments [read]
- GET /v1/product_review_comments/{id} — Get single review comment [read]
- POST /v1/product_review_comments — Create review comment [write]
- POST /v1/product_review_comments/bulk — Bulk create review comments [write]
- PATCH /v1/product_review_comments — Bulk update review comments [write]
- PATCH /v1/product_review_comments/{id} — Update review comment [write]
- DELETE /v1/product_review_comments/{id} — Delete review comment [write]
- DELETE /v1/product_review_comments — Bulk delete review comments [write]

## Agents
- GET /v1/agents — Get agents list [read]

## Product Subscription
- GET /v1/product_subscriptions — Get product subscriptions [read]
- GET /v1/product_subscriptions/{id} — Get product subscription details [read]

## Media
- POST /v1/media — Upload media file [write]

## Order Delivery
- GET /v1/order_deliveries/{id} — Get order delivery [read]
- PUT /v1/order_deliveries/{id} — Update order delivery [write]

## Flash Price Campaign
- GET /v1/flash_price_campaigns — Get flash price campaigns [read]
- GET /v1/flash_price_campaigns/{id} — Get campaign details [read]
- POST /v1/flash_price_campaigns — Create campaign [write]
- PUT /v1/flash_price_campaigns/{id} — Update campaign [write]
- DELETE /v1/flash_price_campaigns/{id} — Delete campaign [write]

## Affiliate Campaign
- GET /v1/affiliate_campaigns — Get affiliate campaigns [read]
- GET /v1/affiliate_campaigns/{id} — Get campaign details [read]
- GET /v1/affiliate_campaigns/{id}/order_usage — Get campaign usage stats [read]
- POST /v1/affiliate_campaigns — Create campaign [write]
- PUT /v1/affiliate_campaigns/{id} — Update campaign [write]
- DELETE /v1/affiliate_campaigns/{id} — Delete campaign [write]

## Metafields
- POST /merchants/current/app-metafields — Create merchant app metafield [write]

## Purchase Orders
- GET /v1/pos/purchase_orders — Get purchase orders [read]
- GET /v1/pos/purchase_orders/{id} — Get purchase order details [read]
- POST /v1/pos/purchase_orders — Create purchase order [write]
- DELETE /v1/pos/purchase_orders — Delete purchase orders [write]

---

## Summary Stats

| Metric | Count |
|---|---|
| Resource sections | 32 |
| Total endpoints | 129 |
| Read endpoints (GET) | 55 |
| Write endpoints (POST/PUT/PATCH/DELETE) | 74 |

## Coverage Status (as of 2026-04-09)

Currently the MCP server ships 19 tools that internally use ~8 endpoints (orders, orders/search, orders/{id}, products, products/search, products/{id}/stocks, warehouses, return_orders, categories, promotions). All other endpoints in this inventory are candidates for new tool coverage.
