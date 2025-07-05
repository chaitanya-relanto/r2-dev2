import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr

from src.utils.logger import get_logger

# Load environment variables from both configuration files.
# This assumes the script is run from the project root where main.py resides.
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

# Initialize logger for this module
logger = get_logger(__name__)

class PRSummarizer:
    """
    A service class to summarize pull request diffs using an OpenAI model.
    """

    def __init__(self):
        """
        Initializes the PRSummarizer with the ChatOpenAI model.
        It retrieves the OpenAI API key from environment variables.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY is not set in the environment variables.")
            raise ValueError("OPENAI_API_KEY must be set for the summarizer to work.")

        self.llm = ChatOpenAI(api_key=SecretStr(api_key), model="gpt-4o-mini", temperature=0.1)
        logger.info("PRSummarizer initialized successfully.")

    def summarize_diff(self, diff_text: str, session_id: str = "anonymous") -> str:
        """
        Summarizes a given diff text using the language model.

        Args:
            diff_text: The raw git diff string to be summarized.
            session_id: A unique identifier for the session, for logging purposes.

        Returns:
            A string containing the summary of the diff.
        """
        log_extra = {"session_id": session_id}
        logger.info("Starting PR diff summarization.", extra=log_extra)
        logger.info(
            f"Diff text length: {len(diff_text)} characters.", extra=log_extra
        )

        system_prompt = (
            "You are an expert at summarizing code changes from a multi-line git diff. "
            "Analyze the provided diff and create a concise summary of 2-3 sentences. "
            "Highlight the key purpose of the changes, such as bug fixes, new features, or refactoring."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please summarize the following git diff:\\n\\n{diff_text}"),
        ]

        try:
            response = self.llm.invoke(messages)
            summary = str(response.content)
            logger.info(f"Generated summary: {summary}", extra=log_extra)
            return summary
        except Exception as e:
            logger.error(f"An error occurred during summarization: {e}", extra=log_extra, exc_info=True)
            return "Error: Could not generate a summary for the provided diff."

if __name__ == "__main__":
    # This block allows for direct execution of the script for testing purposes.
    try:
        summarizer = PRSummarizer()

        # Define a simple, realistic diff for testing
        example_diff = """
diff --git a/src/utils/helpers.py b/src/utils/helpers.py
index e69de29..a8b4b3c 100644
--- a/src/utils/helpers.py
+++ b/src/utils/helpers.py
@@ -1,5 +1,8 @@
 import re
 
 def slugify(text):
-    text = re.sub(r'[^\\w\\s-]', '', text).strip().lower()
-    return re.sub(r'[\\s-]+', '-', text)
+    # Improved slugify function to handle more edge cases
+    text = re.sub(r'[^\\w\\s-]', '', str(text)).strip().lower()
+    return re.sub(r'[\\s-]+', '-', text)
+
+def format_currency(value):
+    return f"${value:,.2f}"
"""
        session_id = "test-session-xyz"
        print(f"--- Running test summarization for session: {session_id} ---")
        summary = summarizer.summarize_diff(example_diff, session_id=session_id)
        
        print("\\n--- Generated Summary ---")
        print(summary)
        print("\\n--- Test Complete ---")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}") 