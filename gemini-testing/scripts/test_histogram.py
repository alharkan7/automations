import os
from google.genai import Client, types
from dotenv import load_dotenv

load_dotenv()

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

output_path = "output"
csv_path = "data/viz_data.csv"

# Upload the CSV file
print("Uploading CSV data...")
uploaded_file = client.files.upload(file=csv_path)
print(f"File uploaded: {uploaded_file.name}")

prompt = f"""
Create a simple histogram visualization from the uploaded CSV data.

The CSV has these variables: user_id, date, region, product, segment, revenue, cost, margin, satisfaction, nps_score, sessions, page_views, time_on_site, converted, churned, device, browser, campaign, hour, day_of_week, month, bounce_rate, click_rate, subscription_tier, age_group

Create a histogram for the 'satisfaction' variable showing its distribution.

Requirements:
- Figure size (10, 6)
- Include KDE overlay (kernel density estimate)
- Use professional color (e.g., 'steelblue' or matplotlib default)
- Clear title: 'Distribution of Satisfaction Scores'
- X-axis label: 'Satisfaction Score'
- Y-axis label: 'Frequency'
- Save to '{output_path}/' with filename 'histogram_satisfaction.png'
- Use dpi=150
- Use plt.tight_layout()

Just create this one histogram and confirm it was saved successfully.
"""

# Include both the file and the text prompt in contents
contents = [uploaded_file, prompt]

print("\nGenerating histogram...")
print("=" * 60)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution())]
    ),
)

print("\nFull Response:")
print("=" * 60)
print(response.text)

print("\n" + "=" * 60)
print("Checking for code execution results...")

# Check for code execution results
if hasattr(response, "candidates") and response.candidates:
    for candidate in response.candidates:
        if (
            hasattr(candidate, "content")
            and candidate.content
            and hasattr(candidate.content, "parts")
        ):
            parts = candidate.content.parts
            if parts:
                for part_idx, part in enumerate(parts):
                    # Save executable code
                    if hasattr(part, "executable_code") and part.executable_code:
                        code_file = f"data/histogram_code_block_{part_idx + 1}.py"
                        code_content = (
                            part.executable_code.code
                            if part.executable_code.code
                            else ""
                        )
                        with open(code_file, "w", encoding="utf-8") as f:
                            f.write(code_content)
                        print(f"\nSaved executable code to {code_file}")

                    # Save code execution result
                    elif (
                        hasattr(part, "code_execution_result")
                        and part.code_execution_result
                    ):
                        cer = part.code_execution_result
                        result_file = f"data/histogram_result_{part_idx + 1}.txt"
                        with open(result_file, "w", encoding="utf-8") as f:
                            f.write(f"Outcome: {cer.outcome}\n\n")
                            if cer.output:
                                f.write("Output:\n")
                                f.write(cer.output)
                        print(f"\nCode execution result {part_idx + 1}:")
                        print(f"  Outcome: {cer.outcome}")
                        if cer.output:
                            lines = cer.output.split("\n")
                            print(f"  Output ({len(lines)} lines)")
                            for line in lines[:20]:
                                print(f"    {line}")
                            if len(lines) > 20:
                                print(f"    ... ({len(lines) - 20} more lines)")

                    # Save inline data (images)
                    elif (
                        hasattr(part, "inline_data")
                        and part.inline_data
                        and part.inline_data.mime_type
                        and part.inline_data.data
                    ):
                        inline_data = part.inline_data
                        mime_type = inline_data.mime_type or "application/octet-stream"
                        data = inline_data.data

                        if data:
                            # Determine file extension based on MIME type
                            ext_map = {
                                "image/png": ".png",
                                "image/jpeg": ".jpg",
                            }
                            ext = ext_map.get(mime_type, ".bin")

                            data_file = f"{output_path}/histogram_from_gemini{ext}"
                            with open(data_file, "wb") as f:
                                f.write(data)
                            print(f"\nSaved image to {data_file}")

print("\n" + "=" * 60)
print("Histogram generation complete.")

# Check if file exists
if os.path.exists(f"{output_path}/histogram_from_gemini.png"):
    print(f"\nSUCCESS: Histogram created at {output_path}/histogram_from_gemini.png")
else:
    print(f"\nFAILED: Histogram not found at {output_path}/histogram_from_gemini.png")
