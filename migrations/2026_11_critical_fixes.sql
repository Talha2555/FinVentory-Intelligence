-- Apply once to the original schema, in the connected target database.
-- Backfilled historical COGS uses today's product cost: audit before production use.
BEGIN;
ALTER TABLE sales_items ADD COLUMN IF NOT EXISTS unit_cost NUMERIC(10,2);
UPDATE sales_items si SET unit_cost = p.cost_price
FROM products p WHERE p.product_id = si.product_id AND si.unit_cost IS NULL;
ALTER TABLE sales_items ALTER COLUMN unit_cost SET NOT NULL;

CREATE OR REPLACE FUNCTION prevent_negative_stock()
RETURNS TRIGGER AS $$
DECLARE current_qty INT;
BEGIN
    SELECT quantity INTO current_qty FROM inventory
    WHERE product_id = NEW.product_id FOR UPDATE;
    IF current_qty IS NULL OR current_qty < NEW.quantity THEN
        RAISE EXCEPTION 'Not enough stock!';
    END IF;
    IF NEW.unit_cost IS NULL THEN
        SELECT cost_price INTO NEW.unit_cost FROM products WHERE product_id = NEW.product_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_low_stock()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.quantity < NEW.reorder_level AND NOT EXISTS (
        SELECT 1 FROM alerts WHERE alert_type = 'LOW_STOCK' AND status = 'UNREAD'
        AND message = 'Low stock for product ID: ' || NEW.product_id
    ) THEN
        INSERT INTO alerts (message, alert_type)
        VALUES ('Low stock for product ID: ' || NEW.product_id, 'LOW_STOCK');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
\ir ../views.sql
COMMIT;
