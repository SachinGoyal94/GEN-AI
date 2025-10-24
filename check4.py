import requests
import urllib.parse

url = "https://plantumlgen.pythonanywhere.com/generate_uml"
uml_text = """
@startuml GCD_LCM_Flowchart

title Algorithm to Find GCD and LCM of Two Numbers

start

:Input two numbers (a, b);

if (a == 0 or b == 0?) then (yes)
  :Error: One or both numbers are zero;
  stop
else (no)
  :Initialize temp_a = a, temp_b = b;
  while (temp_b != 0)
    :temp = temp_b;
    :temp_b = temp_a % temp_b;
    :temp_a = temp;
  endwhile
  :GCD = temp_a;
  :LCM = (a * b) / GCD;
  :Output GCD and LCM;
  stop
endif

@enduml
"""
encoded_text = urllib.parse.quote(uml_text)  # Encode the UML text
params = {"uml_text": encoded_text}
response = requests.get(url, params=params)

import os
if response.status_code == 200:
    with open("diagram_code.png", "wb") as f:
        f.write(response.content)
        print("✅ Diagram saved as diagram.png")