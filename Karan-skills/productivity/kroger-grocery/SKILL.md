---
name: kroger-grocery
description: Use when working with Kroger Developer APIs for grocery search, OAuth, Locations/Products, and add-to-cart testing for pickup. Includes safe OAuth callback workflow, credential environment rules, and cleanup limitations.
tags: [kroger, grocery, oauth, cart, api, pickup]
---

# Kroger Grocery API Workflow

Use this skill when testing or building against Kroger Developer APIs: Products, Locations, Profile/Identity, and Cart add-to-cart.

## Critical Safety Rules

- Never print `client_secret`, access tokens, refresh tokens, auth codes, Kroger passwords, or personal account data.
- Do not ask the user to paste their Kroger password. Use the OAuth browser flow.
- Adding to a personal grocery cart is an account mutation. Get explicit user approval for the exact items and quantities before calling `/cart/add`.
- Kroger Public Cart API is add-only. Do not promise programmatic removal unless using a Partner Cart API with delete/update access or the user has authorized website/UI cleanup.
- Avoid storing product/cart-derived data beyond the active session. Kroger acceptable-use rules prohibit tracking/sharing/storing customer cart-derived data.

## Environments

Kroger app credentials are environment-specific.

- Production base: `https://api.kroger.com/v1`
- Production OAuth base: `https://api.kroger.com/v1/connect/oauth2`
- Certification base: `https://api-ce.kroger.com/v1`
- Certification OAuth base: `https://api-ce.kroger.com/v1/connect/oauth2`

If production token returns `401 unauthorized invalid credentials` while certification works, the app is probably Certification-only. If certification returns `401` while production works, the app is Production-only.

## Local Credential File Convention

For Karan's grocery-shopper project, credentials are in:

`/Users/creator/projects/grocery-shopper/client_secret`

Expected format:

```text
client_id: <id>
client_secret: <secret>
```

The full Kroger client ID may include the app-name prefix. Use the exact value from the developer portal, not only a suffix.

## Client Credentials Smoke Test

Use client credentials for non-user product/location smoke tests.

1. Read `client_id` and `client_secret` from the local file.
2. POST to `/token` with Basic auth:

```text
grant_type=client_credentials
scope=product.compact
```

3. Verify a `200` response with a bearer token.
4. Use that token for:

```text
GET /v1/locations?filter.zipCode.near=45202&filter.limit=1
GET /v1/products?filter.term=milk&filter.limit=3&filter.locationId=<locationId>
```

## Product Selection for Cart Tests

For pickup cart tests, first use Products API with a location ID and choose products with:

- `fulfillment.curbside == true`
- `inventory.stockLevel` not `TEMPORARILY_OUT_OF_STOCK` when available
- exact UPC from the product result

Known tested production examples at location `01400513`:

- Campbell's Condensed Chicken Noodle Soup, 10.75 oz Can: UPC `0005100001251`, pickup available.
- Fresh Large Ripe Avocado: UPC `0000000004225`, pickup available.

Treat these as smoke-test examples, not permanent product assumptions; re-query before using.

## Authorization Code Flow for Customer Cart

Cart add requires CustomerContext via OAuth Authorization Code grant.

Recommended local redirect URI:

`http://localhost:8000/callback`

Register that exact URI in the Kroger app. No trailing slash unless the app is registered with one.

Authorize URL shape:

```text
https://api.kroger.com/v1/connect/oauth2/authorize?scope=cart.basic%3Awrite+profile.compact&response_type=code&client_id=<CLIENT_ID>&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback&state=<STATE>
```

Token exchange:

```text
POST https://api.kroger.com/v1/connect/oauth2/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=<CODE>&redirect_uri=http://localhost:8000/callback
```

## Add to Cart

Endpoint:

```text
PUT https://api.kroger.com/v1/cart/add
Authorization: Bearer <customer_access_token>
Content-Type: application/json
```

Payload example:

```json
{
  "items": [
    {"upc": "0005100001251", "quantity": 1, "modality": "PICKUP"},
    {"upc": "0000000004225", "quantity": 3, "modality": "PICKUP"}
  ]
}
```

Expected success: `204 No Content`.

## Cleanup / Remove Items

Public Cart API docs only expose `PUT /v1/cart/add`. It can add items and increase quantity; it does not expose a public remove/delete/list-cart endpoint.

If a test item must be removed:

1. Prefer asking the user to remove it from their Kroger cart UI, or
2. If they explicitly authorize website UI cleanup, navigate to `https://www.kroger.com/cart` in a browser session where they are logged in and remove the specific items manually, or
3. Use Partner Cart API delete/update endpoints only if the app has Partner Cart permissions and a valid cart ID flow.

Do not claim API cleanup succeeded unless verified in the cart UI or by an authorized API response.

## Known Pitfalls

- Certification accounts cannot test real user Cart/Profile flows because Kroger user accounts are production-side.
- A successful OAuth login in the user's browser does not log the headless Hermes browser into kroger.com.
- Kroger may redirect with state handling that differs from the locally generated value; if a valid code is received on localhost, log a warning and continue only when the code came through the expected localhost callback.
- The Public Cart API returning `204` means the add was accepted, but it does not return cart contents.
- Browser automation must not type or request the Kroger password; let the user complete login.

## Verification Checklist

- [ ] Credentials file exists and contains both fields.
- [ ] Correct environment token endpoint returns `200`.
- [ ] Product lookup confirms pickup availability and stock for selected UPCs.
- [ ] User explicitly approved exact add-to-cart mutation.
- [ ] OAuth code exchange returns customer access token.
- [ ] `PUT /cart/add` returns `204`.
- [ ] User or UI confirms cart contents when needed.
- [ ] Cleanup limitations are stated honestly if public API cannot remove items.
