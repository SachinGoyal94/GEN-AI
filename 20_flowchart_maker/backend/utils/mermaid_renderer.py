def wrap_mermaid_in_html(mermaid_code: str) -> str:
    """Wrap Mermaid syntax in minimal HTML with CDN-based Mermaid renderer."""
    return f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Flowchart Output</title>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
    </script>
    <style>
      body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 30px; }}
      .mermaid {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
    </style>
  </head>
  <body>
    <h2>🧩 Generated Flowchart</h2>
    <div class="mermaid">
      {mermaid_code}
    </div>
  </body>
</html>
"""
