# Kroger API cart testing notes

Use this when testing Kroger grocery/cart automation from local credentials.

## Durable API facts

- Cart mutation is customer-context OAuth, not service-to-service. To add to a real Kroger cart, use OAuth2 Authorization Code flow with the customer's Kroger login and consent.
- Local redirect URI must be registered exactly in the Kroger Developer app before the customer flow will complete. A practical local value is `http://localhost:8000/callback`.
- Kroger production token endpoint: `POST https://api.kroger.com/v1/connect/oauth2/token`.
- Kroger certification token endpoint: `POST https://api-ce.kroger.com/v1/connect/oauth2/token`.
- Authorization endpoint: `https://api.kroger.com/v1/connect/oauth2/authorize`.
- Certification-environment developer apps may authenticate against `api-ce.kroger.com` while returning `401 invalid credentials` against production `api.kroger.com`; test certification first when the app/API rows say `- Certification`.
- Public cart add endpoint: `PUT https://api.kroger.com/v1/cart/add`.
- Cart add payload shape:

```json
{
  "items": [
    {"quantity": 1, "upc": "0001111060903", "modality": "PICKUP"}
  ]
}
```

- Kroger docs/examples use scopes such as `product.compact` for product search and `cart.basic:write` or `cart.basic:rw` for cart writes. Ask the docs/API response if one is rejected.
- Product search can be service-to-service (`client_credentials`) and is useful as a preflight before customer auth:
  - `GET /v1/products?filter.term=<term>`
  - Add `filter.locationId=<store>` for price/availability/fulfillment at a specific location.

## Workflow

1. Keep credentials in a local file or environment variables. Do not paste or echo secrets in chat/output.
2. Parse credential files leniently: Kroger exports may be simple `client_id: ...` / `client_secret: ...` lines rather than JSON or `.env`.
   - Prefer the full app-prefixed `client_id` shown in the developer UI (for example, `<app-name>-<suffix>`). A local file may contain only the suffix; the suffix alone can return `401 invalid credentials`.
   - If the app permissions/API names end in `- Certification`, smoke-test `https://api-ce.kroger.com` before production.
   - If new production credentials return `200` on `api.kroger.com` and `401` on `api-ce.kroger.com`, that is expected and confirms they are production-only credentials.
3. Smoke-test the client ID/secret before asking the user to complete browser OAuth:
   - Use `grant_type=client_credentials` with `scope=product.compact`.
   - Header: `Authorization: Basic base64(client_id:client_secret)`.
   - Body content type: `application/x-www-form-urlencoded`.
4. If client-credentials returns `401 invalid credentials`, stop. The redirect URI is not the problem yet; the client ID/secret pair itself is being rejected.
5. Once credentials pass, make sure the redirect URI is registered exactly, then run local callback listener and open the `/authorize` URL with customer scopes.
   - Practical production authorize URL shape: `https://api.kroger.com/v1/connect/oauth2/authorize?scope=cart.basic%3Awrite+profile.compact&response_type=code&client_id=<client_id>&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback&state=<random>`.
   - Do not ask the user for their Kroger password. Open/navigate to the auth URL and let the user complete login/consent in the browser.
6. Exchange the returned `code` for customer access/refresh tokens with `grant_type=authorization_code`, the same `redirect_uri`, and Basic client auth.
7. Resolve UPCs through product search, preferably with location and fulfillment filters.
   - Search terms can identify pickup-eligible products before auth. For example, `Campbell's Condensed Chicken Noodle Soup` and `Fresh Large Ripe Avocado` return UPCs with `fulfillment.curbside=true` at a location when available.
8. Ask/confirm modality (`PICKUP` vs `DELIVERY`) before cart mutation if the user did not specify. Default recommendation for testing is `PICKUP`.
9. Add items to cart and verify by HTTP status/readback where available. Public Cart API is write-only; a `204 No Content` from `/v1/cart/add` is the primary API-side success signal, and the user can verify final cart contents in Kroger’s UI.

## Reusable helper

- `scripts/kroger_oauth_cart_add.py` is a reusable local helper for customer OAuth + `PUT /v1/cart/add`.
- Run it with a local credential file and explicit items, for example:

```bash
python3 scripts/kroger_oauth_cart_add.py \
  --creds /Users/creator/projects/grocery-shopper/client_secret \
  --redirect-uri http://localhost:8000/callback \
  --item 0005100001251:1:PICKUP \
  --item 0000000004225:3:PICKUP
```

- It prints the auth URL, starts a local callback server, waits for browser login/consent, exchanges the code, and sends the cart-add payload while redacting tokens/secrets.

## Certification smoke-test recipe

For a certification app, a good non-mutating test sequence is:

1. Request a client-credentials token from `https://api-ce.kroger.com/v1/connect/oauth2/token` with `scope=product.compact`.
2. Call Locations: `GET https://api-ce.kroger.com/v1/locations?filter.zipCode.near=45202&filter.limit=1`.
3. Use the returned `locationId` for Products: `GET https://api-ce.kroger.com/v1/products?filter.term=milk&filter.limit=3&filter.locationId=<locationId>`.
4. Redact access tokens and client secrets in all output; product/location names and HTTP statuses are safe to report.
5. Optionally probe production with the same client ID/secret. If certification returns `200` but production returns `401 invalid credentials`, report that the credentials are certification-only rather than broken.

## Pitfalls

- `redirect_uri` errors only occur after credentials are valid enough to start the authorization-code flow. Do not attribute a service-to-service `401 invalid credentials` to redirect setup.
- Refreshing a client secret usually invalidates the old secret; confirm the local credential file actually changed before retrying.
- Do not print secrets while debugging. Print file existence, byte count, parsed keys, ID if user already supplied it, and secret length only.
- Kroger returns gzip-compressed error bodies in some clients. If an HTTP error looks like binary garbage, decompress gzip before interpreting.
- Product search without `locationId` is nationwide catalog only. It does not prove local store availability or cartability.
