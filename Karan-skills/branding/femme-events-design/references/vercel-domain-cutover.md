# Vercel + domain.com cutover for Femme Events

Use this when moving `femmeevents.com` from domain.com forwarding/parking to the Vercel-hosted Femme Events website.

## Known-good target

- Vercel project: `femme-events-website`
- Vercel scope: `sabnanikl-devs-projects`
- GitHub repo: `sabnanikl-dev/Femme-Events-Website`
- Production branch: `main`
- Build settings: Vite, `npm install`, `npm run build`, output `dist`, Node `24.x`
- Production URL before custom DNS: `https://femme-events-website.vercel.app`

## Required Vercel config

The app is Vite + React Router, so direct routes need an SPA fallback. Add/verify `vercel.json`:

```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

Without this, the Vercel homepage can work while direct loads like `/about`, `/journal`, or `/what-happens-next` return Vercel 404s.

Required env vars in Production, Preview, and Development:

- `VITE_FORMSPREE_ENDPOINT`
- `VITE_SANITY_PROJECT_ID`
- `VITE_SANITY_DATASET`
- `VITE_SANITY_API_VERSION`

## domain.com DNS cutover

Keep nameservers at domain.com unless Karan explicitly approves moving DNS to Vercel. Preserve Google Workspace records.

Set web records:

```text
A  @    76.76.21.21
A  www  76.76.21.21
```

Vercel may also support `CNAME www cname.vercel-dns.com`, but in this session Vercel CLI explicitly recommended `A www.femmeevents.com 76.76.21.21`; follow the active Vercel recommendation if it differs.

Do not remove:

- MX `smtp.google.com`
- SPF TXT including `_spf.google.com`
- Google site verification TXT
- DKIM/DMARC/Workspace records if present

Also disable any domain.com web forwarding to `bio.site/AmandaFemme`; stale forwarding can mask correct DNS.

## Verification pattern

Check authoritative DNS first, because public resolvers can cache old values:

```bash
dig @ns1.domain.com +short A femmeevents.com
dig @ns2.domain.com +short A femmeevents.com
dig @ns1.domain.com +short A www.femmeevents.com
dig @ns2.domain.com +short A www.femmeevents.com
```

Then check public resolvers:

```bash
dig @1.1.1.1 +short A femmeevents.com
dig @8.8.8.8 +short A femmeevents.com
dig @1.1.1.1 +short A www.femmeevents.com
dig @8.8.8.8 +short A www.femmeevents.com
```

Expect propagation lag: authoritative domain.com nameservers may show `76.76.21.21` while public resolvers still show the old `209.17.116.163` for a while.

Use forced-resolution probes to distinguish Vercel readiness from public DNS cache:

```bash
curl -I --resolve "femmeevents.com:80:76.76.21.21" http://femmeevents.com/about
curl -vI --resolve "femmeevents.com:443:76.76.21.21" https://femmeevents.com/
curl -vI --resolve "www.femmeevents.com:443:76.76.21.21" https://www.femmeevents.com/
```

HTTPS can be ready at Vercel even while normal lookups still hit the old host. Verify cert SAN matches the host.

## Final acceptance criteria

- Authoritative and public DNS for root and www point to `76.76.21.21`.
- `https://femmeevents.com` loads the Vercel Femme Events site.
- `http://femmeevents.com` redirects to HTTPS.
- `https://www.femmeevents.com` redirects to/root canonical, or otherwise behaves as intentionally configured.
- Direct routes return 200: `/about`, `/journal`, `/what-happens-next`.
- Vercel JS/CSS assets return 200.
- Browser console has no JS errors on a direct route.
- MX/SPF/Google verification records remain intact.

## Silent propagation watchdog pattern

For DNS cutovers, prefer a script-only cron watchdog that stays silent until all checks pass, then sends one concise alert. Avoid noisy repeated “still propagating” updates.

Pattern:

- Script exits 0 with empty stdout while incomplete: no delivery.
- Script writes a state/sentinel file after success to avoid duplicate alerts.
- Cron uses `no_agent=true`, short repeat interval, finite repeat count, and a messaging delivery target.
- Alert should be direct: “Femme Events production is propagated and ready. Go check the website: https://femmeevents.com”.
