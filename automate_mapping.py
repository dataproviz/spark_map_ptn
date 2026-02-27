"""
Pydantic Source Mapping Example
================================
Demonstrates:
  - Loading JSON → Pydantic source models (3 types)
  - Registry-based dispatcher to select mapper per source_type
  - Input massaging (normalization, clamping, derivations, audit trail)
  - Mapping to a unified target model (PersonProfile)
"""

import re
import json
from datetime import datetime
from typing import Literal, Union, Callable
from pydantic import BaseModel


# ── SOURCE MODELS ──────────────────────────────────────────────────────────────

class EmployeeSource(BaseModel):
    source_type: Literal["employee"]
    emp_id: str
    full_name: str
    department: str
    salary: float


class ContractorSource(BaseModel):
    source_type: Literal["contractor"]
    contractor_id: str
    first_name: str
    last_name: str
    hourly_rate: float
    agency: str


class VendorSource(BaseModel):
    source_type: Literal["vendor"]
    vendor_code: str
    company_name: str
    contact_email: str
    contract_value: float


# Discriminated Union — Pydantic picks the right model based on source_type
AnySource = Union[EmployeeSource, ContractorSource, VendorSource]


# ── TARGET MODEL (unified structure) ──────────────────────────────────────────

class PersonProfile(BaseModel):
    id: str
    display_name: str
    category: str           # "internal" | "contract" | "vendor"
    email: str | None = None
    annual_cost: float      # normalized cost field
    metadata: dict = {}


# ── MAPPER FUNCTIONS (with input massaging) ────────────────────────────────────

def map_employee(src: EmployeeSource) -> PersonProfile:
    # ── Name: normalize whitespace + title case
    clean_name = " ".join(src.full_name.strip().split()).title()

    # ── Department: strip special chars, uppercase
    clean_dept = re.sub(r"[^a-zA-Z0-9 ]", "", src.department).strip().upper()

    # ── Salary: cap at a max for display (e.g., compliance rule)
    MAX_DISPLAY_SALARY = 200_000
    display_salary = min(src.salary, MAX_DISPLAY_SALARY)

    # ── Derive seniority band from salary
    if src.salary >= 150_000:
        band = "senior"
    elif src.salary >= 100_000:
        band = "mid"
    else:
        band = "junior"

    return PersonProfile(
        id=src.emp_id.upper(),              # normalize ID to uppercase
        display_name=clean_name,
        category="internal",
        annual_cost=display_salary,
        metadata={
            "department": clean_dept,
            "seniority_band": band,
            "raw_salary": src.salary,       # keep original for audit
        }
    )


def map_contractor(src: ContractorSource) -> PersonProfile:
    # ── Name: strip + title case each part
    first = src.first_name.strip().title()
    last  = src.last_name.strip().title()

    # ── Agency: fallback if empty/whitespace
    agency = src.agency.strip() or "Independent"

    # ── Annualize hourly rate (clamp unrealistic rates)
    MIN_RATE, MAX_RATE = 20, 500
    safe_rate = max(MIN_RATE, min(src.hourly_rate, MAX_RATE))
    if safe_rate != src.hourly_rate:
        print(f"⚠️  Hourly rate {src.hourly_rate} clamped to {safe_rate}")
    annual_cost = safe_rate * 2080   # 40hr * 52wk

    # ── Build email guess if agency is known
    email_domain_map = {"TechStaff": "techstaff.com", "Infosys": "infosys.com"}
    domain = email_domain_map.get(agency)
    inferred_email = f"{first.lower()}.{last.lower()}@{domain}" if domain else None

    return PersonProfile(
        id=src.contractor_id.upper(),
        display_name=f"{first} {last}",
        category="contract",
        email=inferred_email,
        annual_cost=annual_cost,
        metadata={
            "agency": agency,
            "hourly_rate": safe_rate,
            "annualization_basis": "2080hrs",
        }
    )


