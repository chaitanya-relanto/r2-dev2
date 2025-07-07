from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.database_manager import operations as db_ops
from src.services.pr_summarizer.summarize import PRSummarizer

# --- Pydantic Models ---

class DBTicket(BaseModel):
    id: str
    title: str
    description: str
    status: str
    project_id: str
    project_name: Optional[str] = None
    assigned_to: str

class DBPullRequest(BaseModel):
    id: str
    title: str
    summary: str
    ticket_id: str
    author_id: str
    project_id: str

class DBUser(BaseModel):
    id: str
    name: str
    email: str
    role: str

class GitDiff(BaseModel):
    id: str
    diff_text: str
    pr_id: str
    summary: Optional[str] = None

class TicketWithPRs(BaseModel):
    ticket: DBTicket
    pull_requests: List[DBPullRequest]

class DBDocument(BaseModel):
    id: str
    title: str
    content: str
    type: str
    project_id: str
    project_name: Optional[str] = None

class DBLearning(BaseModel):
    id: str
    title: str
    summary: str
    tags: List[str]
    urls: List[str]

# --- API Router Setup ---

router = APIRouter()
pr_summarizer = PRSummarizer()

# --- API Endpoints ---

@router.get("/users/{user_id}/tickets", response_model=List[DBTicket], summary="Get all tickets for a user")
async def get_user_tickets(user_id: str):
    try:
        tickets_data = db_ops.get_tickets_by_user(user_id)
        return [DBTicket(**t) for t in tickets_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/users/{user_id}/tickets/open", response_model=List[DBTicket], summary="Get open tickets for a user")
async def get_user_open_tickets(user_id: str):
    try:
        tickets_data = db_ops.get_tickets_by_user(user_id, status="open")
        return [DBTicket(**t) for t in tickets_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/users/{user_id}/tickets/closed", response_model=List[DBTicket], summary="Get closed/done tickets for a user")
async def get_user_closed_tickets(user_id: str):
    try:
        tickets_data = db_ops.get_tickets_by_user(user_id, status="done")
        return [DBTicket(**t) for t in tickets_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/users/{user_id}/tickets/in-progress", response_model=List[DBTicket], summary="Get in-progress tickets for a user")
async def get_user_in_progress_tickets(user_id: str):
    try:
        tickets_data = db_ops.get_tickets_by_user(user_id, status="in progress")
        return [DBTicket(**t) for t in tickets_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/tickets/{ticket_id}/pull-requests", response_model=List[DBPullRequest], summary="Get pull requests for a ticket")
async def get_ticket_pull_requests(ticket_id: str):
    try:
        prs_data = db_ops.get_pull_requests_by_ticket(ticket_id)
        return [DBPullRequest(**pr) for pr in prs_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/pull-requests/{pr_id}/diff", response_model=GitDiff, summary="Get git diff for a pull request with AI summary")
async def get_pull_request_diff(pr_id: str):
    try:
        diff_data = db_ops.get_diff_by_pr(pr_id)
        if not diff_data:
            raise HTTPException(status_code=404, detail="Git diff not found for this PR")
        
        summary = pr_summarizer.summarize_diff(diff_data['diff_text'], session_id=f"pr_{pr_id}")
        diff_data['summary'] = summary
        return GitDiff(**diff_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/tickets/{ticket_id}/complete", response_model=TicketWithPRs, summary="Get ticket with associated PRs")
async def get_ticket_with_prs(ticket_id: str):
    try:
        # This endpoint makes two DB calls, which can be optimized later if needed
        tickets_data = db_ops.get_tickets_by_user(user_id=None, ticket_id=ticket_id) # This needs adjustment in ops
        if not tickets_data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        prs_data = db_ops.get_pull_requests_by_ticket(ticket_id)
        
        return TicketWithPRs(
            ticket=DBTicket(**tickets_data[0]),
            pull_requests=[DBPullRequest(**pr) for pr in prs_data]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/docs", response_model=List[DBDocument], summary="Get all documentation")
async def get_all_docs():
    try:
        docs_data = db_ops.get_docs()
        return [DBDocument(**d) for d in docs_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/docs/{doc_id}", response_model=DBDocument, summary="Get a specific document")
async def get_document(doc_id: str):
    try:
        docs_data = db_ops.get_docs(doc_id=doc_id)
        if not docs_data:
            raise HTTPException(status_code=404, detail="Document not found")
        return DBDocument(**docs_data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/projects/{project_id}/docs", response_model=List[DBDocument], summary="Get documents for a project")
async def get_project_docs(project_id: str):
    try:
        docs_data = db_ops.get_docs(project_id=project_id)
        return [DBDocument(**d) for d in docs_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/learning", response_model=List[DBLearning], summary="Get all learning resources")
async def get_all_learning():
    try:
        learning_data = db_ops.get_learnings()
        return [DBLearning(**l) for l in learning_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/learning/search", response_model=List[DBLearning], summary="Search learning resources by tag or title")
async def search_learning_resources(q: Optional[str] = None, tag: Optional[str] = None):
    try:
        learning_data = db_ops.get_learnings(q=q, tag=tag)
        return [DBLearning(**l) for l in learning_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/learning/{learning_id}", response_model=DBLearning, summary="Get a specific learning resource")
async def get_learning_resource(learning_id: str):
    try:
        learning_data = db_ops.get_learnings(learning_id=learning_id)
        if not learning_data:
            raise HTTPException(status_code=404, detail="Learning resource not found")
        return DBLearning(**learning_data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/users/{user_id}/info", response_model=DBUser, summary="Get user information")
async def get_user_info(user_id: str):
    try:
        user_data = db_ops.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        return DBUser(**user_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")