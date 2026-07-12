---
name: cpanel-wordpress-domain-triage
description: Diagnose cPanel/HostGator WordPress domain, DNS, SSL, redirects, and emergency holding-page issues safely before making DNS or file changes.
tags: [cpanel, wordpress, hostgator, dns, ssl, redirects, troubleshooting]
triggers:
  - "cpanel"
  - "hostgator"
  - "wordpress ssl"
  - "domain not secure"
  - "safe browse"
  - "ERR_SSL_PROTOCOL_ERROR"
  - "public_html"
---

# cPanel WordPress Domain Triage

Use this when a client site on cPanel/HostGator has DNS, SSL, redirect, SafeBrowse, WordPress, or public_html issues. The goal is to diagnose safely, preserve email/DNS, avoid destructive WordPress changes, and decide whether to keep WordPress, bypass it with a static holding page, or move web traffic elsewhere.

## Core Rules

1. Do not change nameservers, A/CNAME, MX, TXT, or Force HTTPS until current behavior is documented.
2. Preserve email first. MX, SPF, DKIM, autodiscover, and mail A records must not be broken during web fixes.
3. Public cPanel SSL status is not enough. Verify with live `https://root` and `https://www` checks.
4. Root and www are separate DoD checks. Do not mark done if root works but www fails.
5. Always back up `.htaccess` and `index.php` before editing or replacing anything.
6. Prefer a static holding-page test before bypassing WordPress.
7. If WordPress is broken but static files work, use static `index.html` as an emergency path and leave WordPress files intact.

## Step 1: Document DNS and Hosting State

Collect:

- Registrar
- DNS provider / nameservers
- Root A record
- www CNAME/A record
- MX records
- mail A record
- SPF TXT
- DKIM TXT
- Any verification TXT records
- Hosting target / cPanel document root

CLI checks:

```bash
dig +short NS example.com
dig +short A example.com
dig +short CNAME www.example.com
dig +short A www.example.com
dig +short MX example.com
```

Archive exported DNS records if available from cPanel Zone Editor.

## Step 2: Check Live HTTP/HTTPS Behavior

Check all four variants:

```bash
curl -I --max-time 15 http://example.com
curl -I --max-time 15 http://www.example.com
curl -I --max-time 15 https://example.com
curl -I --max-time 15 https://www.example.com
```

Look for:

- 200 OK
- 301/302 targets
- SafeBrowse / malware warning redirects
- TLS protocol errors
- WordPress redirects via `X-Redirect-By: WordPress`
- cPanel/HostGator cache headers

If HTTPS fails with `ERR_SSL_PROTOCOL_ERROR` or TLS protocol error, do not assume AutoSSL is actually working publicly even if cPanel says the cert is valid.

Before making HostGator/WordPress/DNS changes, test whether the failure is local-network specific:

- Ask the user to test the same URL on VPN while staying on the same Wi-Fi.
- Ask the user to test phone cellular with Wi-Fi off.
- Compare against external scanners such as SSL Labs and Sucuri SiteCheck.
- If VPN/cellular/external scanners pass but the local non-VPN path fails with SafeBrowse/TLS errors, pause hosting changes and treat it as likely ISP/router/security filtering or false-positive interception.

## Step 3: Inspect cPanel File Manager

The web root is usually:

```text
/home*/account/public_html
```

In `public_html`, inspect but do not edit yet:

- `.htaccess`
- `index.php`
- `index.html`
- `wp-admin/`
- `wp-content/`
- `wp-includes/`
- `wp-config.php`
- `error_log`

Enable cPanel File Manager setting: “Show Hidden Files (dotfiles)” so `.htaccess` is visible.

### Normal WordPress index.php

Should look like:

```php
<?php
define( 'WP_USE_THEMES', true );
require __DIR__ . '/wp-blog-header.php';
```

### Suspicious signs

In `.htaccess`, `index.php`, themes, plugins, or random PHP files, look for:

- Unknown external domains
- SafeBrowse references
- Redirect/Rewrite rules that do not belong
- `eval`
- `base64_decode`
- `gzinflate`
- `str_rot13`
- long unreadable strings
- random PHP files outside normal WordPress locations

Do not paste or expose `wp-config.php` credentials.

## Step 4: Inspect WordPress Folders

List:

- `wp-content/plugins`
- `wp-content/themes`
- `wp-content/mu-plugins`
- `wp-content/jetpack-waf` if present
- `wp-content/wflogs` if Wordfence exists

Pay attention to recent modifications and security/migration plugins:

