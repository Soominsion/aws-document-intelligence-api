import os
import re
from functools import lru_cache

from app.config import settings


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def rule_based_summary(text: str) -> str:
    cleaned_text = _clean_text(text)
    if not cleaned_text:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", cleaned_text)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    if len(cleaned_text) <= settings.min_text_length_for_model:
        return cleaned_text

    if not sentences:
        return cleaned_text[:300]

    summary = " ".join(sentences[:3])
    return summary[:500].strip()


@lru_cache(maxsize=1)
def _get_summarization_pipeline():
    try:
        os.environ.setdefault("HF_HOME", settings.huggingface_home)

        from transformers import pipeline

        return pipeline("summarization", model=settings.summarization_model)
    except Exception:
        return None


def summarize_text(text: str) -> tuple[str, str]:
    cleaned_text = _clean_text(text)

    if len(cleaned_text) < settings.min_text_length_for_model:
        return rule_based_summary(cleaned_text), "rule_based"

    summarizer = _get_summarization_pipeline()
    if summarizer is None:
        return rule_based_summary(cleaned_text), "rule_based"

    try:
        result = summarizer(
            cleaned_text,
            max_length=settings.max_summary_length,
            min_length=settings.min_summary_length,
            do_sample=False,
        )
        summary = result[0]["summary_text"].strip()
        if not summary:
            return rule_based_summary(cleaned_text), "rule_based"
        return summary, "huggingface"
    except Exception:
        return rule_based_summary(cleaned_text), "rule_based"
