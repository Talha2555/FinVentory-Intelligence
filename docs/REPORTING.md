# Reporting definitions and limits

- Revenue is `SUM(sales_items.quantity * price)`. All financial reporting uses line items, avoiding stale header totals.
- Cost of goods sold is `SUM(quantity * unit_cost)`. New sale inserts capture the product's cost at sale time unless an explicit historical unit cost is supplied. Unsold purchase inventory is not an expense in this calculation.
- Gross profit is revenue minus cost of goods sold; net profit also subtracts recorded operating expenses. Empty totals are zero. This is an all-time operational summary, not a full accounting ledger or tax report.
- Forecasts target the current month using the latest three **completed calendar months**: 50%, 30%, 20%, newest first. Missing months contribute zero, current-month sales are excluded, and products with no history forecast zero. Weights are not renormalized for new products.
- Supplier and retailer rankings use explicit party IDs in the transaction ledger. Product rankings use sale lines and group by product ID, so equal names stay separate.
- Inventory changes automatically after sale/purchase line inserts. The transaction ledger is populated through `record_sale_transaction` and `record_purchase_transaction` procedures; it is **not automatically populated by triggers**. Call the relevant procedure once within the same transaction as your business write. Historical ledger completeness and header/line consistency remain the responsibility of the importing system.
- Existing inventory triggers implement insert workflows. Editing or deleting posted line items does not reverse stock movements; use a separate audited correction workflow. This repair does not add full accounting, returns, or perpetual inventory valuation.
- Database connections are short-lived and always closed. Failed transactions roll back; the UI displays a generic error instead of displaying empty data as a successful request. Server logs contain SQLSTATE codes, not driver error messages or credentials.

## Worked example

The optional demo contains sale-line revenue of Rs. 1,591,000 and sale-time cost of goods sold of Rs. 1,407,000. Gross profit is Rs. 184,000; operating expenses of Rs. 180,000 leave **Rs. 4,000 net profit**. Purchase outlays of Rs. 3,500,000 are not deducted again as COGS.

For monthly unit sales of 20, 0 and 10 from oldest to newest completed month, next-month demand is `20 × 0.2 + 0 × 0.3 + 10 × 0.5 = 9` units. The missing middle month remains zero; the algorithm does not skip back to an older sale month.

## SQL view contracts

| View | Purpose / key output |
| --- | --- |
| `top_products` | Up to five products ranked by line-item revenue; product ID, name, units sold, revenue. |
| `top_suppliers` | Up to five suppliers ranked by recorded PURCHASE ledger amounts. |
| `top_retailers` | Up to five retailers ranked by recorded SALE ledger amounts. |
| `monthly_sales_view` | Calendar month and line-item revenue. The interface orders months chronologically. |
| `inventory_status_view` | Product name, stock quantity, reorder threshold and LOW/OK status. |
| `demand_prediction_view` | Product ID, name and weighted predicted unit sales. |
| `profit_loss_summary` | One row with revenue, COGS, gross profit, expenses and net profit; zero totals on an empty database. |
| `profit_summary` | Compatibility projection of revenue, cost and expenses. |
| `product_performance_view` | Legacy name-grouped performance view retained for compatibility; the dashboard uses ID-grouped `top_products`. |
