import os
import json
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# --- Pydantic Response Models ---

class Task(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    assignee: str
    created_at: str
    due_date: str

class PullRequest(BaseModel):
    id: int
    title: str
    diff_text: str

class Document(BaseModel):
    filename: str
    preview: str

class LearningResource(BaseModel):
    id: int
    title: str
    category: str
    url: str
    summary: str
    tags: List[str]

# --- API Router Setup ---

router = APIRouter()

# Define base directory for data files, relative to the project root
DATA_DIR = Path("data")
TASKS_FILE = DATA_DIR / "tasks.json"
PULL_REQUESTS_FILE = DATA_DIR / "mock_diff.txt"
DOCS_DIR = DATA_DIR / "docs"
LEARNING_RESOURCES_FILE = DATA_DIR / "learning.json"

# --- API Endpoints ---

@router.get("/tasks", response_model=List[Task], summary="Get all tasks")
async def get_tasks():
    """
    Loads and returns all tasks from `data/tasks.json`.
    """
    if not TASKS_FILE.exists():
        raise HTTPException(status_code=404, detail="Tasks data file not found.")
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

@router.get("/pull_requests", response_model=List[PullRequest], summary="Get all pull requests")
async def get_pull_requests():
    """
    Loads PR diffs from `data/mock_diff.txt`, parses them, and returns structured data.
    """
    if not PULL_REQUESTS_FILE.exists():
        raise HTTPException(status_code=404, detail="Pull requests data file not found.")
    
    with open(PULL_REQUESTS_FILE, "r") as f:
        content = f.read()

    diffs = content.strip().split('---')
    pull_requests = []

    # Fake titles corresponding to the generated diffs
    titles = [
        "Feat: Implement JWT token verification",
        "Fix: Correct user profile image path",
        "Refactor: Modernize API client with interceptors",
        "Docs: Update README with setup instructions",
        "Test: Add slugify utility function tests"
    ]

    for i, diff_text in enumerate(diffs):
        diff_text_stripped = diff_text.strip()
        if not diff_text_stripped:
            continue

        pr_title = titles[i] if i < len(titles) else f"Unnamed Pull Request {i + 1}"
        
        pull_requests.append(
            PullRequest(id=i, title=pr_title, diff_text=diff_text_stripped)
        )
    return pull_requests

@router.get("/docs", response_model=List[Document], summary="Get all documentation files")
async def get_docs():
    """
    Reads all markdown files from `data/docs/` and returns their filename and a preview.
    """
    if not DOCS_DIR.is_dir():
        raise HTTPException(status_code=404, detail="Docs directory not found.")
    
    documents = []
    for filename in sorted(os.listdir(DOCS_DIR)):
        if filename.endswith(".md"):
            file_path = DOCS_DIR / filename
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Generate a preview from the first 1-2 paragraphs
            paragraphs = content.split('\n\n')
            preview_text = "\n\n".join(paragraphs[:2]).strip()
            
            documents.append(Document(filename=filename, preview=preview_text))
            
    return documents

@router.get("/learning_resources", response_model=List[LearningResource], summary="Get all learning resources")
async def get_learning_resources():
    """
    Loads and returns all learning resources from `data/learning.json`.
    """
    if not LEARNING_RESOURCES_FILE.exists():
        raise HTTPException(status_code=404, detail="Learning resources file not found.")
    with open(LEARNING_RESOURCES_FILE, "r") as f:
        return json.load(f) 