def map_vendor(src: VendorSource) -> PersonProfile:
    # ── Company name: remove common legal suffixes for display
    LEGAL_SUFFIXES = r"\b(Inc\.?|LLC\.?|Corp\.?|Ltd\.?|Co\.?)\b"
    display_name = re.sub(LEGAL_SUFFIXES, "", src.company_name, flags=re.IGNORECASE).strip()
    display_name = display_name or src.company_name  # fallback to original

    # ── Email: lowercase + basic format validation
    email = src.contact_email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        print(f"⚠️  Invalid email '{email}' for vendor {src.vendor_code}, setting None")
        email = None

    # ── Contract value: round to nearest 1000 for reporting
    rounded_value = round(src.contract_value / 1000) * 1000

    # ── Tier classification by contract value
    if src.contract_value >= 1_000_000:
        tier = "enterprise"
    elif src.contract_value >= 100_000:
        tier = "strategic"
    else:
        tier = "standard"

    # ── Tag with processing timestamp
    processed_at = datetime.utcnow().isoformat() + "Z"

    return PersonProfile(
        id=src.vendor_code.upper(),
        display_name=display_name,
        category="vendor",
        email=email,
        annual_cost=rounded_value,
        metadata={
            "original_company_name": src.company_name,  # audit trail
            "contract_tier": tier,
            "raw_contract_value": src.contract_value,
            "processed_at": processed_at,
        }
    )


# ── MAPPER REGISTRY + DISPATCHER ──────────────────────────────────────────────

SOURCE_MODEL_REGISTRY: dict[str, type] = {
    "employee":   EmployeeSource,
    "contractor": ContractorSource,
    "vendor":     VendorSource,
}

MAPPER_REGISTRY: dict[str, Callable] = {
    "employee":   map_employee,
    "contractor": map_contractor,
    "vendor":     map_vendor,
}


def parse_and_map(raw: dict) -> PersonProfile:
    """
    1. Peek at source_type
    2. Parse into the correct source model (validation runs here)
    3. Apply the correct mapper (massaging + transformation runs here)
    """
    source_type = raw.get("source_type")
    if not source_type:
        raise ValueError("Missing 'source_type' in payload")

    source_model = SOURCE_MODEL_REGISTRY.get(source_type)
    mapper_fn    = MAPPER_REGISTRY.get(source_type)

    if not source_model or not mapper_fn:
        raise ValueError(f"Unsupported source_type: '{source_type}'")

    parsed_source = source_model(**raw)
    return mapper_fn(parsed_source)


def process_file(file_path: str) -> list[PersonProfile]:
    """Load a JSON file (list of mixed-type records) and map all to PersonProfile."""
    with open(file_path) as f:
        records = json.load(f)

    results, errors = [], []
    for i, record in enumerate(records):
        try:
            results.append(parse_and_map(record))
        except Exception as e:
            errors.append({"index": i, "error": str(e), "record": record})

    if errors:
        print(f"\n⚠️  {len(errors)} record(s) failed:")
        for err in errors:
            print(f"  [{err['index']}] {err['error']}")

    return results


# ── GENERIC TRANSFORM HELPER ───────────────────────────────────────────────────

from typing import TypeVar, Type
SourceT = TypeVar("SourceT", bound=BaseModel)
TargetT = TypeVar("TargetT", bound=BaseModel)


def transform(
    raw: dict,
    source_model: Type[SourceT],
    target_model: Type[TargetT],
    mapper_fn: Callable[[SourceT], TargetT]
) -> TargetT:
    """Generic: dict → Source Model → Target Model"""
    source = source_model(**raw)
    return mapper_fn(source)


# ── MAIN: TEST WITH MESSY INPUTS ──────────────────────────────────────────────

if __name__ == "__main__":
    records = [
        {
            "source_type": "employee",
            "emp_id": "e001",                   # lowercase → normalized to E001
            "full_name": "  siva   kancherla ",  # messy whitespace → "Siva Kancherla"
            "department": "data-engineering!!",  # special chars → "DATA ENGINEERING"
            "salary": 250000,                    # over cap → clamped to 200,000
        },
        {
            "source_type": "contractor",
            "contractor_id": "c99",
            "first_name": "  john  ",            # whitespace stripped
            "last_name": "doe",                  # title-cased → "Doe"
            "hourly_rate": 9999,                 # unrealistic → clamped to 500
            "agency": "TechStaff",               # known agency → email inferred
        },
        {
            "source_type": "vendor",
            "vendor_code": "v12",
            "company_name": "AWS Corp.",          # legal suffix stripped → "AWS"
            "contact_email": "  AWS@CORP.COM  ",  # trimmed + lowercased
            "contract_value": 487350,             # rounded → 487,000 | tier: strategic
        },
    ]

    print("=" * 60)
    for record in records:
        profile = parse_and_map(record)
        print(profile.model_dump_json(indent=2))
        print("─" * 60)