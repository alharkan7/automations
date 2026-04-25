#!/usr/bin/env python3
"""Review CV PDFs using Gemini 2.5 Pro with resume capability."""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

RESULTS_FILE = Path(__file__).parent / "cv_review_results.json"

JOB_DESCRIPTION = """
Deskripsi Peran
Kami mencari Data Engineer yang berdedikasi untuk membangun, mengoptimalkan, dan memelihara arsitektur manajemen data perusahaan.
Anda akan bertanggung jawab untuk mengembangkan pipeline data yang skalabel, memastikan integritas data, serta menyediakan infrastruktur data yang andal untuk mendukung kebutuhan analisis bisnis dan tim Data Science.

*Tanggung Jawab Utama (Key Responsibilities)
- Desain & Pengembangan Pipeline: Merancang, membangun, dan memelihara sistem ETL/ELT yang kompleks untuk mengintegrasikan data dari berbagai sumber ke dalam Data Warehouse atau Data Lake.
- Arsitektur Data: Mengembangkan dan mengoptimalkan skema database serta model data (Data Modeling) guna mendukung skalabilitas dan performa kueri.
- Otomasi & Orkestrasi: Mengelola jadwal alur kerja data (workflow) menggunakan alat orkestrasi untuk menjamin ketersediaan data secara real-time maupun batch.
- Kualitas & Keamanan Data: Menerapkan pemantauan kualitas data (data profiling) serta memastikan seluruh proses kepatuhan terhadap kebijakan keamanan dan privasi data.
- Optimasi Performa: Melakukan pengujian, debugging, dan peningkatan performa sistem database maupun proses komputasi data besar (Big Data).
- Kolaborasi Lintas Fungsi: Bekerja sama dengan Data Scientist dan Business Analyst dalam menyediakan dataset yang siap digunakan untuk pemodelan analitik.

*Persyaratan Teknis (Technical Requirements)
- Pendidikan: Sarjana (S1) di bidang Ilmu Komputer, Teknik Informatika, Statistika, atau bidang kuantitatif terkait.
- Bahasa Pemrograman: Mahir dalam Python atau Scala, serta memiliki kemampuan SQL tingkat lanjut (Advanced SQL).
- Sistem Big Data: Pengalaman dalam menggunakan framework pemrosesan data besar seperti Apache Spark (PySpark/Spark SQL).
- Manajemen Database: Pemahaman mendalam mengenakan database relasional (PostgreSQL, MySQL) maupun non-relasional (NoSQL/Hadoop).
- Infrastruktur Cloud: Pengalaman operasional di lingkungan cloud (misalnya: AWS, Azure, atau Google Cloud Platform).
- Alat Orkestrasi: Familiar dengan alat pengelolaan alur kerja seperti Apache Airflow, Prefect, atau sejenisnya.
- Version Control: Terbiasa menggunakan Git (GitHub/GitLab) dalam siklus pengembangan perangkat lunak.

*Kualifikasi Tambahan (Preferred Qualifications)
- Memiliki sertifikasi profesional di bidang Data Engineering (misalnya: Google Professional Data Engineer, Azure Data Engineer Associate, atau Databricks Certified).
- Memahami konsep Containerization menggunakan Docker atau Kubernetes.
- Pengalaman bekerja dalam metodologi Agile/Scrum.

*Kompetensi Perilaku (Soft Skills)
- Kemampuan analisis dan pemecahan masalah yang kuat.
- Kemampuan komunikasi yang baik untuk menjelaskan konsep teknis kepada pemangku kepentingan non-teknis.
- Ketelitian tinggi terhadap detail dan kualitas data.
"""

EVALUATION_INSTRUCTIONS = """
Evaluate the candidate's CV against the Data Engineer job description above.

Provide your evaluation in the following JSON format (strict JSON only, no markdown):

{
  "score": <number from 1-100>,
  "experience_analysis": "<analysis of relevant experience>",
  "skills_analysis": "<analysis of technical skills>",
  "education_analysis": "<analysis of education>",
  "certifications_analysis": "<analysis of certifications>",
  "soft_skills_analysis": "<analysis of soft skills>",
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
  "recommendation": "<Strong Hire / Hire / Consider / Not Recommended>",
  "notes": "<detailed comments explaining the score and recommendation>"
}

Scoring Guidelines:
- 90-100: Exceptional fit - exceeds all requirements
- 75-89: Strong fit - meets most requirements with some strengths
- 60-74: Moderate fit - meets basic requirements with gaps
- 40-59: Weak fit - significant gaps in key areas
- Below 40: Not suitable - does not meet minimum requirements
"""

