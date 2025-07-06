from typing import List, Literal, Optional

from sqlalchemy import text
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

from src.services.database_manager.connection import get_db_session
from src.utils.logger import get_logger


logger = get_logger(__name__)

def create_chat_session(user_id: str, title: str) -> str:
    """Creates a new chat session and returns the session ID."""
    db_session = get_db_session()
    try:
        result = db_session.execute(
            text("INSERT INTO chat_sessions (user_id, title) VALUES (:user_id, :title) RETURNING id"),
            {"user_id": user_id, "title": title}
        ).fetchone()
        if not result:
            raise Exception("Failed to create a new session.")
        session_id = str(result[0])
        db_session.commit()
        return session_id
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error creating chat session: {e}", exc_info=True)
        raise
    finally:
        db_session.close()

def store_message(session_id: str, user_id: str, role: Literal["user", "assistant"], message: str):
    """Stores a chat message in the database."""
    db_session = get_db_session()
    try:
        db_session.execute(
            text("INSERT INTO chat_messages (session_id, user_id, role, message) VALUES (:session_id, :user_id, :role, :message)"),
            {"session_id": session_id, "user_id": user_id, "role": role, "message": message}
        )
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error storing message: {e}", exc_info=True)
        raise
    finally:
        db_session.close()

def get_sessions(user_id: str) -> List[dict]:
    """Retrieves all chat sessions for a user."""
    db_session = get_db_session()
    try:
        results = db_session.execute(
            text("SELECT id as session_id, title, created_at FROM chat_sessions WHERE user_id = :user_id ORDER BY created_at DESC"),
            {"user_id": user_id}
        ).fetchall()
        return [
            {"session_id": str(row.session_id), "title": row.title, "created_at": row.created_at}
            for row in results
        ]
    finally:
        db_session.close()

def get_messages(session_id: str) -> List[dict]:
    """Retrieves all messages for a given session."""
    db_session = get_db_session()
    try:
        results = db_session.execute(
            text("SELECT role, message, created_at as timestamp FROM chat_messages WHERE session_id = :session_id ORDER BY created_at ASC"),
            {"session_id": session_id}
        ).fetchall()
        return [dict(row._mapping) for row in results]
    finally:
        db_session.close()

def get_history(session_id: str) -> List[AnyMessage]:
    """Retrieves the message history for a session and formats it for the agent."""
    messages = get_messages(session_id)
    history: List[AnyMessage] = [
        HumanMessage(content=m['message']) if m['role'] == 'user' else AIMessage(content=m['message'])
        for m in messages
    ]
    return history

def get_user_by_email_for_auth(email: str) -> Optional[dict]:
    """Retrieves user details for authentication by email."""
    db_session = get_db_session()
    try:
        query = text("SELECT id, name, email, password, role FROM users WHERE email = :email")
        result = db_session.execute(query, {"email": email}).fetchone()
        if not result:
            return None
        
        user_data = dict(result._mapping)
        user_data['id'] = str(user_data['id'])
        return user_data
    finally:
        db_session.close()

def get_all_users() -> List[dict]:
    """Retrieves all users."""
    db_session = get_db_session()
    try:
        query = text("SELECT id, name, email, role FROM users ORDER BY name")
        result = db_session.execute(query).fetchall()
        users = []
        for row in result:
            user_data = dict(row._mapping)
            user_data['id'] = str(user_data['id'])
            users.append(user_data)
        return users
    finally:
        db_session.close()

def get_tickets_by_user(user_id: Optional[str] = None, status: Optional[str] = None, ticket_id: Optional[str] = None) -> List[dict]:
    """Get tickets, filtering by user, status, or ticket ID."""
    db_session = get_db_session()
    try:
        base_query = """
            SELECT jt.id, jt.title, jt.description, jt.status, 
                   jt.project_id, jt.assigned_to, p.name as project_name
            FROM jira_tickets jt 
            JOIN projects p ON jt.project_id = p.id
        """
        conditions = []
        params = {}
        
        if user_id:
            conditions.append("jt.assigned_to = :user_id")
            params["user_id"] = user_id
        if status:
            conditions.append("LOWER(jt.status) = :status")
            params["status"] = status
        if ticket_id:
            conditions.append("jt.id = :ticket_id")
            params["ticket_id"] = ticket_id

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " ORDER BY jt.status, jt.title"
        query = text(base_query)
        
        result = db_session.execute(query, params).fetchall()
        tickets = []
        for row in result:
            ticket = dict(row._mapping)
            ticket['id'] = str(ticket['id'])
            ticket['project_id'] = str(ticket['project_id'])
            ticket['assigned_to'] = str(ticket['assigned_to'])
            tickets.append(ticket)
        return tickets
    finally:
        db_session.close()

def get_pull_requests_by_ticket(ticket_id: str) -> List[dict]:
    """Get all pull requests for a specific ticket."""
    db_session = get_db_session()
    try:
        query = text("""
            SELECT id, title, summary, ticket_id, author_id, project_id
            FROM pull_requests
            WHERE ticket_id = :ticket_id
            ORDER BY title
        """)
        result = db_session.execute(query, {"ticket_id": ticket_id}).fetchall()
        prs = []
        for row in result:
            pr = dict(row._mapping)
            pr['id'] = str(pr['id'])
            pr['ticket_id'] = str(pr['ticket_id'])
            pr['author_id'] = str(pr['author_id'])
            pr['project_id'] = str(pr['project_id'])
            prs.append(pr)
        return prs
    finally:
        db_session.close()

