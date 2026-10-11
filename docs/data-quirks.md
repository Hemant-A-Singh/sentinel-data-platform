# Five Highest-Priority Data Quirks

Source: `Data_Architecture.pdf`, section **5. Known data quirks** (page 20), plus table notes elsewhere in the architecture reference.

These five were selected because they can silently distort financial reporting, inventory, pipeline analytics, or historical interpretation.

## 1. Currency labels do not guarantee normalized amounts

**Evidence:** The reference says currencies are not converted for order, invoice, quote, and subscription amounts; these carry a currency label but are priced from a USD list. Campaign spend, procurement, and expenses use fixed-rate conversions, while budgets are USD. (Page 20; also pages 6, 8–9, 11, and 13–14.)

**Why it matters:** Summing values across INR, USD, GBP, SGD, or supplier currencies can produce meaningless revenue, spend, margin, or budget-variance figures. A currency column alone does not make values comparable.

**Mitigation / tests:**
- Preserve each source amount and source currency.
- Define a documented reporting-currency conversion policy and effective-date/rate rules before aggregating.
- Add tests that prevent cross-currency aggregation before normalization.
- Reconcile converted totals against the chosen exchange-rate policy; do not assume all source fixed rates are suitable for reporting.

## 2. Order price uses current price, not historical price

**Evidence:** `sales_order_items.unit_price` is described as current list price, not historical and not currency-converted; the known-quirks section repeats that order prices use current list price instead of `product_price_history`. (Pages 9 and 20.)

**Why it matters:** Historical revenue, discounts, margin, or price-change analysis can be wrong if the stored order-line unit price is treated as the price valid on the order date. The price-history table cannot automatically correct this without a business rule.

**Mitigation / tests:**
- Treat the order-line amount as the supplied transaction value, while flagging that its unit price is not historically reliable.
- Compare `sales_order_items.unit_price` with the price-history record effective on `order_date`.
- Quantify mismatches and obtain a business decision on whether to restate historical prices or preserve source transaction amounts.

## 3. ERP and logistics can disagree on shipment status

**Evidence:** The reference states that ERP may show an order as `Shipped` while its shipment record shows `Delivered`. (Page 20; shipment/order relationships on pages 8 and 12.)

**Why it matters:** Operational dashboards can disagree on delivery performance, open orders, customer promises, and revenue/fulfilment timing. Choosing one status silently can conceal the mismatch.

**Mitigation / tests:**
- Keep source-specific statuses and avoid overwriting one with the other during ingestion.
- Build a reconciliation table keyed by `order_id` and shipment ID.
- Define an agreed status precedence or canonical fulfilment rule with Operations.
- Add a test/report for conflicting statuses and quantify affected orders.

## 4. Records can extend beyond the stated data period

**Evidence:** The dataset covers 2022–2026, but some `opportunities.closed_at` and `payments.payment_date` values fall after 30 September 2026. (Page 20; specific column notes on pages 6 and 13.)

**Why it matters:** A pipeline that assumes 30 September 2026 is a hard maximum can drop valid generated records or produce inconsistent period totals. A pipeline that accepts every date without explanation can also confuse consumers about the intended reporting window.

**Mitigation / tests:**
- Distinguish the dataset's intended reporting cutoff from the maximum observed event date.
- Profile dates by table and create a test/report for records after 2026-09-30.
- Do not silently discard later rows; agree whether to include, quarantine, or flag them for each use case.

## 5. Procurement receipts can differ from ordered quantities

**Evidence:** The reference states suppliers are late on average, about 8% of lines are short-shipped, and some batches have high rejection rates. `goods_receipt_items.quantity_received` excludes rejected quantity. (Pages 11–12 and 20.)

**Why it matters:** Comparing ordered quantities directly to accepted receipts can make stock-in, supplier performance, expected inventory, and procurement cost reporting inaccurate. Rejected units are not the same as accepted inventory.

**Mitigation / tests:**
- Compare ordered, received/accepted, and rejected quantities at purchase-order-item/product grain.
- Separate late delivery, short shipment, and rejection metrics.
- Reconcile receipt items to purchase-related inventory transactions.
- Define whether open or partially received purchase orders count as outstanding supply.

## Additional quirks to track

- `campaign_events` is sorted by date only within each written chunk, not across the whole file (page 20). Do not assume file order is chronological; explicitly sort by event date and use a stable tie-breaker if needed.
- Closed opportunities can skip stages in `opportunity_history` (page 20). Do not assume every deal follows every stage.
- Employee `job_title` is always `Associate`; `accounts.state` and `warehouses.state` contain the literal text `NA`; `departments.parent_department_id` is empty; some employees were terminated before 2022 (page 20).
- `inventory_transactions.quantity` is signed, and the opening balance uses `OPENING_BALANCE` dated 2021-12-31 (page 10 and page 20).
- Quote line totals add up to roughly, not exactly, the opportunity amount (page 20).
- The `returns` table includes both `quantity` and `quantity.1` in the reference schema (page 9); investigate the source CSV and generator before deciding whether this is a duplicate/renamed column.
