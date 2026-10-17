"""Asset Intelligence Copilot backend."""
import os

# No external tracing is authorized for private prompts/history.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
