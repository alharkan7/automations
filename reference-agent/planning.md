# Reference Agent - System Planning Document

## 1. Project Overview
The `reference-agent` is an intelligent autonomous system designed to augment literature reviews and research discovery. It takes user input (ranging from simple keywords to comprehensive research backgrounds) and iteratively interacts with the OpenAlex API to retrieve academic literature. An LLM (Gemini) strictly evaluates each retrieved paper's relevance, and the system autonomously refines search terms and paginates through results until a predefined quota of highly relevant literature is met or safety limits are reached.

## 2. Proposed Metadata for LLM Evaluation
Beyond the standard **Title**, **Keywords**, and **Abstract**, OpenAlex provides rich metadata that can significantly improve the LLM's relevance scoring and filtering. We propose passing the following additional metadata points to Gemini:

*   **Concepts / Topics (OpenAlex Subfields):** Helps the LLM understand the precise academic domains of the paper.
*   **Publication Year:** Useful for filtering out outdated research if the user implies a need for state-of-the-art literature.
*   **Cited-by Count:** Provides a proxy for the paper's influence and academic consensus, which the LLM can weigh when deciding between borderline papers.
*   **Author Affiliations / Primary Institutions:** Useful for identifying seminal work from leading labs.
*   **Source / Journal Name & Open Access Status:** Good for downstream availability checks (e.g., if the user wants to read full texts later).
*   **Relevance Score from OpenAlex API:** If available, passing the initial relevance weight.

## 3. Core System Architecture & Workflow

The system functions primarily as a highly robust **Retrieval-Evaluator Loop**.

### Step 1: Input Processing & Query Generation
*   **Input Acceptance:** Accepts either (1) short queries, or (2) full research documents.
*   **LLM Extraction (if needed):** If the input is a full research background, the LLM first summarizes the core context and extracts optimal initial search queries (keywords/phrases) tailored for the OpenAlex API.

### Step 2: OpenAlex Retrieval
*   **API Calls:** Queries the OpenAlex `/works` endpoint utilizing the extracted keywords.
*   **Pagination State:** Keeps track of the current `cursor` or `page` to continually pull new batches of literature.

### Step 3: LLM Relevance Evaluation
*   **Data Preparation:** The backend formats the retrieved batch into a concise JSON or Markdown structure, including the proposed metadata (Title, Abstract, Concepts, Year, Citations).
*   **Prompting:** Gemini is prompted with the original user context and the batch of papers to evaluate. It outputs a boolean `is_relevant` flag for each paper and a brief rationale.
*   **Result Aggregation:** Papers deemed relevant are saved into the final "Approved Collection".

### Step 4: Autonomous Query Refinement & Pagination
*   **Pagination Logic:** If the evaluated batch yields fewer approved papers than the minimum target (e.g., Target: 20, Current: 5), the system automatically requests the next page from OpenAlex.
*   **Re-Querying Logic (Query Expansion):** If the OpenAlex results for current keywords run out (no more pages) *before* reaching the target output count:
    *   The system feeds the previous query and user context back to Gemini.
    *   Gemini generates **new, orthogonal or broader keywords/synonyms**.
    *   The retrieval process restarts with the new query.
*   **Deduplication:** A cache (Set) of `OpenAlex IDs` is maintained to guarantee the LLM does not evaluate the same paper twice across altered queries.

### Step 5: Termination Conditions
The loop ends when **ANY** of the following conditions are met:
1.  **Quota Met:** The predefined number of highly relevant papers (e.g., 20) is successfully curated.
2.  **Exhaustion:** The LLM cannot generate any more meaningful synonymous queries.
3.  **Safety Limits:** Maximum API limits (OpenAlex requests or Gemini maximum defined token limits) are reached to prevent runaway infinite loops.

## 4. Proposed Application State & Classes

To implement this efficiently, we should structure the Python application with the following core components:

*   `UserContext`: Holds original user query and target paper count.
*   `QueryManager`: Tracks search history, generates initial queries via Gemini, and handles query expansion.
*   `OpenAlexClient`: Manages HTTP requests, pagination (cursor), and rate limits.
*   `GeminiEvaluator`: Constructs the evaluation prompts, parses the structured output from Gemini, and handles token counting.
*   `AgentOrchestrator`: The main loop coordinating the extraction, retrieval, evaluation, and pagination processes.

## 5. UI & Interaction Design

To provide visibility and allow user control over the autonomous loop, we will implement an interactive UI (e.g., using **Streamlit** or **Gradio**, which are well-suited for agentic applications).

### Key Components:
*   **Input Section:** A dual-input area (short keywords vs. long research context) and a settings panel for parameters like Target Quota (e.g., 20 papers).
*   **Real-time Visibility Console:** A live-updating log window in the UI showing the exact state of the agent:
    *   *Example:* "Fetching page 1 from OpenAlex..." ➜ "Gemini evaluating 25 papers..." ➜ "8 approved, 12 needed. Fetching page 2..."
*   **Interactive Retry & Human-in-the-Loop:**
    *   **Query Approval & Step Retry:** Before firing the OpenAlex API, the UI displays the Gemini-extracted or expanded keywords. The user can manually edit them, retry the generation step, or approve to proceed.
    *   **Evaluation Retry:** If the LLM's relevance evaluation on a batch appears unsatisfactory, the user can trigger a retry on that specific batch evaluation.
    *   **Manual Pruning:** A final review table is presented where the user can visually inspect the approved collection and uncheck any false positives before finalizing the export.

## 6. Output Format Strategy

A crucial requirement is ensuring the generated output is not ignored by Git (our global `.gitignore` currently ignores `*.csv` and `*.xlsx`). To ensure the final structured data is trackable, readable, and reusable, we will standardize the output to the following formats:

1.  **JSON (`.json`):** The primary data structure containing all metadata, abstracts, OpenAlex IDs, and Gemini's evaluation rationale. JSON is natively trackable in Git and easily parsable for downstream conversion (e.g., transforming into BibTeX for Zotero/Mendeley).
2.  **Markdown Report (`.md`):** A human-readable summary document that elegantly lists the selected papers, their links, and why they were chosen.

**Git Tracking Strategy:** We will create a `reference-agent/results/` directory using a `.gitkeep_results` identifier to maintain directory structure. Outputting strictly as `.json` and `.md` implicitly bypasses the global `.csv` and `.xlsx` ignoring rules.

## 7. Next Steps for Implementation
1.  **Initialize Project:** Setup project environment (e.g., `requests`, `google-generativeai`, `pydantic`, `streamlit`). We might consider using `langchain` or `langgraph` if state management gets complex, though standard Python is fine for MVP.
2.  **API Client Draft:** Write the `OpenAlexClient` wrapper to handle fetching and parsing raw data into our Metadata schema.
3.  **LLM Evaluator Draft:** Write the structured prompt (using Gemini's `response_schema`/`json` mode) that takes a user query and paper metadata, returning standardized relevance assessments.
4.  **Loop Logic Integration:** Assemble the `AgentOrchestrator` while putting strict safety safeguards on the autonomous loop.
5.  **UI Development:** Build the Streamlit/Gradio frontend that wraps the `AgentOrchestrator`, exposing visibility logs and enabling the human-in-the-loop retry points.