- Wordfence
- Jetpack / Jetpack WAF
- HostGator plugin
- Really Simple SSL
- Redirection
- All-in-One WP Migration
- popup/security plugins
- active premium themes like Divi

## Step 5: Read the Error Log

Open `public_html/error_log`, but only inspect the bottom 20 to 40 lines.

Common actionable findings:

- Theme fatal errors
- Plugin fatal errors
- PHP version incompatibilities
- Missing functions/classes
- Permission denied
- Malware scanner or security plugin messages

Example from JMD: repeated fatal errors from Divi/Divi-child meant WordPress was unstable, but not necessarily DNS or SSL.

## Step 6: Check cPanel SSL/TLS Status

In cPanel > SSL/TLS Status, check:

- `example.com`
- `www.example.com`
- `mail.example.com`
- cPanel/webmail/webdisk subdomains as needed

Record:

- Certificate status
- Expiration
- AutoSSL status
- Warning icons

Then verify publicly with curl/browser. cPanel “AutoSSL Domain Validated” can still coexist with public www/TLS problems.

## Step 7: Check cPanel Domains

In cPanel > Domains, record:

- Domain type: primary/addon/alias/subdomain
- Document Root
- Redirects To
- Force HTTPS Redirect: On/Off

Do not turn on Force HTTPS until both HTTP and HTTPS are understood. WordPress may already redirect HTTP to HTTPS. Turning on cPanel Force HTTPS can compound problems.

## Step 8: Static Holding Page Test

Before replacing WordPress, create a harmless static file in `public_html`:

```text
holding-test.html
```

Minimal content:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Site Test</title>
</head>
<body>
  <h1>Site Test</h1>
  <p>If you can see this, static files are being served.</p>
</body>
</html>
```

Use UTF-8 encoding in cPanel.

Test:

```text
http://example.com/holding-test.html
https://example.com/holding-test.html
```

Interpretation:

- HTTP works, HTTPS works: cPanel can serve static files and SSL likely works for that host.
- HTTP works, HTTPS fails: SSL/vhost problem remains.
- Both redirect to SafeBrowse: server/security-layer or domain/account flag, not just WordPress.
- 404: file placed in wrong document root or cache/routing issue.

## Step 9: Check for Local Network / ISP Filtering False Positives

Before changing HostGator, WordPress, SSL, DNS, cPanel redirects, Force HTTPS, or nameservers, compare the failing path against external evidence. A local SafeBrowse redirect or TLS failure can be caused by ISP/router/security filtering rather than the origin server.

Use this especially when:

- Local non-VPN browser/curl shows SafeBrowse warnings, TLS protocol errors, or `ERR_SSL_PROTOCOL_ERROR`.
- The same Wi-Fi works when the user enables VPN/incognito.
- External scanners can reach the site.

Verification pattern:

1. Confirm DNS from public resolvers (`1.1.1.1`, `8.8.8.8`).
2. Ask the user to test phone cellular with Wi-Fi off.
3. Ask one other external network/person to test root and `www`.
4. Run external SSL and malware/blacklist checks when available.
5. If external checks pass, document the local warning as a network/provider false positive and do **not** make hosting/DNS changes.

Reference: `references/local-filtering-false-positive.md` captures the JMD Menswear pattern and a Linear comment template.

## Step 10: Decide Path

### Option A: Keep WordPress live

Choose if:

- Homepage loads over HTTPS
- Client likes current site
- It is good enough as a foundation
- Root and www are healthy or www can be fixed quickly

Then create follow-up tickets for WordPress cleanup instead of blocking emergency domain task.

### Option B: Static emergency holding page

Choose if:

- WordPress homepage is broken/unusable
- Theme/plugin errors prevent reliable public site
- Static test works

Safe procedure:

1. Backup `.htaccess` to `.htaccess.backup-YYYY-MM-DD`.
2. Backup `index.php` to `index.php.wordpress-backup-YYYY-MM-DD`.
3. Create `index.html` holding page.
4. Test root domain.
5. If WordPress still loads because `index.php` is prioritized, rename original `index.php` to `index.php.wordpress-live-backup-YYYY-MM-DD`.
6. Do not delete `wp-admin`, `wp-content`, `wp-includes`, or `wp-config.php`.

### Option C: Move web traffic to Vercel/Netlify

Only choose if cPanel/HostGator is too messy. Prefer A/CNAME changes over nameserver switch to preserve email:

- Root A to hosting target
- www CNAME to hosting target
- Preserve MX, SPF, DKIM, verification TXT records

## Step 11: Completion Criteria

Do not mark a domain/SSL issue done until:

- `https://example.com` loads correctly
- `http://example.com` redirects cleanly to HTTPS or documented canonical URL
- `https://www.example.com` loads or cleanly redirects to canonical root
- `http://www.example.com` loads or cleanly redirects to canonical root
- No SafeBrowse/malware warning redirects remain
- SSL works publicly, not only in cPanel UI
- DNS/email records are documented
- Final issue comment includes proof and decision: keep WordPress, static holding page, or external hosting

