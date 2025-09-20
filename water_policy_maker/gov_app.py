# gov_app.py
import gradio as gr, os, re
from gov_crew import crew

def run_pipeline(files, problem):
    if not problem:
        return "❌ Enter a policy problem", None
    inputs = {"policy_problem": problem, "files": files}
    result = crew.kickoff(inputs=inputs)
    text = str(result)
    fname = re.sub(r"[^\w\d-]", "_", problem)[:50] + ".md"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(text)
    return text, fname

with gr.Blocks() as demo:
    gr.Markdown("## 🏛 Policy Crew")
    files = gr.File(file_types=[".csv",".xlsx",".txt"], file_count="multiple", label="Upload files")
    problem = gr.Textbox(label="Policy Problem", placeholder="e.g., Reduce groundwater depletion")
    btn = gr.Button("Run Crew")
    out = gr.Textbox(label="Output", lines=20)
    download = gr.File(label="Download", visible=False)

    def click(f, p):
        txt, fname = run_pipeline(f, p)
        if fname:
            return txt, gr.File.update(value=fname, visible=True)
        return txt, gr.File.update(visible=False)

    btn.click(click, [files, problem], [out, download])

if __name__ == "__main__":
    demo.launch()
