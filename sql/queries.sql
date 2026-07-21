-- ============================================================
-- queries.sql
-- SQL analysis queries for the UPI Spend Insights project
-- Database: upi_spend_insights (MySQL)
-- ============================================================

USE upi_spend_insights;

-- ------------------------------------------------------------
-- 1. Basic exploration: view sample transactions
-- ------------------------------------------------------------
SELECT * FROM transactions LIMIT 10;

-- ------------------------------------------------------------
-- 2. Filter: only debit (spending) transactions
-- ------------------------------------------------------------
SELECT * FROM transactions WHERE type = 'Debit' LIMIT 10;

-- ------------------------------------------------------------
-- 3. Aggregation: total spend by category, highest first
-- ------------------------------------------------------------
SELECT category, SUM(amount) AS total_spent
FROM transactions
WHERE type = 'Debit'
GROUP BY category
ORDER BY total_spent DESC;

-- ------------------------------------------------------------
-- 4. Reference table: monthly budget per category
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS category_budget (
    category VARCHAR(50) PRIMARY KEY,
    monthly_budget DECIMAL(10,2)
);

INSERT INTO category_budget (category, monthly_budget) VALUES
('Person/Merchant Payment', 60000),
('Education/Fees', 15000),
('UPI Lite Top-up', 3000),
('Food & Dining', 2000),
('Recharge', 500),
('Shopping', 2000),
('Transport', 1000),
('Others', 1000)
ON DUPLICATE KEY UPDATE monthly_budget = VALUES(monthly_budget);

-- ------------------------------------------------------------
-- 5. JOIN: compare actual spend vs budget (19-month period)
-- ------------------------------------------------------------
SELECT
    t.category,
    SUM(t.amount) AS total_spent,
    b.monthly_budget * 19 AS total_budget_19_months,
    SUM(t.amount) - (b.monthly_budget * 19) AS difference
FROM transactions t
JOIN category_budget b ON t.category = b.category
WHERE t.type = 'Debit'
GROUP BY t.category, b.monthly_budget
ORDER BY difference DESC;

-- ------------------------------------------------------------
-- 6. Window function: running (cumulative) total of spend by month
-- ------------------------------------------------------------
SELECT
    month,
    SUM(amount) AS monthly_spend,
    SUM(SUM(amount)) OVER (ORDER BY month) AS running_total
FROM transactions
WHERE type = 'Debit'
GROUP BY month
ORDER BY month;

-- ------------------------------------------------------------
-- 7. Window function: rank months by spend (highest first)
-- ------------------------------------------------------------
SELECT
    month,
    SUM(amount) AS monthly_spend,
    RANK() OVER (ORDER BY SUM(amount) DESC) AS spend_rank
FROM transactions
WHERE type = 'Debit'
GROUP BY month
ORDER BY spend_rank;