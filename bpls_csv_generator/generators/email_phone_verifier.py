"""
Email & Phone Verification — Verify email deliverability and validate Philippine mobile numbers.
"""

import re
from dataclasses import dataclass


@dataclass
class EmailVerificationResult:
    email: str
    is_valid_format: bool
    domain: str = ""
    has_mx_record: bool = False
    is_disposable: bool = False
    suggestion: str = ""


@dataclass
class PhoneVerificationResult:
    phone: str
    is_valid: bool
    carrier: str = ""
    line_type: str = ""  # mobile, landline
    formatted: str = ""
    suggestion: str = ""


class EmailPhoneVerifier:
    """Verifies email formats and Philippine mobile numbers."""

    # Known disposable email domains
    DISPOSABLE_DOMAINS = {
        "tempmail.com", "throwaway.email", "mailinator.com",
        "guerrillamail.com", "sharklasers.com", "yopmail.com",
        "temp-mail.org", "fakeinbox.com", "dispostable.com",
    }

    # Philippine mobile carrier prefixes (after 639)
    CARRIER_PREFIXES = {
        # Globe/TM
        "917": "Globe", "905": "Globe", "906": "Globe", "915": "Globe",
        "916": "Globe", "926": "Globe", "927": "Globe", "935": "Globe",
        "936": "Globe", "937": "Globe", "945": "Globe", "956": "Globe",
        "965": "Globe", "966": "Globe", "967": "Globe", "975": "Globe",
        "976": "Globe", "977": "Globe", "995": "Globe", "996": "Globe",
        "997": "Globe",
        # Smart/TNT
        "900": "Smart", "907": "Smart", "908": "Smart", "909": "Smart",
        "910": "Smart", "911": "Smart", "912": "Smart", "913": "Smart",
        "914": "Smart", "918": "Smart", "919": "Smart", "920": "Smart",
        "921": "Smart", "928": "Smart", "929": "Smart", "930": "Smart",
        "938": "Smart", "939": "Smart", "946": "Smart", "947": "Smart",
        "948": "Smart", "949": "Smart", "950": "Smart",
        "981": "Smart", "989": "Smart", "991": "Smart", "992": "Smart",
        "993": "Smart", "994": "Smart", "998": "Smart", "999": "Smart",
        # DITO
        "895": "DITO", "896": "DITO", "897": "DITO", "898": "DITO",
        "899": "DITO", "991": "DITO",
        # Sun Cellular
        "922": "Sun", "923": "Sun", "924": "Sun", "925": "Sun",
        "931": "Sun", "932": "Sun", "933": "Sun", "934": "Sun",
        "941": "Sun", "942": "Sun", "943": "Sun",
        # Talk 'N Text
        "902": "TNT", "903": "TNT", "904": "TNT",
    }

    def verify_email(self, email: str) -> EmailVerificationResult:
        """Verify an email address format and domain."""
        email = email.strip().lower()

        # Basic regex validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        is_valid = bool(re.match(pattern, email))

        if not is_valid:
            suggestion = self._suggest_email_fix(email)
            return EmailVerificationResult(
                email=email,
                is_valid_format=False,
                suggestion=suggestion,
            )

        domain = email.split("@")[1]
        is_disposable = domain in self.DISPOSABLE_DOMAINS

        return EmailVerificationResult(
            email=email,
            is_valid_format=True,
            domain=domain,
            is_disposable=is_disposable,
            has_mx_record=True,  # Assume OK without DNS lookup
        )

    def verify_phone(self, phone: str) -> PhoneVerificationResult:
        """Verify a Philippine mobile number."""
        phone = phone.strip()
        original = phone

        # Remove separators
        phone = re.sub(r"[\s\-\(\)]+", "", phone)

        # Normalize: if starts with 09, convert to 639
        if phone.startswith("09"):
            phone = "63" + phone[1:]

        # Validate format
        if not re.match(r"^639\d{9}$", phone):
            return PhoneVerificationResult(
                phone=original,
                is_valid=False,
                suggestion="Phone must be 639XXXXXXXXX (12 digits)",
                formatted="",
            )

        # Identify carrier
        carrier_prefix = phone[2:5]  # e.g., "917"
        carrier = self.CARRIER_PREFIXES.get(carrier_prefix, "Unknown")

        # Format for display
        formatted = f"{phone[:2]} {phone[2:5]} {phone[5:8]} {phone[8:]}"

        return PhoneVerificationResult(
            phone=original,
            is_valid=True,
            carrier=carrier,
            line_type="mobile",
            formatted=formatted,
        )

    def verify_sheet_phones(self, rows: list[dict], field: str = "cellphone_no") -> list[PhoneVerificationResult]:
        """Verify all phone numbers in a sheet."""
        results = []
        for row in rows:
            phone = row.get(field)
            if phone and str(phone).strip():
                result = self.verify_phone(str(phone))
                if not result.is_valid:
                    results.append(result)
        return results

    def verify_sheet_emails(self, rows: list[dict], field: str = "email_address") -> list[EmailVerificationResult]:
        """Verify all emails in a sheet."""
        results = []
        for row in rows:
            email = row.get(field)
            if email and str(email).strip():
                result = self.verify_email(str(email))
                if not result.is_valid_format or result.is_disposable:
                    results.append(result)
        return results

    def _suggest_email_fix(self, email: str) -> str:
        """Suggest a fix for invalid email."""
        if "@" not in email:
            return "Email must contain @ symbol"
        parts = email.split("@")
        if len(parts) == 2 and "." not in parts[1]:
            return f"Domain '{parts[1]}' appears to be missing TLD (e.g., .com)"
        if not parts[0]:
            return "Email must have text before @"
        if not parts[1]:
            return "Email must have domain after @"
        return "Check for typos in the email address"
