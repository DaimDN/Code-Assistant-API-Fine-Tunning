from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
import fnmatch
import json
import uvicorn
from dotenv import load_dotenv
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

load_dotenv()

client = OpenAI()

app = FastAPI(
    title="Code Assistant API",
    description="An API that processes and analyzes codebases using GPT.",
    version="1.0.0",
    docs_url="/",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DirectoryRequest(BaseModel):
    directory_path: str
    file_patterns: List[str] = [
        "*.ts", "*.tsx", "*.jsx", "*.js", "*.html", "*.css", "*.scss", "*.sass", "*.less",
        "*.py", "*.java", "*.cpp", "*.c", "*.cs", "*.go", "*.rs", "*.rb", "*.php",
        "*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.conf",
        "*.md", "*.rst", "*.txt",
        "*.sh", "*.bash", "*.zsh", "*.fish",
        "*.sql", "*.graphql", "*.proto"
    ]
    exclude_patterns: List[str] = [
        "**/node_modules/**",
        "**/.git/**",
        "**/build/**",
        "**/dist/**",
        "**/.next/**",
        "**/venv/**",
        "**/__pycache__/**",
        "**/coverage/**",
        "*.min.js",
        "*.min.css",
        "*.map",
        "*.jpg", "*.jpeg", "*.png", "*.gif", "*.ico", "*.pdf",
        "package-lock.json",
        "yarn.lock",
        "poetry.lock"
    ]

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Code Assistant API Documentation",
        version="1.0.0",
        description="# Code Assistant API Developed by DaimDEV",
        routes=app.routes,
    )
    
    openapi_schema["components"]["examples"] = {
        "LoadDirectoryExample": {
            "value": {
                "directory_path": "/path/to/project",
                "file_patterns": ["*.py", "*.js", "*.tsx", "*.jsx", "*.ts"],
                "exclude_patterns": ["**/node_modules/**", "**/.git/**"]
            }
        },
        "QueryExample": {
            "value": {
                "query": "What are the main React components in this project?"
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema    

def match_file_patterns(file_path, patterns):
    for pattern in patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False

def read_project_structure(directory_request: DirectoryRequest):
    file_found = False
    file_data = []
    for root, dirs, files in os.walk(directory_request.directory_path):
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) for pattern in directory_request.exclude_patterns)]
        for file in files:
            file_path = os.path.join(root, file)
            if match_file_patterns(file_path, directory_request.file_patterns):
                file_found = True
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    file_data.append({
                        "file_name": file,
                        "file_path": os.path.relpath(file_path, directory_request.directory_path),
                        "file_content": file_content
                    })
                except IOError:
                    print(f"Error reading file {file_path}")
    
    if not file_found:
        print("No files matched the given patterns.")
    
    return file_data

def analyze_code_content(content):
    analysis = []
    lines = content.split('\n')
    
    current_block = []
    for line in lines:
        if line.strip().startswith('def ') or line.strip().startswith('class '):
            if current_block:
                analysis.append(' '.join(current_block))
            current_block = [line.strip()]
        elif line.strip() and current_block:
            current_block.append(line.strip())
    
    if current_block:
        analysis.append(' '.join(current_block))
    
    return '\n'.join(analysis)

def extract_js_functions(content):
    functions = []
    lines = content.split('\n')
    current_function = None
    function_body = []
    in_comment = False
    comment_buffer = []

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        if stripped_line.startswith('/*'):
            in_comment = True
            comment_buffer = [stripped_line]
            continue
        if in_comment:
            comment_buffer.append(stripped_line)
            if stripped_line.endswith('*/'):
                in_comment = False
            continue
        
        is_function = (
            'function ' in line or
            '=>' in line or
            stripped_line.startswith('const ') and '(' in line or
            stripped_line.startswith('let ') and '(' in line or
            stripped_line.startswith('var ') and '(' in line or
            stripped_line.startswith('async ') and 'function' in line
        )

        if is_function:
            if current_function:
                functions.append({
                    'name': current_function,
                    'body': '\n'.join(function_body),
                    'comments': '\n'.join(comment_buffer) if comment_buffer else ''
                })
            
            if 'function ' in line:
                current_function = line.split('function ')[1].split('(')[0].strip()
            elif '=>' in line:
                current_function = line.split('=')[0].strip()
            elif any(x in line for x in ['const ', 'let ', 'var ']):
                current_function = line.split('=')[0].split(' ')[1].strip()
            
            function_body = [line.strip()]
            comment_buffer = []
            
        elif current_function and stripped_line:
            function_body.append(line.strip())
            
            if stripped_line == '}' and len(function_body) > 1:
                functions.append({
                    'name': current_function,
                    'body': '\n'.join(function_body),
                    'comments': '\n'.join(comment_buffer) if comment_buffer else ''
                })
                current_function = None
                function_body = []
                comment_buffer = []

    if current_function:
        functions.append({
            'name': current_function,
            'body': '\n'.join(function_body),
            'comments': '\n'.join(comment_buffer) if comment_buffer else ''
        })

    return functions
