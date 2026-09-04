"""Phase 2: Merchant Marketplace Simulator schema migration

Revision ID: 002_phase2_marketplace_simulator
Revises: 001_initial_schema
Create Date: 2026-09-04 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_phase2_marketplace_simulator'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Merchants table
    op.create_table(
        'merchants',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('merchant_code', sa.String(length=32), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('capabilities', sa.JSON(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False, server_default='4.8'),
        sa.Column('logo_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_code')
    )
    op.create_index(op.f('ix_merchants_id'), 'merchants', ['id'], unique=False)
    op.create_index(op.f('ix_merchants_merchant_code'), 'merchants', ['merchant_code'], unique=True)

    # 2. Products table
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('merchant_id', sa.String(length=64), nullable=False),
        sa.Column('sku', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('brand', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=128), nullable=False),
        sa.Column('model', sa.String(length=128), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('rating', sa.Float(), nullable=False, server_default='4.5'),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('specs', sa.JSON(), nullable=True),
        sa.Column('image_url', sa.String(length=512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_merchant_id'), 'products', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=False)
    op.create_index(op.f('ix_products_title'), 'products', ['title'], unique=False)
    op.create_index(op.f('ix_products_brand'), 'products', ['brand'], unique=False)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_current_price'), 'products', ['current_price'], unique=False)
    op.create_index(op.f('ix_products_rating'), 'products', ['rating'], unique=False)
    op.create_index('ix_products_merchant_category', 'products', ['merchant_id', 'category'], unique=False)
    op.create_index('ix_products_category_price', 'products', ['category', 'current_price'], unique=False)

    # 3. Inventory table
    op.create_table(
        'inventory',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('product_id', sa.String(length=64), nullable=False),
        sa.Column('merchant_id', sa.String(length=64), nullable=False),
        sa.Column('available_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reserved_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sold_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('availability_state', sa.String(length=32), nullable=False, server_default='IN_STOCK'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id')
    )
    op.create_index(op.f('ix_inventory_id'), 'inventory', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_product_id'), 'inventory', ['product_id'], unique=True)
    op.create_index(op.f('ix_inventory_merchant_id'), 'inventory', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_inventory_availability_state'), 'inventory', ['availability_state'], unique=False)

    # 4. Prices table
    op.create_table(
        'prices',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('product_id', sa.String(length=64), nullable=False),
        sa.Column('base_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prices_id'), 'prices', ['id'], unique=False)
    op.create_index(op.f('ix_prices_product_id'), 'prices', ['product_id'], unique=False)

    # 5. Discounts table
    op.create_table(
        'discounts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('merchant_id', sa.String(length=64), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('discount_type', sa.String(length=32), nullable=False, server_default='PERCENTAGE'),
        sa.Column('discount_value', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('min_order_value', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('max_discount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discounts_id'), 'discounts', ['id'], unique=False)
    op.create_index(op.f('ix_discounts_merchant_id'), 'discounts', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_discounts_code'), 'discounts', ['code'], unique=False)

    # 6. Shipping Options table
    op.create_table(
        'shipping_options',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('merchant_id', sa.String(length=64), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('cost', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('estimated_days', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('delivery_type', sa.String(length=32), nullable=False, server_default='STANDARD'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shipping_options_id'), 'shipping_options', ['id'], unique=False)
    op.create_index(op.f('ix_shipping_options_merchant_id'), 'shipping_options', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_shipping_options_code'), 'shipping_options', ['code'], unique=False)

    # 7. Carts table
    op.create_table(
        'carts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('merchant_id', sa.String(length=64), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('shipping_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('grand_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_carts_id'), 'carts', ['id'], unique=False)
    op.create_index(op.f('ix_carts_merchant_id'), 'carts', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_carts_session_id'), 'carts', ['session_id'], unique=False)
    op.create_index(op.f('ix_carts_status'), 'carts', ['status'], unique=False)

    # 8. Cart Items table
    op.create_table(
        'cart_items',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('cart_id', sa.String(length=64), nullable=False),
        sa.Column('product_id', sa.String(length=64), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cart_items_id'), 'cart_items', ['id'], unique=False)
    op.create_index(op.f('ix_cart_items_cart_id'), 'cart_items', ['cart_id'], unique=False)
    op.create_index(op.f('ix_cart_items_product_id'), 'cart_items', ['product_id'], unique=False)

    # 9. Checkout Sessions table
    op.create_table(
        'checkout_sessions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('cart_id', sa.String(length=64), nullable=False),
        sa.Column('merchant_id', sa.String(length=64), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discount_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('shipping_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('grand_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('shipping_option_id', sa.String(length=64), nullable=True),
        sa.Column('promo_code', sa.String(length=64), nullable=True),
        sa.Column('items_snapshot', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checkout_sessions_id'), 'checkout_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_checkout_sessions_cart_id'), 'checkout_sessions', ['cart_id'], unique=False)
    op.create_index(op.f('ix_checkout_sessions_merchant_id'), 'checkout_sessions', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_checkout_sessions_status'), 'checkout_sessions', ['status'], unique=False)

    # 10. Orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('order_number', sa.String(length=64), nullable=False),
        sa.Column('merchant_id', sa.String(length=64), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discount_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('shipping_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('grand_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('shipping_address', sa.Text(), nullable=False),
        sa.Column('shipping_method', sa.String(length=64), nullable=False, server_default='STANDARD'),
        sa.Column('payment_method', sa.String(length=64), nullable=False, server_default='UPI_SIMULATED'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='CREATED'),
        sa.Column('tracking_number', sa.String(length=64), nullable=True),
        sa.Column('estimated_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_merchant_id'), 'orders', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_orders_session_id'), 'orders', ['session_id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_tracking_number'), 'orders', ['tracking_number'], unique=False)

    # 11. Order Items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('order_id', sa.String(length=64), nullable=False),
        sa.Column('product_id', sa.String(length=64), nullable=True),
        sa.Column('product_title', sa.String(length=512), nullable=False),
        sa.Column('sku', sa.String(length=64), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_items_id'), 'order_items', ['id'], unique=False)
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_items_product_id'), 'order_items', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('checkout_sessions')
    op.drop_table('cart_items')
    op.drop_table('carts')
    op.drop_table('shipping_options')
    op.drop_table('discounts')
    op.drop_table('prices')
    op.drop_table('inventory')
    op.drop_table('products')
    op.drop_table('merchants')
