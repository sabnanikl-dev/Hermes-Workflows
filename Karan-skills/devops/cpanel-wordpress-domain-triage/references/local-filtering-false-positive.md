# Local Network / ISP SafeBrowse False Positive Pattern

Use this reference when a cPanel/HostGator WordPress site appears broken from the agent's local network, but the user or external scanners can load it.

## Trigger Pattern

- Local non-VPN browser/curl shows SafeBrowse warning redirects, TLS protocol errors, or `ERR_SSL_PROTOCOL_ERROR`.
- The same device/network works when using a VPN.
- External scanners report the origin as healthy.
- DNS still resolves to the expected cPanel/HostGator IP.

## JMD Menswear Example

Observed from the agent's local path:

- `http://jmdmenswear.com` and `http://www.jmdmenswear.com` redirected to `safebrowse.io` warning pages.
- `https://jmdmenswear.com` and `https://www.jmdmenswear.com` failed with TLS protocol errors before a certificate was served.

Counter-evidence:

- User loaded `https://jmdmenswear.com` in incognito while on VPN over the same Wi-Fi.
- SSL Labs external scan returned Grade A for both root and `www` on `192.254.232.174`.
- Sucuri SiteCheck reported no malware, site not blacklisted, Google Safe Browsing clean, redirect to `https://jmdmenswear.com/`, and WordPress reachable.

Conclusion: treat the local failure as likely local ISP/router/security filtering until disproven. Do not change DNS, SSL, HostGator, WordPress files, cPanel redirects, or nameservers based only on the local failing path.

## Verification Sequence

1. Reconfirm DNS from public resolvers:
   - `dig +short A example.com @1.1.1.1`
   - `dig +short A example.com @8.8.8.8`
   - `dig +short A www.example.com @1.1.1.1`
2. Compare local non-VPN vs VPN/incognito behavior.
3. Run external SSL check such as SSL Labs for root and `www`.
4. Run external malware/blacklist check such as Sucuri SiteCheck.
5. Ask the user to test phone cellular with Wi-Fi off.
6. Ask one other external person/network to test root and `www`.
7. If external paths pass, close/mark resolved with a note that local SafeBrowse is a network/provider false positive.
8. If external paths fail, escalate HostGator with the external failures as proof.

## Linear Comment Template

```text
Follow-up correction: this now looks less like a HostGator DNS/SSL failure and more like a local network / ISP/router security false positive.

Evidence:
- VPN/incognito from the same Wi-Fi loads the site.
- External SSL scan passes for root and www.
- External malware/blacklist scan reports clean.
- Local non-VPN path still shows SafeBrowse/TLS errors.

Recommendation: do not change HostGator, WordPress, SSL, DNS, cPanel redirects, or nameservers right now. Verify from phone cellular and one other external network. If those pass, close as resolved and document the local warning as network filtering.
```
