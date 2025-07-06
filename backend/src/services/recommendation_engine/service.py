import os
import json
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr

from src.utils.logger import get_logger
from src.services.database_manager import operations as db_ops

# Load environment variables
load_dotenv("configs/.env")
load_dotenv("configs/secrets/.env")

# Initialize logger for this module
logger = get_logger(__name__)


class RecommendationService:
    """
    A service class to generate follow-up action recommendations based on recent chat messages.
    """

    def __init__(self):
        """
        Initializes the RecommendationService with the ChatOpenAI model.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY is not set in the environment variables.")
            raise ValueError("OPENAI_API_KEY must be set for the recommendation service to work.")

        self.llm = ChatOpenAI(api_key=SecretStr(api_key), model="gpt-4o-mini", temperature=0.3)
        logger.info("RecommendationService initialized successfully.")

    def generate_recommendations(self, session_id: str, num_messages: int = 10) -> List[str]:
        """
        Generates 2-3 follow-up action recommendations based on recent chat messages.

        Args:
            session_id: The session ID to analyze messages from
            num_messages: Number of recent messages to consider (default: 10)

        Returns:
            A list of recommendation strings
        """
        log_extra = {"session_id": session_id}
        logger.info(f"Generating recommendations for session {session_id} with {num_messages} recent messages.", extra=log_extra)

        try:
            # Get recent messages from database
            recent_messages = db_ops.get_recent_messages(session_id, num_messages)
            
            if not recent_messages:
                logger.warning(f"No messages found for session {session_id}.", extra=log_extra)
                return [
                    "What's the best way to structure a new project?",
                    "How do I debug this error I'm getting?",
                    "Can you help me review my code?"
                ]
            
            if len(recent_messages) < 5:
                logger.info(f"Only {len(recent_messages)} message(s) found for session {session_id}. Providing contextual recommendations.", extra=log_extra)
                
                # Analyze the most recent user message to provide contextual recommendations
                user_message = None
                for msg in recent_messages:
                    if msg['role'] == 'user':
                        user_message = msg['message']
                        break
                
                if user_message:
                    user_message_lower = user_message.lower().strip()
                    
                    # Handle greeting messages (hi, hello, hey, etc.)
                    greeting_patterns = [
                        'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 
                        'good evening', 'howdy', 'what\'s up', 'whats up', 'sup'
                    ]
                    
                    if any(greeting in user_message_lower for greeting in greeting_patterns) or len(user_message.strip()) <= 10:
                        return [
                            "What project are you working on?",
                            "I need help with debugging an issue.",
                            "Can you recommend some learning resources?"
                        ]
                    
                    # Provide recommendations based on common development patterns
                    if any(keyword in user_message_lower for keyword in ['bug', 'error', 'issue', 'problem', 'debug', 'fix', 'broken']):
                        return [
                            "What debugging strategies would you recommend?",
                            "How can I add better logging to troubleshoot this?",
                            "What are the most common causes of this type of error?"
                        ]
                    elif any(keyword in user_message_lower for keyword in ['code', 'implement', 'build', 'create', 'develop', 'write', 'program']):
                        return [
                            "What's the best way to structure this code?",
                            "How should I write tests for this functionality?",
                            "Are there any better approaches to implement this?"
                        ]
                    elif any(keyword in user_message_lower for keyword in ['learn', 'tutorial', 'how to', 'guide', 'teach', 'explain']):
                        return [
                            "Can you recommend some good learning resources for this?",
                            "Where can I find tutorials or examples?",
                            "What related topics should I learn next?"
                        ]
                    elif any(keyword in user_message_lower for keyword in ['test', 'testing', 'unit test', 'integration']):
                        return [
                            "What testing framework would you recommend?",
                            "How do I write effective test cases for this?",
                            "What's the best way to set up automated testing?"
                        ]
                    elif any(keyword in user_message_lower for keyword in ['deploy', 'deployment', 'production', 'server', 'hosting']):
                        return [
                            "What's the best deployment strategy for this project?",
                            "How should I configure the server for production?",
                            "Can you help me set up a CI/CD pipeline?"
                        ]
                    else:
                        return [
                            "Can you explain this in more detail?",
                            "What would be the next steps for this?",
                            "Are there any tools or best practices I should know about?"
                        ]
                else:
                    return [
                        "Can you tell me more about that?",
                        "Do you have any examples I can look at?",
                        "What are some alternatives to this approach?"
                    ]

            # Format messages for the prompt (reverse to show chronological order)
            formatted_messages = []
            for msg in reversed(recent_messages):
                role = "User" if msg['role'] == 'user' else "Assistant"
                formatted_messages.append(f"- {role}: {msg['message']}")
            
            messages_text = "\n".join(formatted_messages)
            
            logger.info(f"Formatted {len(recent_messages)} messages for recommendation generation.", extra=log_extra)

            # Create the prompt for OpenAI
            system_prompt = (
                "You are an expert at analyzing conversation patterns and suggesting the next message a user might want to send. "
                "Based on the provided chat messages, suggest 2-3 specific follow-up questions or messages "
                "that the user can click to auto-fill as their next message. "
                "Make the suggestions conversational, natural, and directly related to continuing the conversation. "
                "Write them as if the user is asking the question directly. "
                "Format your response as a JSON array of strings."
            )

            user_prompt = f"""Based on the following recent chat messages, suggest 2-3 follow-up messages the user might want to send next. 
Write them as direct questions or statements the user can click to auto-fill.

Recent Messages:
{messages_text}

Please respond with a JSON array of 2-3 message suggestions that the user can click to send."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # Get response from OpenAI
            response = self.llm.invoke(messages)
            response_content = str(response.content)
            
            logger.info(f"Received response from OpenAI: {response_content[:100]}...", extra=log_extra)

            # Parse the JSON response
            try:
                suggestions = json.loads(response_content)
                if not isinstance(suggestions, list):
                    raise ValueError("Response is not a list")
                
                # Ensure we have 2-3 suggestions
                suggestions = suggestions[:3]  # Limit to max 3
                if len(suggestions) < 2:
                    # Add development-focused suggestions if we don't have enough
                    suggestions.extend([
                        "Can you provide more technical details about this?",
                        "What are some alternative approaches to this?",
                        "Do you have any code examples I can look at?"
                    ])
                    suggestions = suggestions[:3]  # Ensure max 3
                
                logger.info(f"Generated {len(suggestions)} recommendations successfully.", extra=log_extra)
                return suggestions
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response: {e}. Attempting to extract suggestions manually.", extra=log_extra)
                
                # Fallback: try to extract suggestions from the response text
                lines = response_content.strip().split('\n')
                suggestions = []
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('"') or line.startswith('-') or line.startswith('•')):
                        # Clean up the line
                        suggestion = line.strip('"').strip('-').strip('•').strip()
                        if suggestion and len(suggestion) > 10:  # Ensure it's not too short
                            suggestions.append(suggestion)
                
                if suggestions:
                    logger.info(f"Extracted {len(suggestions)} suggestions from response text.", extra=log_extra)
                    return suggestions[:3]  # Limit to 3
                
                # Final fallback
                logger.warning("Could not extract suggestions from response. Using fallback recommendations.", extra=log_extra)
                return [
                    "Can you walk me through the implementation details?",
                    "Do you have any code examples for this?",
                    "What are the best practices for this approach?"
                ]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", extra=log_extra, exc_info=True)
            return [
                "Can you tell me more about this topic?",
                "Do you have any code examples or step-by-step instructions?",
                "What are some alternative approaches I could try?"
            ] 