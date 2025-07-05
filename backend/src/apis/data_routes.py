from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.utils.database import get_engine
from src.services.pr_summarizer.summarize import PRSummarizer

# --- Database Models ---

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

# Get database engine
db_engine = get_engine()

# Initialize PR Summarizer
pr_summarizer = PRSummarizer()

# --- Database-driven API Endpoints ---

@router.get("/users/{user_id}/tickets", response_model=List[DBTicket], summary="Get all tickets for a user")
async def get_user_tickets(user_id: str):
    """
    Get all tickets assigned to a specific user.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT 
                    jt.id, jt.title, jt.description, jt.status, 
                    jt.project_id, jt.assigned_to, p.name as project_name
                FROM jira_tickets jt 
                JOIN projects p ON jt.project_id = p.id 
                WHERE jt.assigned_to = :user_id
                ORDER BY jt.status, jt.title
            """)
            result = connection.execute(query, {"user_id": user_id})
            tickets = []
            for row in result:
                tickets.append(DBTicket(
                    id=str(row.id),
                    title=row.title,
                    description=row.description,
                    status=row.status,
                    project_id=str(row.project_id),
                    project_name=row.project_name,
                    assigned_to=str(row.assigned_to)
                ))
            return tickets
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/users/{user_id}/tickets/open", response_model=List[DBTicket], summary="Get open tickets for a user")
async def get_user_open_tickets(user_id: str):
    """
    Get all open tickets assigned to a specific user.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT 
                    jt.id, jt.title, jt.description, jt.status, 
                    jt.project_id, jt.assigned_to, p.name as project_name
                FROM jira_tickets jt 
                JOIN projects p ON jt.project_id = p.id 
                WHERE jt.assigned_to = :user_id AND LOWER(jt.status) = 'open'
                ORDER BY jt.title
            """)
            result = connection.execute(query, {"user_id": user_id})
            tickets = []
            for row in result:
                tickets.append(DBTicket(
                    id=str(row.id),
                    title=row.title,
                    description=row.description,
                    status=row.status,
                    project_id=str(row.project_id),
                    project_name=row.project_name,
                    assigned_to=str(row.assigned_to)
                ))
            return tickets
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/users/{user_id}/tickets/closed", response_model=List[DBTicket], summary="Get closed/done tickets for a user")
async def get_user_closed_tickets(user_id: str):
    """
    Get all closed/done tickets assigned to a specific user.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT 
                    jt.id, jt.title, jt.description, jt.status, 
                    jt.project_id, jt.assigned_to, p.name as project_name
                FROM jira_tickets jt 
                JOIN projects p ON jt.project_id = p.id 
                WHERE jt.assigned_to = :user_id AND LOWER(jt.status) = 'done'
                ORDER BY jt.title
            """)
            result = connection.execute(query, {"user_id": user_id})
            tickets = []
            for row in result:
                tickets.append(DBTicket(
                    id=str(row.id),
                    title=row.title,
                    description=row.description,
                    status=row.status,
                    project_id=str(row.project_id),
                    project_name=row.project_name,
                    assigned_to=str(row.assigned_to)
                ))
            return tickets
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/users/{user_id}/tickets/in-progress", response_model=List[DBTicket], summary="Get in-progress tickets for a user")
async def get_user_in_progress_tickets(user_id: str):
    """
    Get all in-progress tickets assigned to a specific user.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT 
                    jt.id, jt.title, jt.description, jt.status, 
                    jt.project_id, jt.assigned_to, p.name as project_name
                FROM jira_tickets jt 
                JOIN projects p ON jt.project_id = p.id 
                WHERE jt.assigned_to = :user_id AND LOWER(jt.status) = 'in progress'
                ORDER BY jt.title
            """)
            result = connection.execute(query, {"user_id": user_id})
            tickets = []
            for row in result:
                tickets.append(DBTicket(
                    id=str(row.id),
                    title=row.title,
                    description=row.description,
                    status=row.status,
                    project_id=str(row.project_id),
                    project_name=row.project_name,
                    assigned_to=str(row.assigned_to)
                ))
            return tickets
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/tickets/{ticket_id}/pull-requests", response_model=List[DBPullRequest], summary="Get pull requests for a ticket")
async def get_ticket_pull_requests(ticket_id: str):
    """
    Get all pull requests associated with a specific ticket.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT pr.id, pr.title, pr.summary, pr.ticket_id, pr.author_id, pr.project_id
                FROM pull_requests pr
                WHERE pr.ticket_id = :ticket_id
                ORDER BY pr.title
            """)
            result = connection.execute(query, {"ticket_id": ticket_id})
            pull_requests = []
            for row in result:
                pull_requests.append(DBPullRequest(
                    id=str(row.id),
                    title=row.title,
                    summary=row.summary,
                    ticket_id=str(row.ticket_id),
                    author_id=str(row.author_id),
                    project_id=str(row.project_id)
                ))
            return pull_requests
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/pull-requests/{pr_id}/diff", response_model=GitDiff, summary="Get git diff for a pull request with AI summary")
async def get_pull_request_diff(pr_id: str):
    """
    Get the git diff for a specific pull request with an AI-generated summary.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT gd.id, gd.diff_text, gd.pr_id
                FROM git_diffs gd
                WHERE gd.pr_id = :pr_id
            """)
            result = connection.execute(query, {"pr_id": pr_id})
            row = result.first()
            if not row:
                raise HTTPException(status_code=404, detail="Git diff not found for this PR")
            
            # Generate summary using the PR summarizer
            summary = pr_summarizer.summarize_diff(row.diff_text, session_id=f"pr_{pr_id}")
            
            return GitDiff(
                id=str(row.id),
                diff_text=row.diff_text,
                pr_id=str(row.pr_id),
                summary=summary
            )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/tickets/{ticket_id}/complete", response_model=TicketWithPRs, summary="Get ticket with associated PRs")
