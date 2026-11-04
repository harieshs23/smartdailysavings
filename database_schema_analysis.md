# Database Schema Analysis

## Schema Overview

The application uses a **PostgreSQL database** (Neon-backed) with two main schemas:

### `neon_auth` Schema (Authentication & Authorization)
- **9 tables**: account, invitation, jwks, member, organization, project_config, session, user, verification
- **21 indexes** covering primary keys, foreign keys, and unique constraints

### `public` Schema (Application Data)
- **13 tables**: alembic_version, categories, comments, deal_alerts, deal_clicks, deals, playing_with_neon, stores, users, votes, waitlist
- **24 indexes** including primary keys, unique constraints, and application-specific indexes

---

## Waitlist Table (`public` schema)

### Current Schema
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `email` | TEXT | NOT NULL, UNIQUE |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP |

### Indexes
- `waitlist_pkey` - Primary key constraint on `id`
- `waitlist_email_key` - Unique constraint on `email`

### Historical Context
- **Original schema** (migration `877fb6d9d9bd`): Had only `id`, `email`, `created_at` columns
- **Added** (migration `e95e4baded10`): Added `notification_timestamp` column on 2026-10-27
- **Removed** (current task): `notification_timestamp` column removed, reverting to original schema

### Changes Made
1. **Model** (`backend/app/models.py`): Removed `notification_timestamp` field from `Waitlist` SQLAlchemy model
2. **Endpoint** (`backend/app/main.py`): Updated `join_waitlist` to no longer set `notification_timestamp`
3. **Migration** (`e95e4baded10`): Converted to no-op (upgrade/downgrade do nothing)

---

## Other Key Tables in `public` Schema

### `users` table
- Columns: id (UUID), email, username, password_hash, avatar_url, role, reputation_score, created_at, updated_at
- Indexes: `users_pkey`, `users_email_key`, `users_username_key`

### `deals` table
- Columns: id (UUID), user_id, store_id, category_id, title, slug, description, original_price, sale_price, coupon_code, direct_url, image_url, status, score, views_count, clicks_count, is_free_shipping, expires_at, created_at, updated_at
- Indexes: `deals_pkey`, `deals_slug_key`, `idx_deals_status_score`, `idx_deals_category`, `idx_deals_store`, `stores_pkey`, `stores_name_key`, `stores_slug_key`

### `categories` table
- Columns: id (UUID), name, slug, parent_id
- Indexes: `categories_pkey`, `categories_name_key`, `categories_slug_key`

### `stores` table
- Columns: id (UUID), name, slug, domain, affiliate_network, affiliate_template_url, logo_url, created_at
- Indexes: `stores_pkey`, `stores_name_key`, `stores_slug_key`

### `votes` table
- Columns: id (UUID), user_id, deal_id, value (-1 or 1), created_at
- Indexes: `votes_pkey`, `votes_user_id_deal_id_key`
- Unique constraint: `(user_id, deal_id)`

### `comments` table
- Columns: id (UUID), deal_id, user_id, parent_id, body, created_at, updated_at
- Indexes: `comments_pkey`, `idx_comments_deal`

### `deal_alerts` table
- Columns: id (UUID), user_id, keyword, store_id, max_price, min_score, is_active, created_at

### `deal_clicks` table
- Columns: id (UUID), deal_id, user_id, ip_address, user_agent, created_at

### `alembic_version` table
- Single row tracking current Alembic migration version

---

## `neon_auth` Schema Tables

### `users` table
- Columns: id (UUID PK), email (VARCHAR 255 UNIQUE), username (VARCHAR 50 UNIQUE), password_hash, avatar_url, role (user_role ENUM), reputation_score, created_at, updated_at

### `organization` table
- Columns: id (UUID PK), name (VARCHAR 100 UNIQUE), slug (VARCHAR 100 UNIQUE), domain (VARCHAR 255), affiliate_network, affiliate_template_url, logo_url, created_at

### `project_config` table
- Columns: id (UUID PK), endpoint_id (KEY), created_at

### `session` table
- Columns: id (UUID PK), user_id, token_key, user_id index, created_at

### `invitation` table
- Columns: id (UUID PK), email, organization_id index, pkey, email index, organization_id index

### `member` table
- Columns: id (UUID PK), organization_id index, user_id index, pkey, organization_id index, user_id index

### `account` table
- Columns: id (UUID PK), user_id, provider_type, provider_id, access_token, refresh_token, id_token, password, last_login, created_at

### `verification` table
- Columns: id (UUID PK), identifier, identifier_idx, pkey

### `jwks` table
- Columns: id (UUID PK), kid, kty, use, alg, n, exp

---

## Migration History

| Revision | Description |
|----------|-------------|
| `877fb6d9d9bd` | Initial schema creation |
| `1b97abd` | Add notification_timestamp to waitlist table (later reverted) |
| `e95e4baded10` | Add notification_timestamp column (now no-op) |
| `1ce5d54` | Configure Neon-backed backend |

---

## Summary of Changes

**Removed column:** `notification_timestamp` from `waitlist` table
- Reverted to original 3-column schema: `id`, `email`, `created_at`
- All references removed from models, endpoints, and migrations
- Test suite passes (1/1 tests passing)