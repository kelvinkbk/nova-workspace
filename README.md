# NOVA Command Center — Static Preview

A static dashboard preview for the NOVA autonomous workspace. It intentionally uses demo/default values and does not connect to the local laptop runtime, finance database, or UPI details.

## Preview locally
Open `index.html` in a browser.

## Deploy with GitHub Pages
In the repository, open **Settings → Pages** and set the build/deployment source to **GitHub Actions**. The included workflow publishes the root `index.html` on pushes to `main`.

## Safety
- No credentials, `.env` files, local databases, or payment identifiers belong in this repository.
- This is a public static UI only. Do not expose the local agent or finance backend without a separate authenticated, security-reviewed API.
- Revenue shown is demo/default data, not live financial information.
