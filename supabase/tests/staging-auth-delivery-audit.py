"""Read-only, fixed-staging Auth configuration audit. Output is allowlisted."""
import importlib.util
import json
from pathlib import Path
import urllib.error
import urllib.request

spec = importlib.util.spec_from_file_location("transport", Path(__file__).with_name("phase6d0-staging-query.py"))
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
STAGING = "https://yourizorge.github.io/fitmetzorge-staging/"

def main():
    request = urllib.request.Request(
        "https://api.supabase.com/v1/projects/mokxyyullfhkfalopbzd/config/auth",
        headers={"Authorization": "Bearer " + transport.credential(),
                 "Accept": "application/json", "User-Agent": "FitMetZorge-Staging-Auth-Audit/1"})
    with urllib.request.urlopen(request, timeout=40) as response:
        config = json.load(response)
    template = config.get("mailer_templates_confirmation_content") or ""
    redirects = [item.strip() for item in (config.get("uri_allow_list") or "").split(",")]
    result = {
        "target": "mokxyyullfhkfalopbzd",
        "email_enabled": config.get("external_email_enabled"),
        "email_confirmation_required": config.get("mailer_autoconfirm") is False,
        "custom_smtp_enabled": config.get("smtp_host") not in (None, ""),
        "smtp_port_present": bool(config.get("smtp_port")),
        "smtp_user_present": bool(config.get("smtp_user")),
        "smtp_password_present": bool(config.get("smtp_pass")),
        "smtp_sender_present": bool(config.get("smtp_admin_email")),
        "smtp_provider": next((provider for provider in ["resend", "sendgrid", "gmail", "outlook", "brevo", "mailgun", "amazonaws"] if provider in (config.get("smtp_host") or "").lower()), "other"),
        "email_send_hook_enabled": config.get("hook_send_email_enabled"),
        "email_rate_limit_per_hour": config.get("rate_limit_email_sent"),
        "email_cooldown_seconds": config.get("smtp_max_frequency"),
        "site_url_is_staging": config.get("site_url") == STAGING,
        "staging_exact_redirect_allowlisted": STAGING in redirects,
        "redirect_count": len(redirects),
        "confirmation_template_default": not template,
        "confirmation_template_uses_confirmation_url": "{{ .ConfirmationURL }}" in template,
        "confirmation_template_has_link": "href=" in template,
        "confirmation_template_custom_token_route": ".TokenHash" in template or ".Token " in template,
        "confirmation_path_is_verify": config.get("mailer_urlpaths_confirmation") in ("/auth/v1/verify", "/verify"),
        "confirmation_path_default": not config.get("mailer_urlpaths_confirmation"),
        "otp_expiry_seconds": config.get("mailer_otp_exp"),
    }
    print(json.dumps(result))

try:
    main()
except urllib.error.HTTPError as error:
    print(json.dumps({"ok": False, "status": error.code, "error": "auth_config_read_rejected"}))
except Exception:
    print(json.dumps({"ok": False, "error": "auth_config_transport_unavailable"}))