def get_diff_by_pr(pr_id: str) -> Optional[dict]:
    """Get the git diff for a specific pull request."""
    db_session = get_db_session()
    try:
        query = text("SELECT id, diff_text, pr_id FROM git_diffs WHERE pr_id = :pr_id")
        result = db_session.execute(query, {"pr_id": pr_id}).fetchone()
        if not result:
            return None
        diff = dict(result._mapping)
        diff['id'] = str(diff['id'])
        diff['pr_id'] = str(diff['pr_id'])
        return diff
    finally:
        db_session.close()

def get_docs(doc_id: Optional[str] = None, project_id: Optional[str] = None) -> List[dict]:
    """Get documents, optionally filtering by doc ID or project ID."""
    db_session = get_db_session()
    try:
        base_query = """
            SELECT d.id, d.title, d.content, d.type, 
                   d.project_id, p.name as project_name
            FROM documents d
            JOIN projects p ON d.project_id = p.id
        """
        params = {}
        if doc_id:
            base_query += " WHERE d.id = :doc_id"
            params["doc_id"] = doc_id
        elif project_id:
            base_query += " WHERE d.project_id = :project_id"
            params["project_id"] = project_id
        
        base_query += " ORDER BY d.type, d.title"
        query = text(base_query)
        
        result = db_session.execute(query, params).fetchall()
        docs = []
        for row in result:
            doc = dict(row._mapping)
            doc['id'] = str(doc['id'])
            doc['project_id'] = str(doc['project_id'])
            docs.append(doc)
        return docs
    finally:
        db_session.close()

def get_learnings(learning_id: Optional[str] = None, tag: Optional[str] = None, q: Optional[str] = None) -> List[dict]:
    """Get learning resources, with optional filtering."""
    db_session = get_db_session()
    try:
        base_query = "SELECT id, title, summary, tags, urls FROM learnings"
        params = {}
        if learning_id:
            base_query += " WHERE id = :learning_id"
            params["learning_id"] = learning_id
        elif tag:
            base_query += " WHERE :tag ILIKE ANY(tags)"
            params["tag"] = tag
        elif q:
            base_query += " WHERE LOWER(title) LIKE LOWER(:search_term) OR LOWER(summary) LIKE LOWER(:search_term)"
            params["search_term"] = f"%{q}%"
            
        base_query += " ORDER BY title"
        query = text(base_query)
        
        result = db_session.execute(query, params).fetchall()
        learnings = []
        for row in result:
            learning = dict(row._mapping)
            learning['id'] = str(learning['id'])
            learnings.append(learning)
        return learnings
    finally:
        db_session.close()

def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get information about a specific user by ID."""
    db_session = get_db_session()
    try:
        query = text("SELECT id, name, email, role FROM users WHERE id = :user_id")
        result = db_session.execute(query, {"user_id": user_id}).fetchone()
        if not result:
            return None
        user = dict(result._mapping)
        user['id'] = str(user['id'])
        return user
    finally:
        db_session.close()

def rename_chat_session(session_id: str, new_title: str) -> bool:
    """Renames a chat session."""
    db_session = get_db_session()
    try:
        query = text("UPDATE chat_sessions SET title = :new_title WHERE id = :session_id")
        result = db_session.execute(query, {"new_title": new_title, "session_id": session_id})
        db_session.commit()
        return result.rowcount > 0  # type: ignore
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error renaming session {session_id}: {e}", exc_info=True)
        raise
    finally:
        db_session.close()

def delete_chat_session(session_id: str) -> bool:
    """Deletes a chat session and all its messages."""
    db_session = get_db_session()
    try:
        # First, delete associated messages to maintain foreign key integrity
        db_session.execute(text("DELETE FROM chat_messages WHERE session_id = :session_id"), {"session_id": session_id})

        # Then, delete the session itself
        result = db_session.execute(text("DELETE FROM chat_sessions WHERE id = :session_id"), {"session_id": session_id})
        
        db_session.commit()
        
        return result.rowcount > 0  # type: ignore
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise
    finally:
        db_session.close()

def get_last_active_session(user_id: str) -> Optional[dict]:
    """Get the most recently created session for a user."""
    db_session = get_db_session()
    try:
        query = text("""
            SELECT id as session_id, title, created_at 
            FROM chat_sessions 
            WHERE user_id = :user_id 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        result = db_session.execute(query, {"user_id": user_id}).fetchone()
        if not result:
            return None
        
        session = dict(result._mapping)
        session['session_id'] = str(session['session_id'])
        return session
    finally:
        db_session.close()

def get_recent_messages(session_id: str, limit: int = 10) -> List[dict]:
    """Retrieves the most recent messages for a given session, ordered by timestamp DESC."""
    db_session = get_db_session()
    try:
        results = db_session.execute(
            text("SELECT role, message, created_at as timestamp FROM chat_messages WHERE session_id = :session_id ORDER BY created_at DESC LIMIT :limit"),
            {"session_id": session_id, "limit": limit}
        ).fetchall()
        return [dict(row._mapping) for row in results]
    finally:
        db_session.close()

def update_document_content(doc_id: str, new_content: str) -> bool:
    """Updates the content of a specific document."""
    db_session = get_db_session()
    try:
        query = text("UPDATE documents SET content = :new_content WHERE id = :doc_id")
        result = db_session.execute(query, {"new_content": new_content, "doc_id": doc_id})
        db_session.commit()
        return result.rowcount > 0  # type: ignore
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error updating document {doc_id}: {e}", exc_info=True)
        raise
    finally:
        db_session.close() 