async def get_ticket_with_prs(ticket_id: str):
    """
    Get a ticket along with all its associated pull requests.
    """
    try:
        with db_engine.connect() as connection:
            # Get ticket info
            ticket_query = text("""
                SELECT 
                    jt.id, jt.title, jt.description, jt.status, 
                    jt.project_id, jt.assigned_to, p.name as project_name
                FROM jira_tickets jt 
                JOIN projects p ON jt.project_id = p.id 
                WHERE jt.id = :ticket_id
            """)
            ticket_result = connection.execute(ticket_query, {"ticket_id": ticket_id})
            ticket_row = ticket_result.first()
            
            if not ticket_row:
                raise HTTPException(status_code=404, detail="Ticket not found")
            
            ticket = DBTicket(
                id=str(ticket_row.id),
                title=ticket_row.title,
                description=ticket_row.description,
                status=ticket_row.status,
                project_id=str(ticket_row.project_id),
                project_name=ticket_row.project_name,
                assigned_to=str(ticket_row.assigned_to)
            )
            
            # Get associated PRs
            pr_query = text("""
                SELECT pr.id, pr.title, pr.summary, pr.ticket_id, pr.author_id, pr.project_id
                FROM pull_requests pr
                WHERE pr.ticket_id = :ticket_id
                ORDER BY pr.title
            """)
            pr_result = connection.execute(pr_query, {"ticket_id": ticket_id})
            pull_requests = []
            for pr_row in pr_result:
                pull_requests.append(DBPullRequest(
                    id=str(pr_row.id),
                    title=pr_row.title,
                    summary=pr_row.summary,
                    ticket_id=str(pr_row.ticket_id),
                    author_id=str(pr_row.author_id),
                    project_id=str(pr_row.project_id)
                ))
            
            return TicketWithPRs(ticket=ticket, pull_requests=pull_requests)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/docs", response_model=List[DBDocument], summary="Get all documentation")
async def get_all_docs():
    """
    Get all documentation from the database.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT 
                    d.id, d.title, d.content, d.type, 
                    d.project_id, p.name as project_name
                FROM documents d
                JOIN projects p ON d.project_id = p.id
                ORDER BY d.type, d.title
            """)
            result = connection.execute(query)
            documents = []
            for row in result:
                documents.append(DBDocument(
                    id=str(row.id),
                    title=row.title,
                    content=row.content,
                    type=row.type,
                    project_id=str(row.project_id),
                    project_name=row.project_name
                ))
            return documents
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/docs/{doc_id}", response_model=DBDocument, summary="Get a specific document")
async def get_document(doc_id: str):
    """
    Get a specific document by ID.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT 
                    d.id, d.title, d.content, d.type, 
                    d.project_id, p.name as project_name
                FROM documents d
                JOIN projects p ON d.project_id = p.id
                WHERE d.id = :doc_id
            """)
            result = connection.execute(query, {"doc_id": doc_id})
            row = result.first()
            
            if not row:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return DBDocument(
                id=str(row.id),
                title=row.title,
                content=row.content,
                type=row.type,
                project_id=str(row.project_id),
                project_name=row.project_name
            )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/projects/{project_id}/docs", response_model=List[DBDocument], summary="Get documents for a project")
