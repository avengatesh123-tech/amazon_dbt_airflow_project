CREATE TABLE customers (
    customer_id BIGINT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    is_prime_member CHAR(1),
    created_timestamp TIMESTAMP,
    updated_timestamp TIMESTAMP,
    is_active CHAR(1)
);

CREATE TABLE sellers (
    seller_id BIGINT PRIMARY KEY,
    seller_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    seller_rating NUMERIC(3,2),
    created_timestamp TIMESTAMP,
    updated_timestamp TIMESTAMP,
    is_active CHAR(1)
);

CREATE TABLE categories (
    category_id BIGINT PRIMARY KEY,
    category_name VARCHAR(150),
    parent_category_id BIGINT,
    created_timestamp TIMESTAMP,
    updated_timestamp TIMESTAMP,
    is_active CHAR(1)
);

CREATE TABLE products (
    product_id BIGINT PRIMARY KEY,
    seller_id BIGINT,
    category_id BIGINT,
    product_name VARCHAR(255),
    brand VARCHAR(100),
    price NUMERIC(10,2),
    created_timestamp TIMESTAMP,
    updated_timestamp TIMESTAMP,
    is_active CHAR(1)
);

CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT,
    order_timestamp TIMESTAMP,
    payment_method VARCHAR(50),
    order_status VARCHAR(50),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    total_amount NUMERIC(12,2),
    created_timestamp TIMESTAMP,
    updated_timestamp TIMESTAMP,
    is_active CHAR(1)
);

CREATE TABLE order_items (
    order_item_id BIGINT PRIMARY KEY,
    order_id BIGINT,
    product_id BIGINT,
    seller_id BIGINT,
    quantity INT,
    unit_price NUMERIC(10,2),
    line_amount NUMERIC(12,2),
    created_timestamp TIMESTAMP,
    updated_timestamp TIMESTAMP,
    is_active CHAR(1)
);

CREATE TABLE reviews (
    review_id BIGINT PRIMARY KEY,
    product_id BIGINT,
    customer_id BIGINT,
    order_id BIGINT,
    rating INT,
    review_title VARCHAR(255),
    review_text VARCHAR(1000),
    review_timestamp TIMESTAMP,
    is_verified_purchase CHAR(1),
    created_timestamp TIMESTAMP,
    updated_timestamp TIMESTAMP,
    is_active CHAR(1)
);

-- Foreign keys

ALTER TABLE categories
    ADD CONSTRAINT fk_categories_parent FOREIGN KEY (parent_category_id) REFERENCES categories(category_id);

ALTER TABLE products
    ADD CONSTRAINT fk_products_seller FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
    ADD CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(category_id);

ALTER TABLE orders
    ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id);

ALTER TABLE order_items
    ADD CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(order_id),
    ADD CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    ADD CONSTRAINT fk_order_items_seller FOREIGN KEY (seller_id) REFERENCES sellers(seller_id);

ALTER TABLE reviews
    ADD CONSTRAINT fk_reviews_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    ADD CONSTRAINT fk_reviews_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    ADD CONSTRAINT fk_reviews_order FOREIGN KEY (order_id) REFERENCES orders(order_id);
