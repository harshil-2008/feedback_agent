import os
from pathlib import Path

# Create project directory structure
project_root = Path(r"C:/Users/Harshil/.gemini/antigravity-ide/scratch/feedback_agent")
folders = [
    project_root / "data_ingestion_service" / "adapters",
    project_root / "storage",
    project_root / "nlp",
    project_root / "scheduler",
    project_root / "api",
    project_root / "frontend",
]
for f in folders:
    os.makedirs(f, exist_ok=True)
print("Project directories created.")