async def get_project_docs(project_id: str):
    """
    Get all documents for a specific project.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT 
                    d.id, d.title, d.content, d.type, 
                    d.project_id, p.name as project_name
                FROM documents d
                JOIN projects p ON d.project_id = p.id
                WHERE d.project_id = :project_id
                ORDER BY d.type, d.title
            """)
            result = connection.execute(query, {"project_id": project_id})
            documents = []
            for row in result:
                documents.append(DBDocument(
                    id=str(row.id),
                    title=row.title,
                    content=row.content,
                    type=row.type,
                    project_id=str(row.project_id),
                    project_name=row.project_name
                ))
            return documents
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/learning", response_model=List[DBLearning], summary="Get all learning resources")
async def get_all_learning():
    """
    Get all learning resources from the database.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT id, title, summary, tags, urls
                FROM learnings
                ORDER BY title
            """)
            result = connection.execute(query)
            learnings = []
            for row in result:
                learnings.append(DBLearning(
                    id=str(row.id),
                    title=row.title,
                    summary=row.summary,
                    tags=row.tags or [],
                    urls=row.urls or []
                ))
            return learnings
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/learning/{learning_id}", response_model=DBLearning, summary="Get a specific learning resource")
async def get_learning_resource(learning_id: str):
    """
    Get a specific learning resource by ID.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT id, title, summary, tags, urls
                FROM learnings
                WHERE id = :learning_id
            """)
            result = connection.execute(query, {"learning_id": learning_id})
            row = result.first()
            
            if not row:
                raise HTTPException(status_code=404, detail="Learning resource not found")
            
            return DBLearning(
                id=str(row.id),
                title=row.title,
                summary=row.summary,
                tags=row.tags or [],
                urls=row.urls or []
            )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/learning/search", response_model=List[DBLearning], summary="Search learning resources by tag or title")
async def search_learning_resources(q: Optional[str] = None, tag: Optional[str] = None):
    """
    Search learning resources by title/summary or by tag.
    """
    try:
        with db_engine.connect() as connection:
            if tag:
                # Search by tag
                query = text("""
                    SELECT id, title, summary, tags, urls
                    FROM learnings
                    WHERE :tag = ANY(tags)
                    ORDER BY title
                """)
                result = connection.execute(query, {"tag": tag})
            elif q:
                # Search by title or summary
                query = text("""
                    SELECT id, title, summary, tags, urls
                    FROM learnings
                    WHERE LOWER(title) LIKE LOWER(:search_term) 
                       OR LOWER(summary) LIKE LOWER(:search_term)
                    ORDER BY title
                """)
                result = connection.execute(query, {"search_term": f"%{q}%"})
            else:
                # Return all if no search parameters
                query = text("""
                    SELECT id, title, summary, tags, urls
                    FROM learnings
                    ORDER BY title
                """)
                result = connection.execute(query)
            
            learnings = []
            for row in result:
                learnings.append(DBLearning(
                    id=str(row.id),
                    title=row.title,
                    summary=row.summary,
                    tags=row.tags or [],
                    urls=row.urls or []
                ))
            return learnings
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/users/{user_id}/info", response_model=DBUser, summary="Get user information")
async def get_user_info(user_id: str):
    """
    Get information about a specific user.
    """
    try:
        with db_engine.connect() as connection:
            query = text("""
                SELECT id, name, email, role
                FROM users
                WHERE id = :user_id
            """)
            result = connection.execute(query, {"user_id": user_id})
            row = result.first()
            
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            
            return DBUser(
                id=str(row.id),
                name=row.name,
                email=row.email,
                role=row.role
            )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")