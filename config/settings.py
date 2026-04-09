"""Shopline API 設定"""
import os

BASE_URL = "https://open.shopline.io"
API_VERSION = "v1"
ACCESS_TOKEN = os.environ.get("SHOPLINE_API_TOKEN", "")

# 預設分頁設定
DEFAULT_PER_PAGE = 50  # API 建議上限
DEFAULT_SORT = "desc"

# API 端點 — 完整 Shopline Open API v1 覆蓋
# 命名規則: {resource}_{action} 或 {resource}_{sub_resource}
ENDPOINTS = {
    # === Orders ===
    "orders": f"/{API_VERSION}/orders",
    "orders_search": f"/{API_VERSION}/orders/search",
    "order_detail": f"/{API_VERSION}/orders/{{order_id}}",
    "order_labels": f"/{API_VERSION}/orders/{{order_id}}/labels",
    "order_tags": f"/{API_VERSION}/orders/{{order_id}}/tags",
    "order_action_logs": f"/{API_VERSION}/orders/{{order_id}}/action-logs",
    "order_transactions": f"/{API_VERSION}/orders/{{order_id}}/transactions",
    "orders_archived": f"/{API_VERSION}/orders/archived",
    "order_create": f"/{API_VERSION}/orders",
    "order_update": f"/{API_VERSION}/orders/{{order_id}}",
    "order_shipment": f"/{API_VERSION}/orders/{{order_id}}/shipment",
    "orders_shipment_bulk": f"/{API_VERSION}/orders/shipment/bulk",
    "order_split": f"/{API_VERSION}/orders/{{order_id}}/split",
    "order_cancel": f"/{API_VERSION}/orders/{{order_id}}/cancel",
    "order_status": f"/{API_VERSION}/orders/{{order_id}}/status",
    "order_delivery_status": f"/{API_VERSION}/orders/{{order_id}}/delivery-status",
    "order_payment_status": f"/{API_VERSION}/orders/{{order_id}}/payment-status",
    "order_tags_update": f"/{API_VERSION}/orders/{{order_id}}/tags",

    # === Customers ===
    "customers": f"/{API_VERSION}/customers",
    "customers_search": f"/{API_VERSION}/customers/search",
    "customer_detail": f"/{API_VERSION}/customers/{{customer_id}}",
    "customer_store_credit_history": f"/{API_VERSION}/customers/{{customer_id}}/store-credit-history",
    "customer_member_points": f"/{API_VERSION}/customers/{{customer_id}}/member-points",
    "customer_promotions": f"/{API_VERSION}/customers/{{customer_id}}/promotions",
    "customer_create": f"/{API_VERSION}/customers",
    "customer_update": f"/{API_VERSION}/customers/{{customer_id}}",
    "customer_delete": f"/{API_VERSION}/customers/{{customer_id}}",
    "customer_tags": f"/{API_VERSION}/customers/{{customer_id}}/tags",
    "customer_store_credits_update": f"/{API_VERSION}/customers/{{customer_id}}/store-credits",
    "customer_member_points_update": f"/{API_VERSION}/customers/{{customer_id}}/member-points",

    # === Customer Groups ===
    "customer_groups": f"/{API_VERSION}/customer-groups",
    "customer_groups_search": f"/{API_VERSION}/customer-groups/search",
    "customer_group_customers": f"/{API_VERSION}/customer-groups/{{group_id}}/customers",

    # === Store Credits ===
    "user_credits": f"/{API_VERSION}/user_credits",

    # === Custom Fields ===
    "custom_fields": f"/{API_VERSION}/custom_fields",

    # === Membership Tiers ===
    "membership_tiers": f"/{API_VERSION}/membership_tiers",
    "customer_membership_tier_history": f"/{API_VERSION}/customers/{{customer_id}}/membership-tier-history",

    # === Member Point Rules ===
    "member_point_rules": f"/{API_VERSION}/member_point_rules",

    # === Products ===
    "products": f"/{API_VERSION}/products",
    "products_search": f"/{API_VERSION}/products/search",
    "product_detail": f"/{API_VERSION}/products/{{product_id}}",
    "product_stocks": f"/{API_VERSION}/products/{{product_id}}/stocks",
    "products_locked_inventory": f"/{API_VERSION}/products/locked-inventory",
    "product_create": f"/{API_VERSION}/products",
    "product_update": f"/{API_VERSION}/products/{{product_id}}",
    "product_delete": f"/{API_VERSION}/products/{{product_id}}",
    "product_images": f"/{API_VERSION}/products/{{product_id}}/images",
    "product_variations_create": f"/{API_VERSION}/products/{{product_id}}/variations",
    "product_variation_update": f"/{API_VERSION}/products/{{product_id}}/variations/{{variation_id}}",
    "product_variation_delete": f"/{API_VERSION}/products/{{product_id}}/variations/{{variation_id}}",
    "product_variation_quantity": f"/{API_VERSION}/products/{{product_id}}/variations/{{variation_id}}/quantity",
    "product_variation_price": f"/{API_VERSION}/products/{{product_id}}/variations/{{variation_id}}/price",
    "product_quantity": f"/{API_VERSION}/products/{{product_id}}/quantity",
    "product_price": f"/{API_VERSION}/products/{{product_id}}/price",
    "product_tags": f"/{API_VERSION}/products/{{product_id}}/tags",
    "products_bulk_quantities": f"/{API_VERSION}/products/bulk-update-quantities",
    "products_bulk_categories": f"/{API_VERSION}/products/bulk-assign-categories",

    # === Categories ===
    "categories": f"/{API_VERSION}/categories",
    "category_detail": f"/{API_VERSION}/categories/{{category_id}}",
    "category_create": f"/{API_VERSION}/categories",
    "category_update": f"/{API_VERSION}/categories/{{category_id}}",
    "category_delete": f"/{API_VERSION}/categories/{{category_id}}",

    # === Promotions ===
    "promotions": f"/{API_VERSION}/promotions",
    "promotion_detail": f"/{API_VERSION}/promotions/{{promotion_id}}",
    "promotions_search": f"/{API_VERSION}/promotions/search",
    "promotion_create": f"/{API_VERSION}/promotions",
    "promotion_update": f"/{API_VERSION}/promotions/{{promotion_id}}",
    "promotion_delete": f"/{API_VERSION}/promotions/{{promotion_id}}",
    "coupon_send": f"/{API_VERSION}/coupons/send",
    "coupon_redeem": f"/{API_VERSION}/coupons/redeem",
    "coupon_claim": f"/{API_VERSION}/coupons/claim",

    # === Warehouses ===
    "warehouses": f"/{API_VERSION}/warehouses",

    # === Return Orders ===
    "return_orders": f"/{API_VERSION}/return_orders",
    "return_order_detail": f"/{API_VERSION}/return_orders/{{return_order_id}}",
    "return_order_create": f"/{API_VERSION}/return_orders",
    "return_order_update": f"/{API_VERSION}/return_orders/{{return_order_id}}",

    # === Channels ===
    "channels": f"/{API_VERSION}/channels",
    "channel_detail": f"/{API_VERSION}/channels/{{channel_id}}",

    # === Token ===
    "token_info": f"/{API_VERSION}/token/info",

    # === Conversations ===
    "conversations": f"/{API_VERSION}/conversations",
    "conversation_messages": f"/{API_VERSION}/conversations/{{conversation_id}}/messages",
    "conversation_order_message": f"/{API_VERSION}/conversations/order-messages",
    "conversation_shop_message": f"/{API_VERSION}/conversations/shop-messages",

    # === Gifts ===
    "gifts": f"/{API_VERSION}/gifts",
    "gifts_search": f"/{API_VERSION}/gifts/search",
    "gift_create": f"/{API_VERSION}/gifts",
    "gift_update": f"/{API_VERSION}/gifts/{{gift_id}}",
    "gift_quantity_by_sku": f"/{API_VERSION}/gifts/quantity-by-sku",

    # === Addon Products ===
    "addon_products": f"/{API_VERSION}/addon_products",
    "addon_products_search": f"/{API_VERSION}/addon_products/search",
    "addon_product_create": f"/{API_VERSION}/addon_products",
    "addon_product_update": f"/{API_VERSION}/addon_products/{{addon_product_id}}",
    "addon_product_quantity": f"/{API_VERSION}/addon_products/{{addon_product_id}}/quantity",
    "addon_product_sku_quantity": f"/{API_VERSION}/addon_products/sku/quantity",

    # === Settings ===
    "settings_app": f"/{API_VERSION}/settings/app",

    # === Payment ===
    "payments": f"/{API_VERSION}/payments",

    # === Delivery Options ===
    "delivery_options": f"/{API_VERSION}/delivery_options",
    "delivery_option_detail": f"/{API_VERSION}/delivery_options/{{delivery_option_id}}",
    "delivery_option_time_slots": f"/{API_VERSION}/delivery_options/{{delivery_option_id}}/time_slots",
    "delivery_option_pickup_store": f"/{API_VERSION}/delivery_options/{{delivery_option_id}}/pickup_store",

    # === Merchant ===
    "merchants": f"/{API_VERSION}/merchants",
    "merchant_detail": f"/{API_VERSION}/merchants/{{merchant_id}}",
    "merchant_update": f"/{API_VERSION}/merchants/{{merchant_id}}",

    # === Staff ===
    "staff_permissions": f"/{API_VERSION}/staffs/{{staff_id}}/permissions",

    # === Tax ===
    "taxes": f"/{API_VERSION}/taxes",

    # === Product Review Comments ===
    "product_review_comments": f"/{API_VERSION}/product_review_comments",
    "product_review_comment_detail": f"/{API_VERSION}/product_review_comments/{{comment_id}}",
    "product_review_comment_create": f"/{API_VERSION}/product_review_comments",
    "product_review_comments_bulk_create": f"/{API_VERSION}/product_review_comments/bulk",
    "product_review_comment_update": f"/{API_VERSION}/product_review_comments/{{comment_id}}",
    "product_review_comments_bulk_update": f"/{API_VERSION}/product_review_comments",
    "product_review_comment_delete": f"/{API_VERSION}/product_review_comments/{{comment_id}}",
    "product_review_comments_bulk_delete": f"/{API_VERSION}/product_review_comments",

    # === Agents ===
    "agents": f"/{API_VERSION}/agents",

    # === Product Subscription ===
    "product_subscriptions": f"/{API_VERSION}/product_subscriptions",
    "product_subscription_detail": f"/{API_VERSION}/product_subscriptions/{{subscription_id}}",

    # === Media ===
    "media_create": f"/{API_VERSION}/media",

    # === Order Delivery ===
    "order_delivery_detail": f"/{API_VERSION}/order_deliveries/{{delivery_id}}",
    "order_delivery_update": f"/{API_VERSION}/order_deliveries/{{delivery_id}}",

    # === Flash Price Campaign ===
    "flash_price_campaigns": f"/{API_VERSION}/flash_price_campaigns",
    "flash_price_campaign_detail": f"/{API_VERSION}/flash_price_campaigns/{{campaign_id}}",
    "flash_price_campaign_create": f"/{API_VERSION}/flash_price_campaigns",
    "flash_price_campaign_update": f"/{API_VERSION}/flash_price_campaigns/{{campaign_id}}",
    "flash_price_campaign_delete": f"/{API_VERSION}/flash_price_campaigns/{{campaign_id}}",

    # === Affiliate Campaign ===
    "affiliate_campaigns": f"/{API_VERSION}/affiliate_campaigns",
    "affiliate_campaign_detail": f"/{API_VERSION}/affiliate_campaigns/{{campaign_id}}",
    "affiliate_campaign_order_usage": f"/{API_VERSION}/affiliate_campaigns/{{campaign_id}}/order_usage",
    "affiliate_campaign_create": f"/{API_VERSION}/affiliate_campaigns",
    "affiliate_campaign_update": f"/{API_VERSION}/affiliate_campaigns/{{campaign_id}}",
    "affiliate_campaign_delete": f"/{API_VERSION}/affiliate_campaigns/{{campaign_id}}",

    # === Metafields ===
    "metafield_create": "/merchants/current/app-metafields",

    # === Purchase Orders ===
    "purchase_orders": f"/{API_VERSION}/pos/purchase_orders",
    "purchase_order_detail": f"/{API_VERSION}/pos/purchase_orders/{{purchase_order_id}}",
    "purchase_order_create": f"/{API_VERSION}/pos/purchase_orders",
    "purchase_order_delete": f"/{API_VERSION}/pos/purchase_orders",
}


def get_headers():
    if not ACCESS_TOKEN:
        raise RuntimeError(
            "SHOPLINE_API_TOKEN environment variable is not set. "
            "Run: export SHOPLINE_API_TOKEN=your_token_here"
        )
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def get_url(endpoint_key, **kwargs):
    """取得完整 API URL，支援路徑參數替換"""
    path = ENDPOINTS[endpoint_key].format(**kwargs)
    return f"{BASE_URL}{path}"
