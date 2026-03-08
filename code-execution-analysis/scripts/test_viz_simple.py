import os
from google.genai import Client, types
from dotenv import load_dotenv

load_dotenv()

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

output_path = "output"
csv_path = "data/viz_data.csv"

# Upload existing CSV file
print("Uploading test data...")
uploaded_file = client.files.upload(file=csv_path)
print(f"File uploaded: {uploaded_file.name}")

prompt = f"""
Create 12 visualizations from the uploaded CSV data. Save each to '{output_path}' with names viz_01.png, viz_02.png, etc.

Data variables: region, product, segment, revenue, satisfaction, sessions, page_views, converted, device, month, subscription_tier

Create these 12 plots:
1. Line plot: revenue trends by month
2. Bar chart: average revenue by region  
3. Scatter plot: revenue vs sessions (color by segment)
4. Histogram: satisfaction distribution
5. Box plot: revenue by subscription_tier
6. Violin plot: satisfaction by product
7. Heatmap: correlation of revenue, satisfaction, sessions, page_views
8. Count plot: users by device
9. Pie chart: distribution by segment
10. Stacked bar: revenue by month (stack by product)
11. Swarm plot: satisfaction by subscription_tier
12. Joint plot: revenue vs satisfaction with marginals

Requirements:
- Figure size (10, 6)
- dpi=150
- Clear titles
- Professional colors (use viridis, magma, or tab10 palette)
- tight_layout() (except for joint plots)
- For swarm plot: if data is sparse, fall back to strip plot
- For joint plot: use plt.tight_layout() after calling plt.tight_layout()

Print a summary at the end showing which plots were successfully created.
"""

contents = [uploaded_file, prompt]

print("\nGenerating 12 visualizations...")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution())]
    ),
)

print(
    f"\nStatus: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}"
)

# Check results and save raw outputs
raw_output_dir = "data/raw_viz_output"
os.makedirs(raw_output_dir, exist_ok=True)

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
                        code_file = f"{raw_output_dir}/viz_code_block_{part_idx + 1}.py"
                        with open(code_file, "w", encoding="utf-8") as f:
                            f.write(part.executable_code.code or "")
                        print(f"Saved code to {code_file}")

                    # Save code execution result
                    elif (
                        hasattr(part, "code_execution_result")
                        and part.code_execution_result
                    ):
                        cer = part.code_execution_result
                        result_file = f"{raw_output_dir}/viz_result_{part_idx + 1}.txt"
                        with open(result_file, "w", encoding="utf-8") as f:
                            f.write(f"Outcome: {cer.outcome}\n\n")
                            if cer.output:
                                f.write("Output:\n")
                                f.write(cer.output)
                        print(f"\nExecution {part_idx}: {cer.outcome}")
                        if cer.output:
                            lines = cer.output.split("\n")
                            print(f"  {len(lines)} lines of output")

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
                            ext_map = {
                                "image/png": ".png",
                                "image/jpeg": ".jpg",
                            }
                            ext = ext_map.get(mime_type, ".bin")

                            data_file = (
                                f"{raw_output_dir}/viz_inline_data_{part_idx}{ext}"
                            )
                            with open(data_file, "wb") as f:
                                f.write(data)
                            print(f"Saved image to {data_file}")

print(f"\nDone! Check {raw_output_dir}/ for raw outputs (images, code, results)")
print(f"Note: Files are generated in remote execution environment, not locally.")
