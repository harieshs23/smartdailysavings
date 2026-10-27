Here is the complete **PostgreSQL Relational Database Schema** designed to support this architecture, followed by the essential **RESTful API endpoints**.

---

### Part 1: PostgreSQL Database Schema (`schema.sql`)

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. USERS & PROFILES
CREATE TYPE user_role AS ENUM ('user', 'moderator', 'admin');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    role user_role DEFAULT 'user',
    reputation_score INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. STORES / MERCHANTS
CREATE TABLE stores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    domain VARCHAR(255) NOT NULL,
    affiliate_network VARCHAR(50),      -- e.g. 'impact', 'cj', 'skimlinks'
    affiliate_template_url TEXT,       -- e.g. 'https://click.affiliate.com/?url={CLEAN_URL}&aff_id=123'
    logo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. CATEGORIES
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL
);

-- 4. DEALS
CREATE TYPE deal_status AS ENUM ('new', 'popular', 'frontpage', 'expired', 'removed');

CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE RESTRICT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    original_price DECIMAL(10, 2),
    sale_price DECIMAL(10, 2) NOT NULL,
    coupon_code VARCHAR(50),
    direct_url TEXT NOT NULL,           -- Cleaned original URL (no referral tags)
    image_url TEXT,
    status deal_status DEFAULT 'new',
    score INT DEFAULT 0,                -- Net vote score (upvotes - downvotes)
    views_count INT DEFAULT 0,
    clicks_count INT DEFAULT 0,
    is_free_shipping BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_deals_status_score ON deals (status, score DESC);
CREATE INDEX idx_deals_store ON deals (store_id);
CREATE INDEX idx_deals_category ON deals (category_id);

-- 5. VOTES
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    value SMALLINT NOT NULL CHECK (value IN (-1, 1)),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, deal_id)          -- Restricts to 1 vote per user per deal
);

-- 6. THREADED COMMENTS
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE, -- For nested replies
    body TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_comments_deal ON comments (deal_id);

-- 7. DEAL ALERTS
CREATE TABLE deal_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword VARCHAR(100),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    max_price DECIMAL(10, 2),
    min_score INT DEFAULT 5,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. OUTBOUND CLICK TRACKING (ANALYTICS)
CREATE TABLE deal_clicks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,     -- Optional (guest or registered)
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

```

---

### Part 2: Core RESTful API Specification

#### 1. Deal Management

* **`GET /api/v1/deals`**
* **Query Params:** `status=frontpage|popular|new`, `store_id`, `category_id`, `sort=hot|newest|price_asc`, `page`, `limit`
* **Description:** Retrieves paginated feeds of deals.


* **`POST /api/v1/deals`**
* **Auth:** Required (JWT)
* **Body:** `{ title, description, original_price, sale_price, coupon_code, direct_url, store_id, category_id, image_url }`
* **Description:** Submits a new deal into the community queue.


* **`GET /api/v1/deals/:slug`**
* **Description:** Gets complete deal metadata, merchant details, and vote score.


* **`POST /api/v1/deals/parse-url`**
* **Auth:** Required
* **Body:** `{ url: string }`
* **Description:** Pre-fills the submission form by scraping OpenGraph tags (title, image, price) from the merchant URL.



#### 2. Voting & Community

* **`POST /api/v1/deals/:id/vote`**
* **Auth:** Required
* **Body:** `{ value: 1 | -1 }`
* **Description:** Casts or modifies a vote. Updates the aggregate score on the `deals` table atomically.


* **`DELETE /api/v1/deals/:id/vote`**
* **Auth:** Required
* **Description:** Removes the current user's vote.


* **`GET /api/v1/deals/:id/comments`**
* **Description:** Returns the nested discussion tree for the deal.


* **`POST /api/v1/deals/:id/comments`**
* **Auth:** Required
* **Body:** `{ body: string, parent_id?: string }`
* **Description:** Posts a top-level comment or a reply to an existing comment.



#### 3. Monetization & Redirects

* **`GET /r/:deal_id`**
* **Description:** Ultra-fast redirect handler.
* **Workflow:**
1. Logs click event in `deal_clicks` (asynchronously via Redis/Queue).
2. Retrieves the clean `direct_url` and the merchant's `affiliate_template_url`.
3. Builds the affiliate link and issues an **HTTP 302** redirect to the vendor.





#### 4. Deal Alerts

* **`GET /api/v1/alerts`**
* **Auth:** Required
* **Description:** Lists user's active keyword and price watch triggers.


* **`POST /api/v1/alerts`**
* **Auth:** Required
* **Body:** `{ keyword: string, max_price?: number, min_score?: number, store_id?: string }`
* **Description:** Creates a new deal alert trigger.



---