# Nexora Data Estate — Source Map

## Purpose

This document maps the 12 source systems described in `Nexora_Data_Architecture.pdf` (pages 1 and 4–17). It records each system's business function, key tables, primary keys, refresh style, and important known quirks.

**Important limitation:** The architecture reference describes the generated CSV data and relationships, but it does **not** specify ingestion schedules or whether each table is loaded by full refresh, incremental extraction, or CDC. Refresh styles are therefore marked **Not specified — confirm with source owner / pipeline design**. Do not treat this as evidence that a source supports incremental extraction.

## Source map

| Source system | Pretend source/tool | Owning function (inferred from system purpose) | Key tables and primary keys | Refresh style | Known quirks / caveats |
|---|---|---|---|---|---|
| CRM | Salesforce | Sales / customer relationship management | `accounts(account_id)`; `contacts(contact_id)`; `leads(lead_id)`; `opportunities(opportunity_id)`; `opportunity_history(history_id)` | Not specified — confirm | `accounts.account_owner_id`, `leads.assigned_to`, `opportunities.sales_rep_id`, and `opportunity_history.changed_by` reference HR `employees`; `leads.campaign_id` references Marketing `campaigns`; closed opportunities can skip stages in `opportunity_history`; some `opportunities.closed_at` values fall after 2026-09-30. |
| Marketing | HubSpot / Google Ads / Meta | Marketing | `campaigns(campaign_id)`; `campaign_spend(spend_id)`; `campaign_events(event_id)` | Not specified — confirm | Campaign budgets are USD while spend is in local currency; `campaign_events` is about 7M rows and is not globally sorted by date (sorting is only within each written chunk); `campaign_events.lead_id` is populated only for selected event types and is empty for anonymous events. |
| Sales activity | Sales engagement tool | Sales / sales operations | `sales_activities(activity_id)`; `quotes(quote_id)`; `quote_items(quote_item_id)` | Not specified — confirm | Quote revisions create new `quotes` rows; quote line totals add up to roughly, not exactly, the opportunity amount; quote items reference Product Management `products`. |
| ERP / Order management | ERP | Order management / sales operations | `sales_orders(order_id)`; `sales_order_items(order_item_id)`; `returns(return_id)` | Not specified — confirm | ERP order status can disagree with Logistics shipment status; line-item `unit_price` uses current list price, not historical price, and is not currency-converted; `returns` contains both `quantity` and `quantity.1` columns; SaaS-only orders do not have shipments or stock movements. |
| Product management | Product catalogue | Product management | `products(product_id)`; `product_price_history(price_history_id)` | Not specified — confirm | `product_price_history` prices are always USD; `effective_to` empty means current price; order prices use current list price rather than historical price. |
| Inventory / operations | Warehouse system | Warehouse / inventory operations | `warehouses(warehouse_id)`; `inventory_snapshot(snapshot_date + warehouse_id + product_id)`; `inventory_transactions(transaction_id)` | Not specified — confirm | `inventory_snapshot` has a composite primary key; transaction quantity is signed; `reference_id` is polymorphic and means different things depending on `transaction_type`; inventory starts with `OPENING_BALANCE` transactions dated 2021-12-31. |
| Procurement | Procurement system | Procurement / supply chain | `suppliers(supplier_id)`; `purchase_orders(po_id)`; `purchase_order_items(po_item_id)`; `goods_receipts(receipt_id)`; `goods_receipt_items(receipt_item_id)` | Not specified — confirm | Purchase orders use supplier currency; some deliveries are late, about 8% of lines are short-shipped, and some batches have high rejection rates; receipt item accepted quantity excludes rejected quantity. |
| Shipping / logistics | Carrier / TMS data | Logistics / fulfilment | `shipments(shipment_id)`; `shipment_events(event_id)` | Not specified — confirm | ERP and shipment statuses can disagree; `shipments` covers shipped hardware orders, not SaaS-only orders; shipment event data has a separate event-level grain. |
| Finance / accounting | Accounting ERP | Finance / accounting | `invoices(invoice_id)`; `invoice_items(invoice_item_id)`; `payments(payment_id)`; `expenses(expense_id)`; `budgets(budget_id)` | Not specified — confirm | Order/invoice/payment amounts carry currency labels but are not currency-converted; expense amounts are in local currency while budgets are USD; some `payments.payment_date` values fall after 2026-09-30; budgets and expenses have no direct FK and must be matched by department, category, and year-month after currency conversion. |
| HR | Workday | Human resources | `employees(employee_id)`; `departments(department_id)`; `employee_salary_history(salary_history_id)`; `attendance(attendance_id)`; `leave_requests(leave_id)`; `performance_reviews(review_id)` | Not specified — confirm | Every employee's `job_title` is the placeholder `Associate`; `employees.date_of_birth` is VARCHAR; some employees terminated before 2022; salary history uses effective dates; promotion flags should be compared with salary-history promotion changes. |
| Customer support | Helpdesk | Customer support | `support_tickets(ticket_id)`; `ticket_events(event_id)` | Not specified — confirm | Open tickets have no `resolution_time_hours`; customer rating is filled for only about 60% of closed tickets; `ticket_events.employee_id` is empty for customer-side events. |
| Subscriptions | Subscription billing | Subscription management / recurring revenue | `subscriptions(subscription_id)`; `subscription_events(event_id)` | Not specified — confirm | Current `subscriptions.quantity` reflects seats after upgrades/downgrades, not historical quantity; subscription lifecycle events are separate; subscription billing is not linked to invoices in the supplied model. |

## Cross-system join priorities

1. **Customer → order → product:** `accounts.account_id` → `sales_orders.account_id`; `sales_orders.order_id` → `sales_order_items.order_id`; `sales_order_items.product_id` → `products.product_id`.
2. **Order to cash:** `sales_orders.order_id` → `invoices.order_id` → `payments.invoice_id`.
3. **Hardware fulfilment:** `sales_orders` → `shipments` → `inventory_transactions` (sale transaction), then reconcile against `inventory_snapshot`. SaaS-only orders do not have shipments or stock movements.
4. **Marketing to pipeline:** `campaigns` → `campaign_spend` / `campaign_events`; `campaign_events.lead_id` → `leads.lead_id`; there is no direct lead-to-opportunity key.
5. **Procure to stock:** `purchase_orders` → `purchase_order_items`; `purchase_orders` → `goods_receipts` → `goods_receipt_items`; compare accepted/rejected quantities with purchase rows in `inventory_transactions`.
6. **Budget versus actual:** compare `budgets` and `expenses` by department, category, and year-month after converting expenses to USD.
7. **Support and churn:** compare `support_tickets` with account and subscription status; treat the stated relationship as a hypothesis to test, not proof of causation.

## Open questions before production ingestion

- What is the authoritative refresh mechanism and cadence for each source/table?
- Which sources expose reliable `updated_at`, CDC, deletion markers, or source snapshots?
- What are the required late-arrival and reprocessing windows?
- What exchange-rate policy should be used for cross-currency reporting? The reference describes fixed rates for some source data but does not define a reporting policy for every measure.
- How should order status disagreements be resolved between ERP and Logistics?
- Should `returns.quantity` or `returns.quantity.1` be treated as authoritative? Confirm against the generated CSV/schema before modeling.
- What business rule should link a Closed Won opportunity to a sales order when no key exists?
