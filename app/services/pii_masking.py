# from presidio_analyzer import AnalyzerEngine
# from presidio_anonymizer import AnonymizerEngine

# # Initialize engines once (efficient)
# analyzer = AnalyzerEngine()
# anonymizer = AnonymizerEngine()


# def mask_pii(text: str) -> str:
#     results = analyzer.analyze(
#         text=text,
#         entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON"],
#         language="en"
#     )

#     anonymized_text = anonymizer.anonymize(
#         text=text,
#         analyzer_results=results
#     )

#     return anonymized_text.text



from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def mask_pii(text: str) -> str:
    results = analyzer.analyze(
        text=text,
        entities=["EMAIL_ADDRESS", "PHONE_NUMBER"],
        language="en"
    )

    anonymized_text = anonymizer.anonymize(
        text=text,
        analyzer_results=results
    )

    return anonymized_text.text