## External Scanner / Local Filtering Cross-Check

Use this before escalating or changing files/DNS when results disagree by network.

Recommended outside checks:

- SSL Labs API/UI for `example.com` and `www.example.com`. A clean grade for both root and www means the public TLS endpoint is likely healthy from outside the local network.
- Sucuri SiteCheck for malware/blacklist status, Google Safe Browsing status, observed redirect target, detected CMS, and hosting/IP.
- User-side VPN test on the same Wi-Fi. If VPN succeeds while non-VPN fails, the local ISP/router/security layer is suspect.
- Phone cellular with Wi-Fi off and one additional outside person/network before closing the issue.

Interpretation:

- External scanners pass + VPN/cellular pass + local non-VPN fails: do not touch HostGator/WordPress/DNS; document likely local filtering false positive.
- External scanners fail or multiple outside networks fail: continue HostGator/security/SSL escalation.
- Root passes but `www` fails externally: keep the domain issue open unless DoD is explicitly changed to root-only.

## Host Support Escalation Pattern

If cPanel shows “AutoSSL Domain Validated” but public checks still fail with `ERR_SSL_PROTOCOL_ERROR`, `tlsv1 alert protocol version`, or `no peer certificate available` from multiple external networks/scanners, push support beyond “SSL is installed.” The key language is:

```text
cPanel SSL Status says valid, but the public HTTPS handshake fails before any certificate is served. Please test externally, not only inside cPanel/internal tools. Check the Apache/nginx SSL vhost, SNI routing, and any SafeBrowse/security routing for both root and www.
```

Ask support to confirm before any reinstall/reissue:

- No website files will be changed.
- No DNS records will be changed.
- No email/MX records will be changed.
- Both root and `www` will be included.

If they offer SSL reinstallation/reissue with a 0-24 hour window and confirm files/email are unaffected, approve it. During that window, do not change DNS, redirects, Force HTTPS, WordPress files, or SSL settings.

Support message template:

```text
Please initiate the SSL installation/reissue for example.com and www.example.com. You confirmed this will not affect website files or email. After it completes, please verify externally that:
1. https://example.com works
2. https://www.example.com works or redirects cleanly
3. http://www.example.com no longer redirects to SafeBrowse
```

## cPanel Redirects Caveat

The cPanel Redirects tool may not fix `https://www` when the TLS handshake fails, because the certificate/SNI handshake happens before Apache redirect rules can run. A redirect can help `http://www`, but if `http://www` is intercepted by SafeBrowse or `https://www` fails TLS, the fix is usually HostGator/server-side security or SSL vhost repair.

If using cPanel Redirects, avoid broad defaults:

- Do not use `** All Public Domains **` unless intentionally global.
- Do not use “redirect with or without www” when root already works.
- Prefer domain-specific + “Only redirect with www” + target canonical root URL.

Remove failed experimental redirects so they do not confuse later troubleshooting.

## JMD Lesson Learned

Detailed case note: `references/jmd-safebrowse-local-filtering.md`.

For JMD Menswear, the root domain intermittently worked over HTTPS and WordPress loaded, but `www` still failed TLS / redirected to SafeBrowse. The correct recommendation was not to close JMD-4 until `www` was fixed or the DoD was explicitly changed to root-domain-only. This prevented a false “done” on a partially broken domain setup.

Later, Karan tested incognito + VPN on the same Wi-Fi and the site loaded; SSL Labs gave both root and `www` an A grade; Sucuri reported no malware and Google Safe Browsing clean. That changed the diagnosis to likely local ISP/router/security filtering. The correct updated recommendation was to pause HostGator/WordPress/DNS changes and verify from cellular + another external network before closing.

2. A later JMD pass showed the opposite risk: the local non-VPN path still showed SafeBrowse/TLS failures while VPN/incognito and external scanners showed the site healthy. When VPN works from the same Wi-Fi and SSL Labs/Sucuri pass, pause HostGator changes and treat the failure as likely local ISP/router/security filtering until phone-cellular and another external network disprove it.
