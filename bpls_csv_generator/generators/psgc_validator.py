"""
PSGC Address Validator — Validate Philippine municipality/barangay codes.
"""

import re
from dataclasses import dataclass


@dataclass
class PSGCValidationResult:
    code: str
    is_valid: bool
    region: str = ""
    province: str = ""
    municipality: str = ""
    barangay: str = ""
    message: str = ""


class PSGCValidator:
    """
    Validates Philippine Standard Geographic Code (PSGC) addresses.
    PSGC codes are 9-digit codes: RR(2) PP(2) CC(2) BB(3)
    - RR = Region
    - PP = Province
    - CC = City/Municipality
    - BB = Barangay
    """

    # NCR/Region 14 codes (simplified — common LGUs for BPLS)
    # Full PSGC registry has 40k+ entries; this is a practical subset
    REGIONS = {
        "01": "Region I - Ilocos Region",
        "02": "Region II - Cagayan Valley",
        "03": "Region III - Central Luzon",
        "04": "Region IV-A - CALABARZON",
        "05": "Region V - Bicol Region",
        "06": "Region VI - Western Visayas",
        "07": "Region VII - Central Visayas",
        "08": "Region VIII - Eastern Visayas",
        "09": "Region IX - Zamboanga Peninsula",
        "10": "Region X - Northern Mindanao",
        "11": "Region XI - Davao Region",
        "12": "Region XII - SOCCSKSARGEN",
        "13": "Region XIII - Caraga",
        "14": "NCR - National Capital Region",
        "15": "BARMM - Bangsamoro",
        "16": "CAR - Cordillera Administrative Region",
        "17": "MIMAROPA",
    }

    # NCR cities (common)
    NCR_CITIES = {
        "1401": "Manila",
        "1402": "Mandaluyong",
        "1403": "Marikina",
        "1404": "Pasig",
        "1405": "Quezon City",
        "1406": "San Juan",
        "1407": "Makati",
        "1408": "Taguig",
        "1409": "Pasay",
        "1410": "Parañaque",
        "1411": "Las Piñas",
        "1412": "Muntinlupa",
        "1413": "Pateros",
        "1414": "Taguig (Fort Bonifacio)",
        "1415": "Valenzuela",
        "1416": "Malabon",
        "1417": "Navotas",
        "1418": "Caloocan",
    }

    def __init__(self, psgc_data_file: str | None = None):
        """
        Initialize with optional PSGC data file.
        If not provided, uses built-in NCR subset.
        """
        self.psgc_lookup = {}
        if psgc_data_file:
            self._load_psgc_data(psgc_data_file)

    def validate_barangay_code(self, code: str | int) -> PSGCValidationResult:
        """
        Validate a 9-digit PSGC barangay code.
        Format: RRPPCCBBB (2+2+2+3 = 9 digits)
        """
        code_str = str(code).strip().zfill(9)

        if not re.match(r"^\d{9}$", code_str):
            return PSGCValidationResult(
                code=code_str,
                is_valid=False,
                message="Invalid PSGC format. Must be 9 digits.",
            )

        region_code = code_str[:2]
        province_code = code_str[2:4]
        city_code = code_str[4:6]
        barangay_code = code_str[6:]

        full_municipal = code_str[:6]
        full_province = code_str[:4]

        # Check if we have this in our lookup
        if code_str in self.psgc_lookup:
            entry = self.psgc_lookup[code_str]
            return PSGCValidationResult(
                code=code_str,
                is_valid=True,
                region=entry.get("region", ""),
                province=entry.get("province", ""),
                municipality=entry.get("municipality", ""),
                barangay=entry.get("barangay", ""),
            )

        # Fallback: validate structure only
        region = self.REGIONS.get(region_code, f"Region {region_code}")

        # For NCR, check city
        municipality = ""
        if region_code == "14":
            municipality = self.NCR_CITIES.get(full_municipal, f"Unknown City ({full_municipal})")

        return PSGCValidationResult(
            code=code_str,
            is_valid=True,
            region=region,
            municipality=municipality,
            message="Structurally valid (not in PSGC database — consider loading full PSGC data)",
        )

    def validate_municipality_code(self, code: str | int) -> PSGCValidationResult:
        """Validate a 6-digit municipality/city code."""
        code_str = str(code).strip().zfill(6)

        if not re.match(r"^\d{6}$", code_str):
            return PSGCValidationResult(
                code=code_str,
                is_valid=False,
                message="Invalid municipality code format. Must be 6 digits.",
            )

        region_code = code_str[:2]
        region = self.REGIONS.get(region_code, f"Region {region_code}")

        municipality = ""
        if region_code == "14":
            municipality = self.NCR_CITIES.get(code_str, f"Unknown City ({code_str})")

        return PSGCValidationResult(
            code=code_str,
            is_valid=True,
            region=region,
            municipality=municipality,
        )

    def _load_psgc_data(self, filepath: str):
        """
        Load PSGC data from a CSV file.
        Expected columns: psgc_code, region, province, municipality, barangay
        """
        import csv

        if not filepath.endswith(".csv"):
            return

        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get("psgc_code", "").strip()
                    if code:
                        self.psgc_lookup[code] = {
                            "region": row.get("region", ""),
                            "province": row.get("province", ""),
                            "municipality": row.get("municipality", ""),
                            "barangay": row.get("barangay", ""),
                        }
        except FileNotFoundError:
            pass

    def extract_region_from_barangay(self, barangay_code: str | int) -> str:
        """Extract region code from a barangay code."""
        code_str = str(barangay_code).strip().zfill(9)
        if len(code_str) >= 2:
            return self.REGIONS.get(code_str[:2], f"Region {code_str[:2]}")
        return "Unknown"
