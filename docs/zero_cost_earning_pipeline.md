# NOVA zero-cost earning pipeline

**Mission:** Reach the first ₹100 in verified legitimate revenue without owner-funded spending. Revenue is a goal, not a guarantee.

## Current status (25 October 2026)

- Existing runtime foundation: persistent memory, local model provider, research/evidence evaluation, sandbox prototype building, and approval/safety modules.
- Baseline before finance changes: 323 tests passed.
- New evidence-based finance ledger added in `finance/ledger.py`; the autonomous runtime can read a finance summary but cannot write transactions through its action list.
- New read-only `finance_status` action is registered in the runtime and security policy.
- Full test suite after changes: 328 passed.
- First digital-product prototype created at `finance/products/clubledger-lite/`.
- No customer, order, payout, or revenue has been verified. Product is not published.

## Initial experiment: ClubLedger Lite

A standalone offline-first browser app for student clubs and small committees to record income and expenses, filter transactions, and export CSV/JSON backups. It requires no paid hosting, external library, or backend. It is a plausible first experiment because the product can be delivered as a static file and its scope is small enough to test quickly; this is a hypothesis, not proof of demand.

### Experiment gates

1. **Functional QA:** Verify transaction totals, monthly summaries, search/filter, CSV export, JSON backup/restore, and deletion behavior using dummy data in multiple browsers.
2. **Offer QA:** Review the listing copy, price, screenshots if needed, support expectations, and product limitations. Proposed test price: ₹49; not validated.
3. **Channel check:** Confirm platform eligibility, accepted file type, Indian payout/KYC requirements, fees, and payout timing using current official terms. Select a platform with ₹0 upfront cost and no paid subscription. Initial official-source check: [Instamojo pricing](https://www.instamojo.com/pricing) lists a ₹0/year Lite plan and a 10% + ₹3 digital-product fee, while some Instamojo help articles show different rates; verify the fee in the live seller dashboard before publishing. [Topmate](https://topmate.io/) lists no monthly fee, 10% on own-link sales or 20% marketplace sales, plus gateway charges and GST on its fee; its first withdrawal opens 7 days after the first paid sale. No seller platform has been selected or connected.
4. **Human approval before publication:** No account creation, payout setup, public posting, or customer messaging should happen without owner review/authorization. Do not publish private or identifying data.
5. **Demand test:** Share the offer only through a small, relevant, permitted channel. Record visits, genuine enquiries, orders, refunds, and payout evidence. Do not spam or fabricate testimonials.
6. **Verified revenue:** Record income only after confirming the actual completed payment or payout and storing an evidence reference. Pending orders, hypothetical earnings, and test transactions do not count.
7. **Decision:** Improve based on real feedback, continue if there is evidence of demand, or stop and test a different zero-cost opportunity. Do not buy ads or subscriptions.

## Finance ledger rules

- Currency stored as integer paise to avoid floating-point accounting errors.
- Only `verified` entries count in revenue/expense totals; verified entries require an evidence reference.
- Owner funding is tracked separately and never counted as earned revenue.
- The autonomous runtime has read-only finance access. It cannot create, verify, transfer, or withdraw money.
- Ledger entries are local records, not bank reconciliation; evidence must be checked by a trusted human.

## Remaining work

- Complete browser-level QA and accessibility checks for ClubLedger Lite.
- Package the product and review the listing draft.
- Check official seller-platform terms and choose a zero-upfront channel.
- Obtain owner approval before public release or customer contact.
- Add real-world outcome tracking for discovery, product delivery, conversion, payout and refunds.
- Verify bounded runtime operation and recovery before enabling any unattended cycles.
