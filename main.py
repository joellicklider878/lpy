# main.py
import os
import sys
import requests #standard asynchronous requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lpyc import run_lpy

app = FastAPI(title="Lpy IDE Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompileRequest(BaseModel):
    source: str

@app.post("/compile")
def compile_code(request: CompileRequest):
    #initialize variables cleanly
    python_code = "# compilation not attempted"
    
    try:
        print(f"--- Received payload to compile ---\n{request.source}\n------------------")
        
        # 1. Compile the clause using your compiler
        python_code = run_lpy(request.source)
        print(f"--- Compiled Python Code Output ---\n{python_code}\n------------------")

        # Fallback check if run_lpy returns None or empty
        if python_code is None or str(python_code).strip() == "" or python_code == "None": 
            python_code = f"# Warning: run_lpy returned empty output."
            return {
                "python": python_code,
                "output": "execution skipped because compiler returned empty code.",
                "errors": ["Compiler error: run_lpy did not output any Python code strings."]
        }
        # 2. Call headless LM studio to execute the python code
        url = "http://localhost:11434/v1/chat/completions"
        # openai chat format payload structure        
        data = {
            "model": "qwen3:0.6b",
            "messages": [
                {"role": "user", "content": f"execute or process this code:\n{python_code}"}
            ],
            "temperature": 0.2
        }
        
        # Synchronous request execution with a timeout
        response = requests.post(url, json=data, timeout=45)
        response.raise_for_status()
        result = response.json()
        
        # 3. Extract the response text from LM studio payload safely
        lm_output = ""
        if isinstance(result, dict) and "choices" in result:
            choices_list = result["choices"]
            if isinstance(choices_list, list) and len(choices_list) > 0:
                first_choice = choices_list[0]
                if isinstance(first_choice, dict):
                    lm_output = first_choice.get("message", {}).get("content", "")
            
            # fallback if text extraction yieled nothing
            if not lm_output:
                lm_output = str(result)

        # clean JSON BLOCK
        return {
            "python": python_code,
            "output": lm_output,
            "errors": []
        }
        
    except requests.exceptions.Timeout as e:
        print(f"Ollama Generation Timeout: {e}")
        # FIX: Changed "python_code" to "python"
        return {
            "python": str(python_code),
            "output": "",
            "errors": ["Error: LM Studio took too long to respond."]
        }       
    except requests.exceptions.RequestException as e:
        print(f"Ollama connection error: {e}")
        # FIX: Changed "python_code" to "python"
        return {
            "python": str(python_code),
            "output": "",
            "errors": [f"Failed to connect to LM studio: {str(e)}"]
        }
    except Exception as e:
        print(f"Critical backend error: {str(e)}")
        # FIX: Changed "python_code" to "python"
        return {
            "python": str(python_code),
            "output": "",
            "errors": [f"Backend Compiler Server Error: {str(e)}"]
    }
    
@app.get("/", response_class=HTMLResponse)
def get_ide():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()

        # cache buster
        import time
        cache_buster = f"<script>// Version ID: {int(time.time())}</script></body>"
        return html_content.replace("</body>", cache_buster)
    return "<h1>index.html not found. Save your html5 markup as index.html next to main.py</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
