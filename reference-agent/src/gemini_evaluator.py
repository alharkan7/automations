from __future__ import annotations

import json
import logging
import os

from google import genai
from google.genai import types

from .models import BatchEvaluation, EvaluationResult, PaperMetadata

logger = logging.getLogger(__name__)

MAX_GEMINI_REQUESTS = 50

EVALUATION_SYSTEM_PROMPT = """\
You are a strict academic relevance evaluator. You will be given a user's research \
context and a batch of academic papers. For EACH paper, decide whether it is \
highly relevant to the user's research context.

Rules:
- Only mark a paper as relevant (is_relevant: true) if it directly addresses \
the user's research topic, methods, or domain.
- Tangentially related papers should be marked as NOT relevant.
- Provide a brief rationale (1-2 sentences) for each decision.
- Return your response as a JSON array where each element has: \
"openalex_id", "title", "is_relevant" (boolean), "rationale" (string).
"""


def _format_paper_for_prompt(paper: PaperMetadata) -> str:
    abstract_snippet = (paper.abstract or "N/A")[:600]
    concepts_str = ", ".join(paper.concepts[:5]) if paper.concepts else "N/A"
    return (
        f"  ID: {paper.openalex_id}\n"
        f"  Title: {paper.title}\n"
        f"  Year: {paper.publication_year or 'N/A'}\n"
        f"  Citations: {paper.cited_by_count}\n"
        f"  Topic: {paper.primary_topic or 'N/A'}\n"
        f"  Concepts: {concepts_str}\n"
        f"  Source: {paper.source_name or 'N/A'}\n"
        f"  Authors: {', '.join(paper.authors[:3]) or 'N/A'}\n"
        f"  Institutions: {', '.join(paper.institutions[:3]) or 'N/A'}\n"
        f"  Abstract: {abstract_snippet}\n"
    )


class GeminiEvaluator:
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required. "
                "Set it in the Streamlit sidebar or as an environment variable."
            )
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.request_count = 0
        self.max_requests = MAX_GEMINI_REQUESTS

    @property
    def limit_reached(self) -> bool:
        return self.request_count >= self.max_requests

    def _generate(self, prompt: str, system_instruction: str | None = None) -> str:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        return response.text

    def evaluate_batch(
        self, user_context: str, papers: list[PaperMetadata]
    ) -> BatchEvaluation:
        if self.limit_reached:
            logger.warning("Gemini request safety limit reached (%d)", self.max_requests)
            return BatchEvaluation(evaluations=[])

        if not papers:
            return BatchEvaluation(evaluations=[])

        papers_block = "\n---\n".join(
            f"Paper {i + 1}:\n{_format_paper_for_prompt(p)}"
            for i, p in enumerate(papers)
        )

        prompt = (
            f"## User Research Context\n{user_context}\n\n"
            f"## Papers to Evaluate ({len(papers)} total)\n{papers_block}\n\n"
            "Evaluate each paper. Return a JSON array of objects with keys: "
            '"openalex_id", "title", "is_relevant", "rationale".'
        )

        try:
            text = self._generate(prompt, system_instruction=EVALUATION_SYSTEM_PROMPT)
            self.request_count += 1
            return self._parse_response(text, papers)
        except Exception as exc:
            logger.error("Gemini evaluation failed: %s", exc)
            self.request_count += 1
            return BatchEvaluation(evaluations=[])

    def _parse_response(
        self, response_text: str, papers: list[PaperMetadata]
    ) -> BatchEvaluation:
        try:
            raw = json.loads(response_text)
            if not isinstance(raw, list):
                raw = raw.get("evaluations", raw.get("results", []))

            paper_map = {p.openalex_id: p for p in papers}
            evaluations: list[EvaluationResult] = []

            for item in raw:
                oa_id = item.get("openalex_id", "")
                title = item.get("title", "")
                if not title and oa_id in paper_map:
                    title = paper_map[oa_id].title
                evaluations.append(
                    EvaluationResult(
                        openalex_id=oa_id,
                        title=title,
                        is_relevant=bool(item.get("is_relevant", False)),
                        rationale=item.get("rationale", "No rationale provided."),
                    )
                )
            return BatchEvaluation(evaluations=evaluations)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.error("Failed to parse Gemini response: %s", exc)
            return BatchEvaluation(evaluations=[])

    def extract_queries(self, research_context: str) -> list[str]:
        """Use Gemini to extract search queries from a longer research context."""
        if self.limit_reached:
            return []

        prompt = (
            "You are helping a researcher find relevant academic papers. "
            "Given the following research context, generate 3-5 concise search queries "
            "that would be effective for searching the OpenAlex academic database.\n\n"
            "Each query should be a short phrase (2-6 words) capturing a key aspect "
            "of the research.\n\n"
            f"## Research Context\n{research_context}\n\n"
            'Return a JSON array of strings, e.g. ["query one", "query two", ...]'
        )

        try:
            text = self._generate(prompt)
            self.request_count += 1
            queries = json.loads(text)
            if isinstance(queries, list):
                return [str(q) for q in queries if q]
            return []
        except Exception as exc:
            logger.error("Gemini query extraction failed: %s", exc)
            self.request_count += 1
            return []

    def expand_queries(self, user_context: str, previous_queries: list[str]) -> list[str]:
        """Generate new orthogonal search queries based on previous attempts."""
        if self.limit_reached:
            return []

        prompt = (
            "You are helping a researcher find more academic papers. "
            "The following search queries have already been used and are exhausted:\n"
            f"{json.dumps(previous_queries)}\n\n"
            "Given the original research context below, generate 2-4 NEW and DIFFERENT "
            "search queries. Use synonyms, related concepts, broader/narrower terms, "
            "or alternative phrasing that the previous queries did not cover.\n\n"
            f"## Research Context\n{user_context}\n\n"
            'Return a JSON array of strings, e.g. ["new query one", "new query two", ...]'
        )

        try:
            text = self._generate(prompt)
            self.request_count += 1
            queries = json.loads(text)
            if isinstance(queries, list):
                return [str(q) for q in queries if q]
            return []
        except Exception as exc:
            logger.error("Gemini query expansion failed: %s", exc)
            self.request_count += 1
            return []
