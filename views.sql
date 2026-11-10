-- Canonical reporting definitions, used by both fresh install and migration.
CREATE OR REPLACE VIEW monthly_sales_view AS
SELECT date_trunc('month', s.sale_date) AS month,
       SUM(si.quantity * si.price) AS revenue
FROM sales s JOIN sales_items si USING (sale_id)
GROUP BY 1;

CREATE OR REPLACE VIEW top_products AS
SELECT p.product_id, p.name, SUM(si.quantity) AS total_sold,
       SUM(si.quantity * si.price) AS revenue
FROM products p JOIN sales_items si USING (product_id)
GROUP BY p.product_id, p.name
ORDER BY revenue DESC, p.product_id LIMIT 5;

-- Supplier/retailer rankings use the explicit transaction party IDs.
CREATE OR REPLACE VIEW top_suppliers AS
SELECT s.supplier_id, s.name, SUM(t.amount) AS total_purchases
FROM suppliers s JOIN transactions t USING (supplier_id)
WHERE t.transaction_type = 'PURCHASE'
GROUP BY s.supplier_id, s.name
ORDER BY total_purchases DESC, s.supplier_id LIMIT 5;

CREATE OR REPLACE VIEW top_retailers AS
SELECT r.retailer_id, r.name, SUM(t.amount) AS total_sales
FROM retailers r JOIN transactions t USING (retailer_id)
WHERE t.transaction_type = 'SALE'
GROUP BY r.retailer_id, r.name
ORDER BY total_sales DESC, r.retailer_id LIMIT 5;

CREATE OR REPLACE VIEW profit_loss_summary AS
WITH amounts AS (
    SELECT COALESCE(SUM(quantity * price), 0) AS total_revenue,
           COALESCE(SUM(quantity * unit_cost), 0) AS total_cost
    FROM sales_items
), spending AS (
    SELECT COALESCE(SUM(amount), 0) AS total_expenses FROM expenses
)
SELECT total_revenue, total_cost, total_revenue - total_cost AS gross_profit,
       total_expenses, total_revenue - total_cost - total_expenses AS net_profit
FROM amounts CROSS JOIN spending;

CREATE OR REPLACE VIEW profit_summary AS
SELECT total_revenue, total_cost, total_expenses FROM profit_loss_summary;

-- Forecast the current month using the three completed calendar months.
-- Missing months have zero demand; incomplete current-month sales are excluded.
CREATE OR REPLACE VIEW demand_prediction_view AS
WITH months AS (
    SELECT date_trunc('month', CURRENT_DATE) - n * INTERVAL '1 month' AS month,
           CASE n WHEN 1 THEN 0.5 WHEN 2 THEN 0.3 ELSE 0.2 END AS weight
    FROM generate_series(1, 3) AS n
), monthly_units AS (
    SELECT si.product_id, date_trunc('month', s.sale_date) AS month,
           SUM(si.quantity) AS units
    FROM sales_items si JOIN sales s USING (sale_id)
    WHERE s.sale_date >= date_trunc('month', CURRENT_DATE) - INTERVAL '3 months'
      AND s.sale_date < date_trunc('month', CURRENT_DATE)
    GROUP BY si.product_id, date_trunc('month', s.sale_date)
)
SELECT p.product_id, p.name,
       ROUND(SUM(COALESCE(u.units, 0) * m.weight), 2) AS predicted_sales
FROM products p CROSS JOIN months m
LEFT JOIN monthly_units u ON u.product_id = p.product_id AND u.month = m.month
GROUP BY p.product_id, p.name;
