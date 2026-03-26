# Gemini File Search cost report — `library_inventory.json` corpus

This report estimates the cost of using Google’s **Gemini File Search** (managed RAG) for every file listed in `library_inventory.json` under `al-library/`. It is based on Google’s published documentation (as of the report date) and local measurements against the paths recorded in that inventory.

**Primary sources**

- [File Search](https://ai.google.dev/gemini-api/docs/file-search) (overview, limits, pricing subsection)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) (embeddings, “Pricing for tools” table)

---

## 1. How File Search is billed (official)

File Search imports, chunks, and indexes documents so Gemini can retrieve relevant passages at query time. Google separates **indexing** costs from **storage** and **query-time retrieval mechanics**, but **chat usage** still consumes model tokens.

| Component | Billing (paid tier, per docs) |
|-----------|-------------------------------|
| **Indexing (initial ingest)** | Charged for **embeddings** at the **`gemini-embedding-001`** rate: **$0.15 per 1 million tokens**. |
| **Storage** | **Free of charge** (indexed material in the File Search store). |
| **Query-time search / retrieval embeddings** | **Free of charge** (per File Search pricing section). |
| **Using the model with File Search** | **Retrieved document tokens are charged as regular model input (context) tokens** at the rates for whichever Gemini model you use. |

Indexing is described as using **`gemini-embedding-001`** in the File Search “How it works” section. There is **no separate per-gigabyte upload fee** for File Search itself; the main managed-RAG line item is **embedding token volume at index time**, then **normal generateContent pricing** when you ask questions.

The [pricing tools table](https://ai.google.dev/gemini-api/docs/pricing#pricing-for-tools) states for File Search (paid tier): charged for embeddings at **$0.15 / 1M tokens**; retrieved tokens follow model pricing.

---

## 2. Limits that affect this library

From [File Search → Limitations](https://ai.google.dev/gemini-api/docs/file-search#limitations):

| Limit | Value |
|--------|--------|
| **Maximum size per document** | **100 MB** |
| **Total File Search store usage per project (by tier)** | **Free: 1 GB** · **Tier 1: 10 GB** · **Tier 2: 100 GB** · **Tier 3: 1 TB** |
| **Operational guidance** | Google recommends keeping each store **under ~20 GB** for retrieval latency. |

**Backend size accounting:** Google notes that the enforced store size is based on **input plus embeddings stored**, and is **typically about 3× the size of your raw input data**.

**Implication for this corpus:** Total on-disk size for inventoried files is **~860 MB** (see §3). Rough backend accounting **≈ 3 × 0.86 GB ≈ 2.6 GB**, which **exceeds the free-tier 1 GB project cap** for File Search stores. In practice you should plan for a **paid tier with sufficient File Search quota** (e.g. **Tier 1 / 10 GB** minimum) unless you split projects, delete material, or shrink the corpus.

All inventoried files were verified **under 100 MB** per file.

---

## 3. Inventory summary (`library_inventory.json`)

The inventory’s `summary` block and a full filesystem check of `file_path` entries yield:

| Metric | Value |
|--------|--------|
| **Total files** | **146** |
| **PDF** | **107** |
| **EPUB** | **39** |
| **Total size on disk** | **901,490,916 bytes (~860 MiB)** |
| **PDF total size** | **~638 MiB** |
| **EPUB total size** | **~222 MiB** |

**By top-level folder (from JSON summary):**

| Folder | Count |
|--------|------:|
| Lib 1 - Asus | 88 |
| Lib 4 - Mac | 30 |
| Lib 3 - Dell | 22 |
| Lib 2 - SEA Today | 4 |
| Papers | 2 |

**PDF page count:** **33,717 pages** across all 107 PDFs (measured with `pypdf`).

**Largest files by byte size (examples):** include large EPUBs (e.g. on the order of **~81 MiB** and **~57 MiB**) and large PDFs (e.g. **~44 MiB**, **~41 MiB**). None exceed the **100 MB** per-document API limit.

---

## 4. EPUB and supported formats

[Supported file types](https://ai.google.dev/gemini-api/docs/file-search#supported-file-types) include **`application/pdf`** and many Office and text MIME types. **`application/epub+zip` (EPUB) is not listed** as a supported type.

**Workflow assumption (as requested):** EPUBs (and any other unsupported types) should be **converted to PDF or another supported format** before upload. Google does not charge a separate “conversion fee” in File Search; conversion is your own tooling/compute. **Indexing cost tracks text (tokens) extracted after upload**, not the original EPUB byte size.

**Note:** PDFs produced from EPUB are often **larger in bytes** than the EPUB (layout, fonts, images), which affects **quota math (~3× input)** more than it maps linearly to **embedding dollars** (same book text ≈ similar token count).

---

## 5. Chunking and what “tokens” means for indexing

On import, files are **chunked**, **embedded**, and **indexed**. You can tune chunk size and overlap via [`chunking_config`](https://ai.google.dev/gemini-api/docs/file-search#chunking-configuration) (e.g. `max_tokens_per_chunk`, `max_overlap_tokens`).

**Billing impact:** Each chunk is embedded; **overlapping regions are embedded in multiple chunks**, so **billed embedding tokens at index time are typically somewhat higher** than a single naive pass over “unique” plain text. A rough scaling factor for illustration: if chunks are ~200 tokens with ~20-token overlap, step ≈ 180 tokens, multiplier ≈ **200/180 ≈ 1.11×** vs. non-overlapping segmentation (actual defaults and behavior should be confirmed in your SDK/API version).

---

## 6. Estimating one-time indexing cost (embeddings)

Google charges **$0.15 / 1M tokens** for the embedding input used during indexing (aligned with **`gemini-embedding-001`** paid pricing).

**Important:** Exact token counts use **Google’s tokenizer**, not a homegrown rule. The estimates below use **reproducible heuristics** so you can bound cost; treat them as **order-of-magnitude**, not an invoice.

### 6.1 EPUB text volume (39 files)

Rough method: read EPUB as ZIP, decode `.xhtml` / `.html` / `.htm`, strip tags with a regex, concatenate text.

| Metric | Value |
|--------|--------|
| **Approx. total characters** | **~31,209,801** |
| **Tokens (heuristic: chars ÷ 4)** | **~7.8M** |
| **Indexing cost at $0.15 / 1M tokens (no overlap adjustment)** | **~$1.17** |

### 6.2 PDF text volume (107 files, 33,717 pages)

Full text extraction for every page of every PDF was prohibitively slow on a few very large or complex PDFs in this library. Instead:

- A **stratified random sample of 18 PDFs** (by file size: small / medium / large) was processed with `pypdf`.
- **Mean extractable text ≈ 1,456 characters per page** (sample average).
- Scaled to **33,717** total pages.

| Metric | Value |
|--------|--------|
| **Extrapolated characters** | **≈ 49.1M** |
| **Tokens (heuristic: chars ÷ 4)** | **≈ 12.3M** |
| **Indexing cost at $0.15 / 1M tokens (no overlap adjustment)** | **≈ $1.84** |

**Sample caveats:** The sample included **image-heavy PDFs with ~0 extractable text** (e.g. some “deck”-style PDFs) and **text-dense books with very high chars/page**. The true corpus likely sits between “mostly scanned, little text” (lower indexing cost, weaker RAG) and “dense digital text” (higher cost).

### 6.3 Combined estimate (single index of full library after EPUB → PDF)

After conversion, you index **each book once** (not EPUB bytes + PDF bytes as separate logical books unless you duplicate). Combining the EPUB-derived token estimate with the PDF extrapolation:

| Stage | Tokens (heuristic) | Cost @ $0.15/M (no overlap) |
|-------|-------------------:|----------------------------:|
| EPUB content (as future PDF text) | ~7.8M | ~$1.17 |
| Existing PDF content | ~12.3M | ~$1.84 |
| **Subtotal** | **~20.1M** | **~$3.02** |
| **With ~1.11× overlap illustration** | **~22.3M** | **~$3.35** |

**Planning range:** **~$3–$5** one-time indexing on paid embedding pricing is a reasonable **order-of-magnitude** for this library **if** most PDFs are normal text (not huge unscanned image-only volumes). Wide PDF variance can push this lower (little extractable text) or higher (denser layout, more tokens per page than the sample).

### 6.4 Free tier note

Documentation lists File Search under free tier as **“Free of charge”** in the tools table, but **project File Search store size limits** still apply. At **~860 MB** raw input and **~3×** backend accounting, this corpus **likely does not fit the free 1 GB File Search store quota** for a single project without changes.

---

## 7. Ongoing costs (queries)

There is **no separate per-query File Search surcharge** in the sense of a second billable “search API.” Instead:

- You pay **normal Gemini model rates** for **prompt + output** tokens.
- **Chunks retrieved into the context** are billed as **standard input / context tokens** for that model (per File Search pricing text).

So monthly cost depends entirely on **how many questions you ask**, **which model**, **prompt length**, and **how much retrieved text** is injected—not on a fixed “per search” line item from File Search.

---

## 8. Re-indexing and updates

If you **replace or re-import** documents, **new or changed chunks** will incur **embedding charges again** for the work done to index them. Storage of the store remains **free** per current docs; operational limits and **~3×** size accounting still apply.

---

## 9. Summary table

| Topic | Takeaway |
|-------|----------|
| **Indexing** | **~$0.15 / 1M embedding tokens** (paid); **~$3–$5** heuristic one-time for this 146-file library. |
| **Storage** | **Free**; **project store quota** by tier; **~3×** input typical for enforced size. |
| **This library vs free 1 GB** | **Likely over free tier** once **~3×** accounting is applied to **~860 MB** raw input. |
| **EPUB** | **Not in supported MIME list**; **convert to PDF** (or other supported type) before upload. |
| **Queries** | **Retrieved text = model input tokens**; cost scales with **model choice and usage**. |
| **Per-file limit** | **100 MB**; **all current inventory files** were under this limit. |

---

## 10. Methodology notes (reproducibility)

- **Inventory:** `al-library/library_inventory.json` — `files[].file_path`, `extension`, `summary`.
- **Sizes / existence:** `pathlib.Path.stat()` on each `file_path`.
- **PDF pages:** `pypdf.PdfReader` page count for all PDFs.
- **EPUB chars:** ZIP + regex HTML strip on `*.xhtml` / `*.html` / `*.htm`.
- **PDF text extrapolation:** stratified sample of 18 PDFs, mean chars/page × 33,717.

Re-run analyses after updating the inventory or converting EPUBs to PDF if you need numbers tied to **post-conversion** file sets.

---

*Report generated for the `al-library` automation folder. Pricing and limits are defined by Google and may change; confirm current values on the official documentation pages linked above.*
