CREATE TABLE IF NOT EXISTS transformed_orders
    (
        order_id INT PRIMARY KEY,
        customer_name TEXT,
        customer_email TEXT,
        product_name TEXT,
        category TEXT,
        quantity INT,
        unit_price NUMERIC(10,2),
        order_date DATE,
        ship_country TEXT,
        delivery_status TEXT,
        loaded_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );


INSERT INTO transformed_orders
(
        order_id,
        customer_name,
        customer_email,
        product_name,
        category,
        quantity,
        unit_price,
        order_date,
        ship_country,
        delivery_status
)
SELECT 
TRIM(order_id):: INT,
NULLIF(TRIM(customer_name),''),
NULLIF(TRIM(customer_email),''),
NULLIF(TRIM(product_name),''),
NULLIF(TRIM(category),''),
NULLIF(TRIM(quantity),''):: INT,
NULLIF(TRIM(unit_price),''):: NUMERIC(10,2),
CASE
    WHEN TRIM(order_date) LIKE '____/__/__' THEN TO_DATE(TRIM(order_date),'YYYY/MM/DD')
    WHEN TRIM(order_date) LIKE '____-__-__' THEN TO_DATE(TRIM(order_date),'YYYY-MM-DD')
    WHEN TRIM(order_date) LIKE '__/__/____' THEN TO_DATE(TRIM(order_date),'DD/MM/YYYY')
    WHEN TRIM(order_date) LIKE '__-__-____' THEN TO_DATE(TRIM(order_date),'DD-MM-YYYY')
END AS order_date,
NULLIF(TRIM(ship_country),''),
NULLIF(TRIM(status),'')
FROM raw_orders
ON CONFLICT(order_id)
DO UPDATE SET
        delivery_status = EXCLUDED.delivery_status,
        updated_at = NOW();
    
