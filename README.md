# AI SQL Assistant (LangChain + Ollama + Streamlit)

Ask questions about a local SQLite sales database in plain English. SQL is generated locally using Ollama; no paid LLM API key is required.

## Architecture

```text
ai_sql_assistant/
├── app.py                  # Streamlit UI
├── sql_assistant.py        # Schema context, SQL generation, validation, execution
├── setup_database.py       # Creates and seeds sales.db
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── data/
    └── .gitkeep            # sales.db is generated here
```

## Requirements
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running
- A model pulled locally, for example `llama3:8b`

> You can use `codellama` if it is already installed, but a current code model such as `llama3:8b` is a reasonable starting point.

## Run on Windows PowerShell

```powershell
# 1. Open this folder in VS Code / PowerShell
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install Python packages
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Start Ollama in another terminal if it is not already running
ollama serve

# 4. Download the model (run once)
ollama pull llama3:8b

# 5. Create the sample database
python setup_database.py

# 6. Start the app
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`).

## Example questions
- Which product generated the highest revenue?
- What was total revenue by product?
- Show monthly revenue for 2025.
- Which products have fewer than 20 units in stock?

## Safety notes
- This starter only permits a single read-only `SELECT` query.
- SQL is checked before execution, and the database connection uses SQLite read-only mode.
- The UI displays the generated SQL before execution; review it before clicking **Run query**.
- SQL checks are defense-in-depth, not a complete security boundary. Use a least-privilege database account, row limits, query timeouts, access controls, and human approval for production data.
- Do not expose this app publicly without authentication and additional security review.