PROMPT = f"""You are an expert technical recruiter reviewing CVs for a Data Engineer position.

{JOB_DESCRIPTION}

{EVALUATION_INSTRUCTIONS}

Review the attached CV and provide your evaluation in JSON format.
"""


def load_existing_results():
    """Load existing results from JSON file."""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return []


def save_results(results):
    """Save results to JSON file immediately."""
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)


def get_processed_cv_codes(results):
    """Get set of CV codes that have been successfully processed."""
    return {r["cv_code"] for r in results if "evaluation" in r}


def review_cv(client, pdf_path: str, model_name: str = "gemini-2.5-pro"):
    """Review a single CV PDF using Gemini."""
    cv_name = Path(pdf_path).stem
    print(f"\nReviewing {cv_name}...")
    print(f"  Uploading {cv_name}.pdf...", flush=True)

    uploaded_file = client.files.upload(file=pdf_path)
    print(f"  Uploaded: {uploaded_file.name}", flush=True)

    print(f"  Sending to Gemini {model_name}...", flush=True)
    response = client.models.generate_content(
        model=model_name,
        contents=types.Content(
            parts=[
                types.Part.from_text(text=PROMPT),
                types.Part.from_uri(
                    file_uri=uploaded_file.uri,
                    mime_type=uploaded_file.mime_type,
                ),
            ]
        ),
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )

    return cv_name, response.text


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    client = genai.Client(api_key=api_key)

    # Load existing results
    results = load_existing_results()
    processed_codes = get_processed_cv_codes(results)

    # Find all CV PDFs
    cv_dir = Path(__file__).parent
    pdf_files = sorted(cv_dir.glob("CV *.pdf"))

    # Filter out already processed CVs
    remaining_files = [f for f in pdf_files if f.stem not in processed_codes]

    print(f"Total CV files: {len(pdf_files)}")
    print(f"Already processed: {len(processed_codes)}")
    print(f"Remaining to process: {len(remaining_files)}")

    if remaining_files:
        print(f"\nRemaining CVs: {[f.stem for f in remaining_files]}")

    for pdf_path in remaining_files:
        try:
            cv_name, evaluation = review_cv(client, str(pdf_path))

            # Create or update result
            result_entry = {
                "cv_code": cv_name,
                "evaluation": json.loads(evaluation),
            }

            # Update results list
            results.append(result_entry)

            # Save immediately after each CV
            save_results(results)
            print(f"  Saved result to {RESULTS_FILE}", flush=True)

            # Print summary
            score = result_entry["evaluation"]["score"]
            recommendation = result_entry["evaluation"]["recommendation"]
            print(f"  Score: {score}/100 - {recommendation}", flush=True)

        except Exception as e:
            print(f"  Error reviewing {pdf_path.name}: {e}", flush=True)
            # Save error state
            results.append({
                "cv_code": Path(pdf_path).stem,
                "error": str(e),
            })
            save_results(results)

    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    valid_results = [r for r in results if "evaluation" in r]
    error_results = [r for r in results if "error" in r]

    for result in results:
        cv_code = result["cv_code"]
        if "error" in result:
            print(f"{cv_code}: ERROR - {result['error']}")
        else:
            score = result["evaluation"]["score"]
            recommendation = result["evaluation"]["recommendation"]
            print(f"{cv_code}: {score}/100 - {recommendation}")

    # Sort by score and print ranking
    if valid_results:
        print("\n" + "=" * 60)
        print("RANKING BY SCORE")
        print("=" * 60)
        sorted_results = sorted(valid_results, key=lambda x: x["evaluation"]["score"], reverse=True)
        for i, result in enumerate(sorted_results, 1):
            cv_code = result["cv_code"]
            score = result["evaluation"]["score"]
            recommendation = result["evaluation"]["recommendation"]
            print(f"{i:2}. {cv_code}: {score}/100 - {recommendation}")


if __name__ == "__main__":
    main()
