# Sentinel Cross-System ERD — First Joins

This ERD prioritizes the requested **customer, product, and order** path and includes the main surrounding entities needed to validate order-to-cash and fulfilment. Table and key names come from the architecture reference (especially pages 8–10, 13, 18–20).

```mermaid EREDiagram
    ACCOUNTS ||--o{ SALES_ORDERS : places
    SALES_ORDERS ||--|{ SALES_ORDER_ITEMS : contains
    PRODUCTS ||--o{ SALES_ORDER_ITEMS : appears_in

    SALES_ORDERS ||--o| INVOICES : invoiced_by
    INVOICES ||--o{ PAYMENTS : paid_by
    INVOICES ||--|{ INVOICE_ITEMS : contains
    PRODUCTS ||--o{ INVOICE_ITEMS : appears_in

    SALES_ORDERS ||--o{ SHIPMENTS : fulfilled_by
    SHIPMENTS ||--o{ SHIPMENT_EVENTS : tracked_by
    WAREHOUSES ||--o{ SHIPMENTS : ships_from
    WAREHOUSES ||--o{ INVENTORY_TRANSACTIONS : records
    PRODUCTS ||--o{ INVENTORY_TRANSACTIONS : moves
    WAREHOUSES ||--o{ INVENTORY_SNAPSHOT : has_balance
    PRODUCTS ||--o{ INVENTORY_SNAPSHOT : stock_of

    ACCOUNTS ||--o{ CONTACTS : has
    ACCOUNTS ||--o{ SUPPORT_TICKETS : raises
    CONTACTS ||--o{ SUPPORT_TICKETS : submits
    ACCOUNTS ||--o{ SUBSCRIPTIONS : holds
    PRODUCTS ||--o{ SUBSCRIPTIONS : subscribes_to

    ACCOUNTS {
        int account_id PK
        string account_name
        string account_type
        string country
        string status
    }

    SALES_ORDERS {
        int order_id PK
        int account_id FK
        int warehouse_id FK
        date order_date
        string currency
        string order_status
        decimal order_total
    }

    SALES_ORDER_ITEMS {
        int order_item_id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
        decimal line_total
    }

    PRODUCTS {
        int product_id PK
        string sku
        string product_name
        string product_type
        decimal list_price
    }

    INVOICES {
        int invoice_id PK
        int account_id FK
        int order_id FK
        date invoice_date
        string currency
        decimal total_amount
    }

    INVOICE_ITEMS {
        int invoice_item_id PK
        int invoice_id FK
        int product_id FK
        decimal line_amount
    }

    PAYMENTS {
        int payment_id PK
        int invoice_id FK
        int account_id FK
        date payment_date
        decimal amount
        string currency
    }

    SHIPMENTS {
        int shipment_id PK
        int order_id FK
        int warehouse_id FK
        string status
        date ship_date
        date actual_delivery_date
    }

    SHIPMENT_EVENTS {
        int event_id PK
        int shipment_id FK
        timestamp event_datetime
        string event_type
    }

    WAREHOUSES {
        int warehouse_id PK
        string warehouse_name
        string country
    }

    INVENTORY_TRANSACTIONS {
        int transaction_id PK
        timestamp transaction_datetime
        int warehouse_id FK
        int product_id FK
        string transaction_type
        int quantity
        string reference_id
    }

    INVENTORY_SNAPSHOT {
        date snapshot_date PK
        int warehouse_id PK, FK
        int product_id PK, FK
        int quantity_on_hand
        int quantity_available
    }

    CONTACTS {
        int contact_id PK
        int account_id FK
        string email
    }

    SUPPORT_TICKETS {
        int ticket_id PK
        int account_id FK
        int contact_id FK
        string status
        decimal resolution_time_hours
    }

    SUBSCRIPTIONS {
        int subscription_id PK
        int account_id FK
        int product_id FK
        string status
        int quantity
        decimal unit_price
    }
```

## Join definitions and cautions

| Join | Join condition | Main risk / validation |
|---|---|---|
| Customer to orders | `accounts.account_id = sales_orders.account_id` | Validate that every order maps to an account. |
| Orders to order lines | `sales_orders.order_id = sales_order_items.order_id` | One-to-many: aggregate line metrics before joining to other one-to-many facts. |
| Order lines to products | `sales_order_items.product_id = products.product_id` | Product price is current list price, not historical price; order currency is not converted. |
| Orders to invoices | `sales_orders.order_id = invoices.order_id` | One invoice per non-cancelled order is described; test exceptions and amount reconciliation. |
| Invoices to payments | `invoices.invoice_id = payments.invoice_id` | Multiple payments can exist; compare sum of payments with invoice total and status. |
| Orders to shipments | `sales_orders.order_id = shipments.order_id` | Shipment data is for hardware orders; SaaS-only orders may have no shipment. Statuses may disagree. |
| Products / warehouses to inventory | Join by `product_id` and `warehouse_id` | `inventory_snapshot` grain is the composite key `(snapshot_date, warehouse_id, product_id)`. Transactions use signed quantities. |
| Account to subscription | `accounts.account_id = subscriptions.account_id` | Subscription quantity is current state; subscription events are required for lifecycle history. |

## Relationships that are not direct foreign-key joins

The architecture reference explicitly identifies these gaps:

- **Closed Won opportunity → sales order:** no direct key; match on account and date only as a provisional business rule and validate ambiguity.
- **Lead → opportunity:** no direct key connecting a lead to the deal it became.
- **Subscription → invoice:** subscription billing is not linked to invoices in this data model.
- **Inventory transaction → business reference:** `reference_id` is polymorphic and must be interpreted using `transaction_type`; internal transfer/adjustment/damage codes are not order IDs.
- **Budgets → expenses:** match on department, category, and year-month; convert expenses to USD before comparison.

## Recommended first implementation

1. Build and test dimensions for accounts/customers and products.
2. Model order headers and order lines separately, preserving their grains.
3. Add invoice headers, invoice lines, and payments as separate facts for order-to-cash reconciliation.
4. Add shipments and inventory only after distinguishing hardware from SaaS products and documenting status mismatches.
5. Add referential-integrity tests for every declared FK and reconciliation tests for amounts and quantities.
