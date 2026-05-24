# Admin pricing, discounts, grants, and analytics

This Docker build includes a production-oriented admin control layer while keeping Stripe collection disabled until live keys are available.

## Admin access

- The first registered account becomes the initial admin.
- Normal users can log in to use their plan, but `/dashboard` returns a generic not-found style page unless the logged-in user has the `admin` role.
- There is no separate public admin login page; admins use the same login route, then open `/dashboard`.

## Pricing and limits

Admins can edit:

- Monthly and yearly plan prices
- Daily scan/clean limits
- Monthly file limits
- Batch file limits
- Per-file-type upload limits for images, PDFs, Office, ZIP, audio, video, and other files

The backend enforces these limits before every processing job starts.

## Promo banner

Admins can publish a top-bar discount campaign by setting:

- Discount percentage
- Duration in days
- Coupon code
- Banner copy
- Optional affiliate or campaign URL

The remaining days are computed dynamically from the campaign end date.

## Manual paid-plan access

Admins can create or update a user with a paid plan without Stripe. This is useful for beta users, clients, partners, refunds, and free-access campaigns.

## Coupons and affiliates

Admins can create stored coupon codes and affiliate/campaign links now. Stripe checkout redemption should be connected after Stripe keys and webhook secrets are configured.

## Analytics

The dashboard tracks:

- Page views for 7 and 30 days
- Traffic source and UTM source
- Approximate visitor location from proxy headers when available
- Average session time
- Top pages
- Top tool views for 7 and 30 days
- Tool processing job frequency and status

For production deployment behind Cloudflare/Vercel/Nginx, pass country headers such as `CF-IPCountry` or `X-Vercel-IP-Country` to improve location reporting.
