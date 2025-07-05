import os
import uuid
import random
from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    ForeignKey,
    ARRAY
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from src.utils.logger import get_logger

# --- Setup ---
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")
logger = get_logger(__name__)

LOG_EXTRA = {"session_id": "mock-data-seed"}

# --- LLM Setup ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

# --- SQLAlchemy Setup ---
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)
    tickets = relationship("JiraTicket", back_populates="assignee")
    pull_requests = relationship("PullRequest", back_populates="author")

class Project(Base):
    __tablename__ = 'projects'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    tickets = relationship("JiraTicket", back_populates="project")
    pull_requests = relationship("PullRequest", back_populates="project")
    documents = relationship("Document", back_populates="project")

class JiraTicket(Base):
    __tablename__ = 'jira_tickets'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    assignee = relationship("User", back_populates="tickets")
    project = relationship("Project", back_populates="tickets")
    pull_requests = relationship("PullRequest", back_populates="ticket")

class PullRequest(Base):
    __tablename__ = 'pull_requests'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    summary = Column(Text)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey('jira_tickets.id'))
    author_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    ticket = relationship("JiraTicket", back_populates="pull_requests")
    author = relationship("User", back_populates="pull_requests")
    project = relationship("Project", back_populates="pull_requests")
    diffs = relationship("GitDiff", back_populates="pull_request")

class Document(Base):
    __tablename__ = 'documents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(Text)
    type = Column(String)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    project = relationship("Project", back_populates="documents")

class Learning(Base):
    __tablename__ = 'learnings'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    summary = Column(Text)
    tags = Column(ARRAY(String))
    urls = Column(ARRAY(String))

class GitDiff(Base):
    __tablename__ = 'git_diffs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diff_text = Column(Text)
    pr_id = Column(UUID(as_uuid=True), ForeignKey('pull_requests.id'))
    pull_request = relationship("PullRequest", back_populates="diffs")

# --- Database Connection ---
def get_db_session():
    """Establishes a connection to the PostgreSQL database and returns a session."""
    try:
        password = os.getenv("PG_PASSWORD")
        db_url = (
            f"postgresql+psycopg://{os.getenv('PG_USER')}:{password}@"
            f"{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DB')}"
        ) if password else (
            f"postgresql+psycopg://{os.getenv('PG_USER')}@"
            f"{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DB')}"
        )
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)  # Create tables if they don't exist
        Session = sessionmaker(bind=engine)
        session = Session()
        logger.info("Database session established.", extra=LOG_EXTRA)
        return session
    except Exception as e:
        logger.error(f"Database connection failed: {e}", extra=LOG_EXTRA)
        raise

def clear_data(session):
    """Clears all data from the tables."""
    logger.info("Clearing all existing data from tables...", extra=LOG_EXTRA)
    try:
        # The order is important, so we reflect and sort tables by dependency.
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        logger.info("All tables cleared successfully.", extra=LOG_EXTRA)
    except Exception as e:
        logger.error(f"Failed to clear data: {e}", extra=LOG_EXTRA)
        session.rollback()
        raise

# --- LLM-Powered Data Generation ---

def generate_llm_data(prompt_template, **kwargs):
    """Uses an LLM to generate data based on a prompt template."""
    logger.info(f"Generating data with LLM for: {kwargs}", extra=LOG_EXTRA)
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=list(kwargs.keys()),
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | parser
    try:
        result = chain.invoke(kwargs)
        if not result:
            raise ValueError("LLM returned empty result")
        return result
    except Exception as e:
        logger.error(f"LLM data generation failed: {e}", extra=LOG_EXTRA)
        raise

# --- Data Generation ---
def generate_users():
    """Generates a predefined list of users."""
    logger.info("Generating predefined user list...", extra=LOG_EXTRA)
    users_data = [
        {'name': 'Steve Rogers', 'email': 'steve.rogers@relanto.ai', 'role': 'developer'},
        {'name': 'Rust Cohle', 'email': 'rust.cohle@relanto.ai', 'role': 'developer'},
        {'name': 'Leo Messi', 'email': 'leo.messi@relanto.ai', 'role': 'lead'},
        {'name': 'Darth Vader', 'email': 'darth.vader@relanto.ai', 'role': 'admin'},
        {'name': 'Vito Corleone', 'email': 'vito.corleone@relanto.ai', 'role': 'developer'},
    ]
    for user in users_data:
        user['id'] = str(uuid.uuid4())
    return users_data

def generate_projects():
    prompt = """
    Generate 3 software project names and a one-sentence description for each.
    The project names should be inspired by mythical creatures (e.g., Phoenix, Pegasus, Griffin).
    The projects should be related to internal developer tools or infrastructure.
    Return the result as a JSON list of objects, where each object has 'name' and 'description' keys.
    {format_instructions}
    """
    projects_data = generate_llm_data(prompt)
    for p in projects_data:
        p["id"] = str(uuid.uuid4())
    return projects_data

def generate_jira_tickets(projects, users):
    tickets = []
    devs = [u for u in users if u["role"] == "developer"]
    prompt = """
    For a software project named '{project_name}', generate {num_tickets} realistic Jira ticket titles and descriptions.
    The tickets should cover a range of tasks including new features, bug fixes, technical debt, and documentation.
    Return as a JSON list of objects, each with 'title' and 'description' keys.
    {format_instructions}
    """
    for project in projects:
        num_tickets = random.randint(10, 15)
        ticket_data = generate_llm_data(prompt, project_name=project["name"], num_tickets=num_tickets)
        for item in ticket_data:
            tickets.append({
                "id": str(uuid.uuid4()),
                "title": item["title"],
                "description": item["description"],
                "status": random.choice(["Open", "In Progress", "Done"]),
                "assigned_to": random.choice(devs)["id"],
                "project_id": project["id"]
            })
    return tickets

