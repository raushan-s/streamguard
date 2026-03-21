"""
StreamGuard V3 - Layer 1: PII Detection
Uses Microsoft Presidio to detect and sanitize PII in text.
"""

import re
from typing import List, Dict, Optional
from presidio_analyzer import AnalyzerEngine, RecognizerResult, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_analyzer.nlp_engine import SpacyNlpEngine
import spacy


class PIIDetector:
    """
    PII Detection and sanitization using Microsoft Presidio.

    Supports 30+ entity types including:
    - EMAIL_ADDRESS, PHONE_NUMBER
    - US_SSN (with custom patterns), UK_NINO, IT_FISCAL_CODE
    - CREDIT_CARD (with custom patterns), IBAN_CODE, US_BANK_NUMBER
    - PERSON, LOCATION, DATE_TIME
    - IP_ADDRESS, URL, AWS_KEY, API_KEY
    - MEDICAL_LICENSE, LICENSE_PLATE
    """

    def __init__(self):
        """Initialize the PII detector with Presidio analyzers and custom patterns."""
        # Load the small spacy model explicitly to avoid downloading large models
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to en_core_web_lg if sm not available
            nlp = spacy.load("en_core_web_lg")

        # Create NLP engine with the loaded model
        # Updated for newer Presidio API - models parameter instead of spacy_model
        nlp_engine = SpacyNlpEngine(models=[{"lang_code": "en", "model_name": "en_core_web_sm"}])
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

        # Add custom SSN recognizer
        ssn_patterns = [
            Pattern(name="SSN pattern 1", regex=r"\b\d{3}-\d{2}-\d{4}\b", score=0.9),
            Pattern(name="SSN pattern 2", regex=r"\b\d{3}\s\d{2}\s\d{4}\b", score=0.9),
            Pattern(name="SSN pattern 3", regex=r"\b\d{9}\b", score=0.6),
        ]
        ssn_recognizer = PatternRecognizer(
            supported_entity="US_SSN",
            patterns=ssn_patterns,
            context=["SSN", "social security", "social security number", "tax id"]
        )
        self.analyzer.registry.add_recognizer(ssn_recognizer)

        # Add custom credit card recognizer
        cc_patterns = [
            Pattern(name="Visa", regex=r"\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", score=0.9),
            Pattern(name="Mastercard", regex=r"\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", score=0.9),
            Pattern(name="Amex", regex=r"\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b", score=0.9),
            Pattern(name="Generic CC", regex=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", score=0.7),
        ]
        cc_recognizer = PatternRecognizer(
            supported_entity="CREDIT_CARD",
            patterns=cc_patterns,
            context=["credit card", "card", "visa", "mastercard", "amex", "cc"]
        )
        self.analyzer.registry.add_recognizer(cc_recognizer)

        self.anonymizer = AnonymizerEngine()

    def check_pii(self, text: str) -> Dict:
        """
        Detect PII in text and return sanitized version.

        Args:
            text: Original text (NOT normalized)

        Returns:
            Dictionary with:
                - detected: bool indicating if PII was found
                - entities: list of detected PII entities with metadata
                - sanitized: text with PII replaced by placeholders
        """
        if not text or not text.strip():
            return {
                "detected": False,
                "entities": [],
                "sanitized": text or ""
            }

        # Analyze text for PII entities
        analyzer_results = self.analyzer.analyze(
            text=text,
            language='en',
            return_decision_process=True
        )

        # Convert to our entity format
        entities = []
        for result in analyzer_results:
            entity_text = text[result.start:result.end]
            entities.append({
                "type": result.entity_type,
                "text": entity_text,
                "score": result.score,
                "start": result.start,
                "end": result.end
            })

        # Sort entities by start position for proper anonymization
        entities.sort(key=lambda x: x["start"])

        # Create anonymizer results and operators
        anonymizer_results = []
        operators = {}
        for result in analyzer_results:
            anonymizer_results.append(result)
            # Create operator config for this entity type
            operators[result.entity_type] = OperatorConfig(
                "replace",
                params={"new_value": f"<{result.entity_type}>"}
            )

        # Anonymize the text
        if anonymizer_results:
            anonymized_text = self.anonymizer.anonymize(
                text=text,
                analyzer_results=anonymizer_results,
                operators=operators
            ).text
        else:
            anonymized_text = text

        return {
            "detected": len(entities) > 0,
            "entities": entities,
            "sanitized": anonymized_text
        }


# Singleton instance
_detector_instance: Optional[PIIDetector] = None


def get_detector() -> PIIDetector:
    """Get or create the singleton PII detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = PIIDetector()
    return _detector_instance


def check_pii(text: str) -> Dict:
    """
    Main entry point for PII detection.

    Args:
        text: Original text (NOT normalized)

    Returns:
        Dictionary with detection results and sanitized text
    """
    detector = get_detector()
    return detector.check_pii(text)


# List of supported Presidio entity types
SUPPORTED_ENTITIES = {
    # US-specific
    "US_SSN": "US Social Security Number",
    "US_DRIVER_LICENSE": "US Driver's License",
    "US_PASSPORT": "US Passport",
    "US_BANK_NUMBER": "US Bank Account Number",
    "US_ITIN": "US Individual Taxpayer Identification Number",

    # UK-specific
    "UK_NINO": "UK National Insurance Number",
    "UK_PASSPORT": "UK Passport",

    # Other countries
    "IT_FISCAL_CODE": "Italian Fiscal Code",
    "IT_DRIVER_LICENSE": "Italian Driver's License",
    "IT_PASSPORT": "Italian Passport",
    "IT_VAT_CODE": "Italian VAT Code",
    "ES_NIF": "Spanish Tax Identification Number",
    "FR_NIF": "French Tax Identification Number",

    # Financial
    "CREDIT_CARD": "Credit Card Number",
    "IBAN_CODE": "International Bank Account Number",
    "IBAN": "International Bank Account Number",

    # Contact
    "EMAIL_ADDRESS": "Email Address",
    "PHONE_NUMBER": "Phone Number",

    # Personal
    "PERSON": "Person Name",
    "FIRST_NAME": "First Name",
    "LAST_NAME": "Last Name",
    "FULL_NAME": "Full Name",

    # Location
    "LOCATION": "Location",
    "ADDRESS": "Street Address",
    "CITY": "City",
    "REGION": "Region/State",
    "COUNTRY": "Country",
    "ZIP_CODE": "Postal/ZIP Code",

    # Identifiers
    "DATE_TIME": "Date/Time",
    "DATE_OF_BIRTH": "Date of Birth",
    "TIME": "Time",
    "URL": "URL/Link",
    "IP_ADDRESS": "IP Address",
    "DOMAIN": "Domain Name",

    # Technical
    "AWS_KEY": "AWS Access Key",
    "API_KEY": "API Key",
    "MEDICAL_LICENSE": "Medical License Number",
    "LICENSE_PLATE": "Vehicle License Plate",

    # Other
    "NRP": "National/Regional Passport",
    "ID": "General ID Number",
}


if __name__ == "__main__":
    # Quick test
    test_text = "My SSN is 123-45-6789 and email is john@example.com"
    result = check_pii(test_text)
    print(f"Original: {test_text}")
    print(f"Detected: {result['detected']}")
    print(f"Entities: {result['entities']}")
    print(f"Sanitized: {result['sanitized']}")
