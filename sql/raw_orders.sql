DROP TABLE IF EXISTS raw_orders;
CREATE TABLE raw_orders
    (
        order_id TEXT,
        customer_name TEXT,
        customer_email TEXT,
        product_name TEXT,
        category TEXT,
        quantity TEXT,
        unit_price TEXT,
        order_date TEXT,
        ship_country TEXT,
        status TEXT
    );




