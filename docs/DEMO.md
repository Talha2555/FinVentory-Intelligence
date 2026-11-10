# Five-minute project walkthrough

Use a fresh local database with the optional sample data and a locally created Admin account. Complete [setup](SETUP.md) first. Keep passwords, account files and real business data out of a recording.

## Suggested sequence

1. **Explain the problem:** sales, stock and expenses are difficult to evaluate in isolation. FinVentory brings them into one reporting interface.
2. **Dashboard:** show product/party rankings and monthly revenue. Explain that product revenue comes from sale lines; supplier/retailer rankings use explicit ledger records.
3. **Inventory & Alerts:** inspect quantities and reorder thresholds. Run the system alert check twice to demonstrate that repeated scans do not duplicate an unread low-stock alert. The sample rent expense produces a high-expense alert.
4. **Demand Predictions:** explain the 50/30/20 calendar-month formula. A 20, 0, 10 sequence from oldest to newest gives 9 predicted units. The fixed demo is dated April 2026, so forecasts can correctly be zero outside its three-month window. Use the automated forecast test to demonstrate calendar gaps independently of today's date.
5. **Profit & Loss:** show revenue Rs. 1,591,000, COGS Rs. 1,407,000, expenses Rs. 180,000 and net profit **Rs. 4,000**. Explain why unsold purchases are not deducted again as COGS.
6. **Transactions and roles:** show the recorded ledger. Log in with a Staff account to demonstrate the three shared pages and the absence of Admin financial navigation.
7. **Engineering evidence:** open the test workflow and explain sale-cost snapshots, rollback/recovery, hashed credentials and the migration's historical-cost limitation.

## Evidence to include in a portfolio

Capture actual running pages after setup: the dashboard, inventory/alerts, profit summary and a successful CI run. Add captions identifying the sample data and test environment. Do not present mockups as implemented UI, claim a hosted deployment without a live URL, or claim forecast accuracy without backtesting.

For an interview, keep the GitHub repository, PR, architecture diagram and successful workflow available. If the repair PR remains open, link reviewers to its branch rather than implying the repaired code is already on `main`.
