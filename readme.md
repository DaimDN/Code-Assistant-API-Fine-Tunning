# Code Assistant API

Welcome to the **Code Assistant API**, a tool designed to analyze and process
codebases using AI powered by GPT. This API helps developers understand codebase
structures, generate usage examples, and fine-tune models based on
project-specific data.

## Overview

- **Title**: Code Assistant API
- **Description**: An API that processes and analyzes codebases using GPT.
- **Version**: 1.0.0
- **Documentation**: Available at `/` (Swagger UI) and `/redoc` (ReDoc).

## Features

- **Project Structure Analysis**: Scan directories for specific file types,
  excluding certain patterns, to gather code data.
- **Code Analysis**: Breaks down code into functions, classes, and usage
  examples.
- **AI Integration**: Uses OpenAI's GPT for detailed code understanding and
  response generation.
- **Fine-Tuning Support**: Fine-tune models with project-specific data for
  better performance.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/DaimDN/Code-Assistant-API-Fine-Tunning
   cd Code-Assistant-API-Fine-Tunning
   ```

2. **Set up the environment:** Ensure Python 3.8+ is installed. Create and
   activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:** Copy `.env.example` to `.env` and add your OpenAI
   API key:
   ```bash
   cp .env.example .env
   ```

## Usage

### Running the Server

To run the FastAPI server:

```bash
python main.py
```

### Endpoints

- **POST /preprocess**  
  Description: Load and preprocess code from a directory.  
  Request body:

  ```json
  {
  	"directory_path": "/path/to/project",
  	"file_patterns": ["*.py", "*.js"],
  	"exclude_patterns": ["**/node_modules/**"]
  }
  ```

- **POST /model/fine-tune**  
  Description: Initiate a fine-tuning job using preprocessed data.

- **GET /model/job/{job_id}**  
  Description: Check the status of a fine-tuning job.

- **POST /model/response**  
  Description: Query the fine-tuned model with a prompt.  
  Request body:
  ```json
  {
  	"model_id": "ft:gpt-3.5-turbo-0123456",
  	"prompt": "What are the main Python functions in this module?"
  }
  ```

## Project Structure

- `main.py`: Main application file running FastAPI server.
- `data/`: Directory for storing preprocessed data (jsonl files).
- `.env`: Environment variables, including API keys.

## Notes

- Ensure you have the necessary permissions and API keys to use OpenAI services.
- The CORS middleware is configured to allow all origins for development
  purposes. Adjust it for production.

## License

This project is licensed under the MIT License. See the LICENSE.md file for
details.

## Acknowledgments

- FastAPI for the robust framework.
- OpenAI for the AI services integration.

```

```
