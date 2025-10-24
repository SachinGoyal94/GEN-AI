import json

def extract_flowchart(json_data, output_type="html"):
    """
    Extract a clean flowchart from CrewAI JSON output.

    Args:
        json_data (dict): JSON returned from CrewAI backend
        output_type (str): "html" for full HTML, "mermaid" for only Mermaid code

    Returns:
        str: Clean, formatted HTML or Mermaid code
    """
    try:
        if output_type == "html":
            # Full HTML from HTML Renderer task (usually tasks_output[2])
            html_raw = json_data["html"]["tasks_output"][2]["raw"]
            # Remove triple backticks
            if html_raw.startswith("```html"):
                html_clean = html_raw[len("```html"):].rstrip("`")
            elif html_raw.startswith("```"):
                html_clean = html_raw[3:].rstrip("`")
            else:
                html_clean = html_raw
            # Replace escaped newlines with real newlines
            html_clean = html_clean.replace("\\n", "\n").strip()
            return html_clean

        elif output_type == "mermaid":
            # Mermaid code from Flowchart Designer task (usually tasks_output[1])
            mermaid_raw = json_data["html"]["tasks_output"][1]["raw"]
            # Remove triple backticks
            if mermaid_raw.startswith("```mermaid"):
                mermaid_clean = mermaid_raw[len("```mermaid"):].rstrip("`")
            else:
                mermaid_clean = mermaid_raw
            # Replace escaped newlines with real newlines
            mermaid_clean = mermaid_clean.replace("\\n", "\n").strip()
            return mermaid_clean

        else:
            raise ValueError("output_type must be 'html' or 'mermaid'")

    except Exception as e:
        print("Error extracting flowchart:", e)
        return None

# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    # Load your JSON output (replace 'output.json' with your file)
    with open("output.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Get full HTML
    html_flowchart = extract_flowchart(json_data, output_type="html")
    with open("flowchart.html", "w", encoding="utf-8") as f:
        f.write(html_flowchart)
    print("Saved full HTML flowchart as flowchart.html")

    # Optional: get only Mermaid code
    mermaid_code = extract_flowchart(json_data, output_type="mermaid")
    print("\n--- Mermaid Code ---\n")
    print(mermaid_code)
