import os
from google.genai import Client, types
from dotenv import load_dotenv

load_dotenv()

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

csv_path = "data/ab_testing_data.csv"

# Upload the local CSV file to Gemini's file storage
print(f"Uploading {csv_path}...")
uploaded_file = client.files.upload(file=csv_path)
print(f"File uploaded: {uploaded_file.name}")
print(f"  URI: {uploaded_file.uri}")
print(f"  Display name: {uploaded_file.display_name}")
print(f"  MIME type: {uploaded_file.mime_type}")

output_path = "output"

# Create the content with the uploaded file reference
prompt = f"""
Analyze the A/B testing data from the uploaded CSV file.

The data contains A/B testing results with the following variables:
- user_id: Unique user identifier
- group: Test group ('A' for control, 'B' for treatment)
- conversion: Binary conversion status (0 or 1)
- time_on_page: Time spent on page in seconds
- click_count: Number of clicks
- session_duration: Total session duration in minutes
- bounce_rate: Bounce rate (0-1)
- page_views: Number of pages viewed

Perform a comprehensive statistical analysis including:
1. Descriptive statistics for all numerical variables
2. Correlation matrix between all numerical variables
3. Group comparisons (Control A vs Treatment B):
   - Conversion rate comparison with statistical significance test
   - Mean comparison for time_on_page, session_duration, bounce_rate
   - T-tests for key metrics
4. Regression analysis predicting conversion
5. Data visualization: Create plots showing:
   - Conversion rate by group
   - Distribution of time_on_page by group
   - Correlation heatmap
   - Scatter plots of key relationships

Save all results, visualizations, and outputs to the '{output_path}' folder.
"""

# Include both the file and the text prompt in contents
contents = [uploaded_file, prompt]

print("\nRunning Gemini Code Execution analysis...")
print("=" * 60)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution())]
    ),
)

print("\nText Response:")
print("=" * 60)
print(response.text)

print("\n" + "=" * 60)
print("Checking for code execution results and saving raw output...")

# Create data directory for raw output
raw_output_dir = "data/raw_output"
os.makedirs(raw_output_dir, exist_ok=True)

# Save the full text response
text_content = response.text if response.text else ""
with open(f"{raw_output_dir}/full_text_response.txt", "w", encoding="utf-8") as f:
    f.write(text_content)
print(f"Saved full text response to {raw_output_dir}/full_text_response.txt")

# Check for code execution results and save raw data
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
                        code_file = f"{raw_output_dir}/code_block_{part_idx + 1}.py"
                        code_content = (
                            part.executable_code.code
                            if part.executable_code.code
                            else ""
                        )
                        with open(code_file, "w", encoding="utf-8") as f:
                            f.write(code_content)
                        print(f"Saved executable code to {code_file}")

                    # Save code execution result output
                    elif (
                        hasattr(part, "code_execution_result")
                        and part.code_execution_result
                    ):
                        cer = part.code_execution_result
                        result_file = (
                            f"{raw_output_dir}/execution_result_{part_idx + 1}.txt"
                        )
                        with open(result_file, "w", encoding="utf-8") as f:
                            f.write(f"Outcome: {cer.outcome}\n\n")
                            if cer.output:
                                f.write("Output:\n")
                                f.write(cer.output)
                        print(f"Saved code execution result to {result_file}")
                        print(f"  Outcome: {cer.outcome}")
                        if cer.output:
                            lines = cer.output.split("\n")
                            print(f"  Output ({len(lines)} lines, showing first 20):")
                            for line in lines[:20]:
                                print(f"    {line}")
                            if len(lines) > 20:
                                print(f"    ... ({len(lines) - 20} more lines)")

                    # Save inline data (images, CSVs, etc.)
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
                            extension_map = {
                                "image/png": ".png",
                                "image/jpeg": ".jpg",
                                "text/csv": ".csv",
                                "application/json": ".json",
                            }
                            ext = extension_map.get(mime_type, ".bin")

                            data_file = (
                                f"{raw_output_dir}/inline_data_{part_idx + 1}{ext}"
                            )
                            with open(data_file, "wb") as f:
                                f.write(data)
                            print(f"Saved inline data to {data_file} ({mime_type})")

print("\n" + "=" * 60)
print("Analysis complete.")
print(f"All raw outputs saved to {raw_output_dir}/")
