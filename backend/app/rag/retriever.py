from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass
class RetrievedChunk:
    text: str
    page: int
    source: str = "Northwind_Employee_Handbook_TEST.pdf"

_FACTS = [
    ("performance review", "Performance reviews are conducted twice a year: a mid-year review in June and an annual review in December.", 4),
    ("1-on-1", "You can book a 1-on-1 session with HR for a Performance Review, Career Discussion, or Benefits Consultation.", 5),
    ("pto", "Employees receive 24 days of paid time off per year. Up to 10 days may be carried over.", 6),
    ("carry over", "Up to 10 days of PTO can be carried over to the next year.", 6),
    ("health insurance", "The health insurance sum insured is INR 5,00,000 per family.", 7),
    ("insurance", "The health insurance sum insured is INR 5,00,000 per family.", 7),
    ("probation", "The probation period is 90 days.", 2),
    ("remote", "Employees may work remotely up to 3 days per week.", 3),
    ("hotel", "The hotel limit in a metro city is INR 8,000 per night.", 10),
]

class HandbookRetriever:
    """Small deterministic retriever with optional Chroma-backed documents."""
    def __init__(self, vectorstore=None):
        self.vectorstore = vectorstore

    def search(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        if self.vectorstore:
            docs = self.vectorstore.similarity_search(query, k=k)
            return [RetrievedChunk(d.page_content, int(d.metadata.get("page", 1)), d.metadata.get("source", "handbook")) for d in docs]
        lowered = query.lower()
        scored = [(sum(1 for token in re.findall(r"\w+", key) if token in lowered), text, page) for key, text, page in _FACTS]
        hits = sorted((row for row in scored if row[0] > 0), reverse=True)
        return [RetrievedChunk(text, page) for _, text, page in hits[:k]]