def generate_pull_requests(tickets, users, projects):
    prs = []
    devs = [u for u in users if u["role"] == "developer"]
    prompt = """
    For a Jira ticket titled '{ticket_title}', generate a realistic pull request title and a short, one-paragraph summary of the changes.
    The title should be concise and prefixed with the ticket context, like 'feat:' or 'fix:'.
    Return as a JSON object with 'title' and 'summary' keys.
    {format_instructions}
    """
    for ticket in tickets:
        for _ in range(random.randint(1, 2)):
            pr_data = generate_llm_data(prompt, ticket_title=ticket["title"])
            pr = {
                "id": str(uuid.uuid4()),
                "title": pr_data["title"],
                "summary": pr_data["summary"],
                "ticket_id": ticket["id"],
                "author_id": random.choice(devs)["id"],
                "project_id": ticket["project_id"]
            }
            prs.append(pr)
    return prs

def generate_documents(projects):
    docs = []
    prompt = """
    For a software project named '{project_name}', generate a document of type '{doc_type}'.
    The document should have a 'title' and detailed 'content' (2-3 paragraphs).
    Return as a JSON object with 'title' and 'content' keys.
    {format_instructions}
    """
    doc_types = ["API Guide", "Onboarding Guide", "Architecture Overview"]
    for project in projects:
        for doc_type in doc_types:
            doc_data = generate_llm_data(prompt, project_name=project["name"], doc_type=doc_type)
            docs.append({
                "id": str(uuid.uuid4()),
                "title": doc_data["title"],
                "content": doc_data["content"],
                "type": doc_type,
                "project_id": project["id"]
            })
    return docs

def generate_learnings():
    prompt = """
    Generate 20 developer-focused 'learnings'. Each should have a concise title, a one-paragraph summary, 2-5 relevant tags, and a single realistic but fake URL.
    The topics should be diverse, covering areas like new technologies, performance optimization, security best practices, or effective debugging techniques.
    Return as a JSON list of objects, each with 'title', 'summary', 'tags' (a list of strings), and 'urls' (a list containing one URL string).
    {format_instructions}
    """
    learnings_data = generate_llm_data(prompt)
    for l in learnings_data:
        l["id"] = str(uuid.uuid4())
    return learnings_data

def generate_git_diffs(prs):
    diffs = []
    prompt = """
    For a pull request titled '{pr_title}', generate a realistic, small git diff.
    The diff should be for a Python file (e.g., `app/utils.py` or `services/logic.py`).
    It should be plausible for the given PR title and represent a small code change.
    Return as a JSON object with a single key 'diff_text' containing the diff.
    {format_instructions}
    """
    for pr in prs:
        for _ in range(random.randint(1, 2)):
            diff_data = generate_llm_data(prompt, pr_title=pr["title"])
            diffs.append({
                "id": str(uuid.uuid4()),
                "diff_text": diff_data["diff_text"],
                "pr_id": pr["id"]
            })
    return diffs

# --- Data Insertion ---
def insert_data(session, model, data):
    """Inserts data into the database using SQLAlchemy session."""
    if not data:
        return
    logger.info(f"Inserting {len(data)} records into {model.__tablename__}...", extra=LOG_EXTRA)
    
    # Ensure all generated IDs are preserved
    session.bulk_insert_mappings(model, data)
    
    try:
        session.commit()
        logger.info(f"Successfully inserted data into {model.__tablename__}.", extra=LOG_EXTRA)
    except Exception as e:
        logger.error(f"Data insertion failed for {model.__tablename__}: {e}", extra=LOG_EXTRA)
        session.rollback()
        raise

# --- Main Execution ---
def main():
    """Main function to run the data population script."""
    logger.info("Starting mock data population script...", extra=LOG_EXTRA)
    session = get_db_session()
    try:
        clear_data(session)
        # Generate Data
        users_data = generate_users()
        projects_data = generate_projects()
        
        # Insert users and projects first to satisfy foreign key constraints
        insert_data(session, User, users_data)
        insert_data(session, Project, projects_data)
        
        # Pass generated IDs to subsequent generation functions
        jira_tickets_data = generate_jira_tickets(projects_data, users_data)
        insert_data(session, JiraTicket, jira_tickets_data)

        pull_requests_data = generate_pull_requests(jira_tickets_data, users_data, projects_data)
        insert_data(session, PullRequest, pull_requests_data)

        documents_data = generate_documents(projects_data)
        insert_data(session, Document, documents_data)

        learnings_data = generate_learnings()
        insert_data(session, Learning, learnings_data)

        git_diffs_data = generate_git_diffs(pull_requests_data)
        insert_data(session, GitDiff, git_diffs_data)

        # Print Summary
        print("\\n--- Data Population Summary ---")
        print(f"Created {len(users_data)} users")
        print(f"Created {len(projects_data)} projects")
        print(f"Inserted {len(jira_tickets_data)} Jira tickets")
        print(f"Inserted {len(pull_requests_data)} pull requests")
        print(f"Inserted {len(documents_data)} documents")
        print(f"Inserted {len(learnings_data)} learnings")
        print(f"Inserted {len(git_diffs_data)} git diffs")
        print("---------------------------------\\n")

    finally:
        session.close()
        logger.info("Database connection closed.", extra=LOG_EXTRA)

if __name__ == "__main__":
    main() 