def generate_usage_examples(content):
    examples = []
    lines = content.split('\n')
    
    for line in lines:
        if line.strip().startswith('def '):
            func_name = line.strip().split('def ')[1].split('(')[0]
            params = line.split('(')[1].split(')')[0]
            example = f"result = {func_name}({generate_param_examples(params)})"
            examples.append(example)
    
    return '\n\n'.join(examples)

def generate_param_examples(params):
    if not params.strip():
        return ""
    
    param_list = params.split(',')
    example_params = []
    
    for param in param_list:
        param = param.strip()
        if '=' in param:
            example_params.append(param.split('=')[1])
        else:
            if 'path' in param or 'file' in param:
                example_params.append('"example/path"')
            elif 'name' in param:
                example_params.append('"example_name"')
            elif 'id' in param:
                example_params.append('"123"')
            else:
                example_params.append('"example_value"')
    
    return ', '.join(example_params)

def generate_jsonl_data(file_data):
    jsonl_data = []
    for data in file_data:
        prompt = (
            f"File: {data['file_path']}\n"
            f"Please analyze the following code and describe all functions, classes, "
            f"and their purposes in detail:\n\n{data['file_content']}"
        )
        
        response = (
            f"This file contains the following code analysis:\n\n"
            f"1. File path: {data['file_path']}\n"
            f"2. Code content analysis:\n"
            f"{analyze_code_content(data['file_content'])}\n"
            f"3. Usage examples for any custom functions or classes found in the code.\n"
            f"4. The relationships between different components in the code."
        )
        
        training_examples = [
            {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response}
                ]
            },
            {
                "messages": [
                    {"role": "user", "content": f"What are the functions defined in {data['file_path']}?"},
                    {"role": "assistant", "content": f"Here are the functions defined in this file: {extract_js_functions(data['file_content'])}"}
                ]
            },
            {
                "messages": [
                    {"role": "user", "content": f"How do I use the functions in {data['file_path']}?"},
                    {"role": "assistant", "content": f"Here's how to use the functions: {extract_js_functions(data['file_content'])}"}
                ]
            },
            {
                "messages": [
                    {"role": "user", "content": f"code for {data['file_path']}?"},
                    {"role": "assistant", "content": f"Here is the code for {extract_js_functions(data['file_content'])}"}
                ]
            }
        ]
        
        jsonl_data.extend(training_examples)
    
    return jsonl_data


def save_as_jsonl(jsonl_data, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in jsonl_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

app.openapi = custom_openapi

@app.post("/preprocess")
async def load_directory(request: DirectoryRequest):
    try:
        file_data = read_project_structure(request)
        
        if not file_data:
            raise HTTPException(status_code=400, detail="No matching files found in the directory.")
        
        jsonl_data = generate_jsonl_data(file_data)
        
        output_file = 'data/preprocess.jsonl'
        
        save_as_jsonl(jsonl_data, output_file)
        
        return {"message": f"Data successfully saved to {output_file}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the directory: {str(e)}")


@app.post("/model/fine-tune")
async def fine_tune_model():
    try:
        file_path = "data/preprocess.jsonl"
        base_dir = os.path.dirname(os.path.realpath(__file__))
        full_path = os.path.join(base_dir, file_path)

        if not os.path.exists(full_path):
            raise HTTPException(status_code=400, detail=f"File not found: {full_path}")

        with open(full_path, 'rb') as file:
            upload_response = client.files.create(
                file=file,
                purpose="fine-tune"
            )
        
        fine_tune_response = client.fine_tuning.jobs.create(
            training_file=upload_response.id,
            model="gpt-3.5-turbo"
        )

        return {"message": f"Fine-tuning job created successfully with ID: {fine_tune_response.id}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during fine-tuning: {str(e)}")
    

@app.get("/model/job/{job_id}")
async def check_fine_tuning_job_status(job_id: str):
    try:
        job_status = client.fine_tuning.jobs.retrieve(job_id)
        
        response = {
            "job_id": job_id,
            "status": job_status.status,
            "created_at": job_status.created_at,
            "finished_at": job_status.finished_at if hasattr(job_status, 'finished_at') else None,
            "error": job_status.error if hasattr(job_status, 'error') else None,
            "model": job_status.fine_tuned_model if job_status.status == "succeeded" else None,
            "message": get_status_message(job_status.status)
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking job status: {str(e)}")

def get_status_message(status):
    messages = {
        "succeeded": "Fine-tuning job completed successfully.",
        "failed": "Fine-tuning job failed.",
        "cancelled": "Fine-tuning job was cancelled.",
        "pending": "Fine-tuning job is pending.",
        "running": "Fine-tuning job is currently running.",
        "validating_files": "Fine-tuning job is validating files.",
    }
    return messages.get(status, "Unknown status for fine-tuning job.")



class ModelQueryRequest(BaseModel):
    model_id: str
    prompt: str

client = OpenAI()

@app.post("/model/response")
async def query_model(request: ModelQueryRequest):
    try:
        response = client.chat.completions.create(
            model=request.model_id,
            messages=[{"role": "user", "content": request.prompt}],
            max_tokens=100
        )
        
        return {
            "model_id": request.model_id,
            "prompt": request.prompt,
            "response": response.choices[0].message.content
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying the model: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)