---
name: bulk-email-outreach
description: Send batch inquiry emails to rental vendors, venues, or suppliers from Hermes using himalaya CLI or sendmail
version: 1.0.0
metadata:
  hermes:
    tags: [email, outreach, vendor-research, rentals]
    category: productivity
---

# Bulk Email Outreach — Vendor / Rental Inquiries

Use this when the user wants to contact multiple vendors or rental companies at once for an event or project inquiry.

## Step 1 — Find Contact Emails

Use web search to find email addresses for target companies. Preferred sources:
- Company website contact pages
- Google Business listings
- Yahoo or Bing search (avoid Google — blocks bots with CAPTCHAs)

> Note: Many company websites use anti-bot protection. If a site returns 403 or CAPTCHA, try Bing/Yahoo or look up the business on Google Maps for a direct link to their site or email.

### Known False Positives to Watch
- **A-1 Party Rental (Lilburn, GA)** — domain `a1partyrental.com` now redirects to Hundred House in California. This is NOT the same company. Phone number (770) 931-7222 is no longer valid for GA. Cross-check by searching the phone number to confirm the location.

## Step 2 — Confirm Email Reachable

Before composing, verify the email is monitored:
- Try navigating to `https://[companydomain]/contact` to see if they have a contact form
- If the company website is down (DNS failure, 403, etc.), the email may be unmonitored — note this to the user

## Step 3 — Send Emails

### Option A: himalaya (preferred — works in non-TTY environments)

**Install** (if not present):
```bash
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh
```

**Configure manually** — himalaya's interactive wizard requires a TTY, so write the config file directly:
```bash
mkdir -p ~/.config/himalaya
cat > ~/.config/himalaya/config.toml << 'EOF'
[accounts.personal]
email = "YOUR_EMAIL@gmail.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.gmail.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "YOUR_EMAIL@gmail.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.gmail.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "YOUR_EMAIL@gmail.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"
EOF
```

**Send email** (non-interactive, via stdin):
```bash
cat << 'EOF' | himalaya template send --account personal
From: Your Name <your@email.com>
To: vendor@example.com
Subject: Your Subject Line

Your message body here.
EOF
```

### Option B: sendmail (if himalaya is unavailable)

On macOS, `/usr/sbin/sendmail` exists but is actually Apple's `mail` wrapper — it only works if the system has SMTP configured. Test first:
```bash
echo "test" | sendmail -v recipient@example.com 2>&1 | head -5
# If it says "mailer daemon" in output, it's not configured
```

### Option C: curl to Gmail SMTP (fallback)
```bash
curl -s --url 'smtp://smtp.gmail.com:587' \
  --user 'YOUR_EMAIL@gmail.com:APP_PASSWORD' \
  --mail-from 'YOUR_EMAIL@gmail.com' \
  --mail-rcpt 'recipient@example.com' \
  --upload-file - <<< $'From: Your Name <your@email.com>\nTo: recipient@example.com\nSubject: Subject\n\nBody'
```

## Step 4 — Report Back

Return to the user:
- Which emails were sent successfully
- Which companies had unreachable emails or websites (so they can call instead)
- The full email text used (so they can resend manually if needed)

## Email Composition Tips

- No emojis in the email body (user preference noted)
- Sound human — warm, professional, not templated
- Include: event date, venue location, specific needs (tent size/style, seating count, setup time)
- Offer to call as alternative — always include a phone number or invitation to reply

## Verification

After sending, confirm no errors in the terminal output. If himalaya returns an error, fall back to Option C (curl SMTP) or report to user with the full email text to send manually.
