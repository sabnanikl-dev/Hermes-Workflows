# JMD SafeBrowse / Local Filtering Case

Session: 2026-05-03
Client/site: `jmdmenswear.com` on HostGator/cPanel/WordPress

## Symptom

From the local non-VPN environment:

- `https://jmdmenswear.com` and `https://www.jmdmenswear.com` failed with TLS protocol errors.
- `http://jmdmenswear.com` and `http://www.jmdmenswear.com` redirected to `safebrowse.io` warning pages.

This initially looked like HostGator SSL/vhost/SafeBrowse failure.

## Contradicting Evidence

Karan tested incognito + VPN on the same Wi-Fi and the site loaded.

External checks then showed:

- SSL Labs: grade A for both root and `www`, IP `192.254.232.174`.
- Sucuri SiteCheck: no malware found, not blacklisted, Google Safe Browsing clean, redirects to `https://jmdmenswear.com/`, WordPress reachable.

## Diagnosis

Likely local ISP/router/security-layer false-positive filtering/interception, not a HostGator/DNS/WordPress failure.

## Recommended Sequence

1. Do not change DNS, nameservers, SSL, Force HTTPS, `.htaccess`, WordPress, or HostGator files while external checks pass.
2. Ask the user to test:
   - phone cellular with Wi-Fi off
   - one other external network/person
   - root and `www`
3. If external tests pass, close the domain issue as hosting resolved and document the local warning as network filtering.
4. If multiple external tests fail, resume HostGator escalation with external proof.

## Lesson

When local CLI/browser checks fail but VPN on the same Wi-Fi succeeds, immediately branch into local-filtering diagnostics before recommending hosting changes.
