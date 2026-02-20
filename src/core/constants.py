"""Fixed constants and lookup tables"""

COMPANY_SYNONYMS = {
    "AAPL": {
        "canonical_name": "Apple Inc.",
        "synonyms": ["apple", "apple inc", "aapl", "apple computer", "iphone maker"],
    },
    "MSFT": {
        "canonical_name": "Microsoft Corp.",
        "synonyms": ["microsoft", "microsoft corp", "msft", "windows maker", "azure"],
    },
    "GOOGL": {
        "canonical_name": "Alphabet Inc.",
        "synonyms": ["alphabet", "googl", "google", "youtube", "android"],
    },
    "AMZN": {
        "canonical_name": "Amazon.com, Inc.",
        "synonyms": ["amazon", "amzn", "aws"],
    },
    "META": {
        "canonical_name": "Meta Platforms, Inc.",
        "synonyms": ["meta", "facebook", "instagram", "whatsapp"],
    },
    "NVDA": {
        "canonical_name": "NVIDIA Corp.",
        "synonyms": ["nvidia", "nvda"],
    },
    "TSLA": {
        "canonical_name": "Tesla, Inc.",
        "synonyms": ["tesla", "tsla"],
    },
    "ORCL": {
        "canonical_name": "Oracle Corp.",
        "synonyms": ["oracle", "orcl"],
    },
    "CRM": {
        "canonical_name": "Salesforce, Inc.",
        "synonyms": ["salesforce", "crm", "slack"],
    },
    "NFLX": {
        "canonical_name": "Netflix, Inc.",
        "synonyms": ["netflix", "nflx"],
    },
    "ADBE": {
        "canonical_name": "Adobe Inc.",
        "synonyms": ["adobe", "adbe", "photoshop"],
    },
}

HEADINGS_10K = [
    "business",
    "risk factors",
    "legal proceedings",
    "properties",
    "management discussion and analysis of financial condition and results of operations",
    "quantitative and qualitative disclosures about market risk",
    "financial statements and supplementary data",
    "controls and procedures",
    "market for registrant's common equity, related stockholder matters and issuer purchases of equity securities",
    "executive compensation",
    "security ownership of certain beneficial owners and management and related stockholder matters",
    "certain relationships and related transactions and director independence",
    "directors, executive officers and corporate governance",
    "principal accountant fees and services",
    "unresolved staff comments",
    "cybersecurity",
    "other information",
    "exhibits and financial statement schedules",
    "10-k summary",
]

HEADINGS_10Q = [
    "financial statements",
    "management discussion and analysis of financial condition and results of operations",
    "risk factors",
    "legal proceedings",
    "quantitative and qualitative disclosures about market risk",
    "controls and procedures",
    "unregistered sales of equity securities and use of proceeds",
    "exhibits",
    "other information",
]

QUERY_TYPES = ["GENERAL", "SIMPLE", "BROAD", "COMPARISON", "CHANGE_DETECTION"]
DATA_SOURCES = ["SEC", "TRANSCRIPT"]
INPUT_CLASSIFICATIONS = [
    "SMALL_TALK",
    "OUT_OF_SCOPE",
    "INVESTMENT_ADVICE_REQUEST",
    "PERSONAL_INFO",
    "FINANCE_RESEARCH_OK",
]
TRANSCRIPT_FOCUS = ["METRICS", "RISKS", "GUIDANCE", "GENERAL"]