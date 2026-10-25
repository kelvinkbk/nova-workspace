# NOVA Workspace

NOVA autonomous workspace source, tests, documentation, and ClubLedger Lite prototype.

The root index.html is a static Command Center preview. It uses demo defaults and does not connect to the local NOVA runtime or financial records.

Private environment files, local SQLite databases, receiving/payment configuration, virtual environments, caches, and generated ZIP packages are excluded.

Run tests with python -m pytest -q. Open finance/products/clubledger-lite/index.html to preview the offline finance tracker.

Never commit API keys, credentials, UPI/bank identifiers, live customer data, or local database files.
