"""
Webhook Notifications — Send notifications to Slack, Discord, Teams, etc.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional
import urllib.request
import urllib.error


@dataclass
class WebhookConfig:
    url: str
    provider: str  # "slack", "discord", "teams", "generic"
    name: str = ""
    enabled: bool = True


@dataclass
class NotificationPayload:
    event: str
    filename: str
    total_rows: int
    total_errors: int
    total_corrections: int
    quality_score: float
    output_files: list[str] = field(default_factory=list)
    message: str = ""


class WebhookNotifier:
    """Sends notifications to webhook URLs after processing."""

    def __init__(self, configs_file: str = "outputs/webhook_configs.json"):
        self.configs_file = configs_file
        self.configs: list[WebhookConfig] = []
        self._load_configs()

    def _load_configs(self):
        """Load webhook configurations from file."""
        if os.path.exists(self.configs_file):
            with open(self.configs_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    self.configs.append(WebhookConfig(**item))

    def add_config(self, config: WebhookConfig):
        """Add a webhook configuration."""
        self.configs.append(config)
        self._save_configs()

    def _save_configs(self):
        """Save webhook configurations."""
        os.makedirs(os.path.dirname(self.configs_file) or ".", exist_ok=True)
        with open(self.configs_file, "w", encoding="utf-8") as f:
            json.dump([c.__dict__ for c in self.configs], f, indent=2)

    def notify(self, payload: NotificationPayload) -> dict[str, bool]:
        """Send notification to all enabled webhooks."""
        results = {}
        for config in self.configs:
            if not config.enabled:
                continue

            body = self._format_payload(config.provider, payload)
            success = self._send_webhook(config.url, body)
            results[config.name or config.provider] = success

        return results

    def _format_payload(self, provider: str, payload: NotificationPayload) -> dict:
        """Format payload for the specific provider."""
        if provider == "slack":
            return {
                "blocks": [
                    {"type": "header", "text": {"type": "plain_text", "text": f"✅ {payload.event}"}},
                    {"type": "section", "fields": [
                        {"type": "mrkdwn", "text": f"*File:* {payload.filename}"},
                        {"type": "mrkdwn", "text": f"*Rows:* {payload.total_rows}"},
                        {"type": "mrkdwn", "text": f"*Errors:* {payload.total_errors}"},
                        {"type": "mrkdwn", "text": f"*Quality:* {payload.quality_score}%"},
                    ]},
                ]
            }
        elif provider == "discord":
            return {
                "embeds": [{
                    "title": f"✅ {payload.event}",
                    "color": 5763719,
                    "fields": [
                        {"name": "File", "value": payload.filename},
                        {"name": "Rows", "value": str(payload.total_rows)},
                        {"name": "Errors", "value": str(payload.total_errors)},
                        {"name": "Quality", "value": f"{payload.quality_score}%"},
                    ],
                    "footer": {"text": "BPLS CSV Generator"},
                }]
            }
        elif provider == "teams":
            return {
                "@type": "MessageCard",
                "summary": payload.event,
                "sections": [{
                    "activityTitle": payload.event,
                    "facts": [
                        {"name": "File", "value": payload.filename},
                        {"name": "Rows", "value": str(payload.total_rows)},
                        {"name": "Errors", "value": str(payload.total_errors)},
                        {"name": "Quality", "value": f"{payload.quality_score}%"},
                    ],
                }],
            }
        else:
            return {
                "event": payload.event,
                "filename": payload.filename,
                "total_rows": payload.total_rows,
                "total_errors": payload.total_errors,
                "total_corrections": payload.total_corrections,
                "quality_score": payload.quality_score,
                "output_files": payload.output_files,
                "message": payload.message,
            }

    def _send_webhook(self, url: str, payload: dict) -> bool:
        """Send POST request to webhook URL."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in (200, 204)
        except Exception:
            return False
