from typing import List, Optional
import json
from pydantic import BaseModel
import pydantic
from modules.base_module import TrackModule
from utils import generate_content

# Define Pydantic models for report structure
class QuestionScore(BaseModel):
    id: int
    question: str
    score: str   # Should be '+' or '-'
    error: Optional[str] = None  # User mistake if score is '-'
    proper_answer: Optional[str] = None  # Proper answer if score is '-'

class Report(BaseModel):
    questions_and_scores: List[QuestionScore]
    total_score: float  # Number of '+' divided by the number of questions
    recommendations_to_repeat: Optional[List[str]]

class iOSTrackModule:
    def __init__(self, user_preferences, rag_manager, type_name="IOS_RU"):
        self.user_preferences = user_preferences
        self.rag_manager = rag_manager
        self.type_name = type_name
    
    def get_questions_by_theme(self):
        # Retrieve questions related to the given theme using embeddings or any other logic
        return self.rag_manager.get_questions_by_theme(self.user_preferences['theme'], self.user_preferences['number_of_questions'])

    def get_questions_by_level(self):
        # Fetch questions for a particular level
        print(self.user_preferences['level'], self.rag_manager.sglite, self.user_preferences['number_of_questions'])
        return self.rag_manager.get_questions_by_level(self.type_name, self.user_preferences['level'], self.user_preferences['number_of_questions'])
    
    def fetch_questions(self):
        # Fetch iOS-specific questions based on level and theme
        if self.user_preferences['theme']:
            questions = self.get_questions_by_theme()
        else:
            questions = self.get_questions_by_level()
        return questions

    async def generate_report(self, answers, questions):
        
        # Compare answers, calculate score, and generate report
        schema = json.dumps(Report.model_json_schema(), indent=2)
        prompt = (
            f"""Based on the user's answers: {answers}, generate a report using the following questions and proper answers: {questions}.
            
            Format the report as JSON that adheres to the following schema:
            {schema}
            
            Make sure the report includes real data, with '+' or '-' as scores, and includes proper answers and user mistakes if applicable. Return only valid JSON data."""
        )
    
        # Await the result of the async function
        content = await generate_content(prompt)
        print(f"[DEBUG] Generated content: {content}")  # Debug: Print raw content from the prompt
        content = content.strip().lstrip("```json").rstrip("```")

        try:
            content_json = json.loads(content)
            print(f"[DEBUG] Content JSON before validation: {json.dumps(content_json, indent=2)}")
            report_json = Report.model_validate(content_json)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing failed: {e}")
            return "Error: Unable to parse the report content."
        except pydantic.ValidationError as e:
            print(f"[ERROR] Validation failed: {e}")
            print(f"[DEBUG] Content JSON structure: {json.dumps(content_json, indent=2)}")
            return "Error: The generated content does not match the expected report structure."

        print(f"[DEBUG] Parsed report JSON: {report_json}")  # Debug: Print parsed JSON report

        # Format the report as a user-friendly string
        formatted_report = "Report:\n\n"
        for idx, item in enumerate(report_json.questions_and_scores, start=1):
            formatted_report += f"{idx}. Question: {item.question}\n"
            formatted_report += f"   Score: {item.score}\n"
            if item.score == '-':
                formatted_report += f"   User's mistake: {item.error}\n"
                formatted_report += f"   Proper Answer: {item.proper_answer}\n"
            else:
                # Call change_status when score is +
                print(f"[DEBUG] Changing status for question {idx} to 'Completed'")  # Debug: Status change
                await self.change_status(item.id, "Completed")
            formatted_report += "\n"

        formatted_report += f"Total score: {report_json.total_score:.2f}\n\n"
        formatted_report += "Recommendations to repeat:\n"
        formatted_report += "\n".join(report_json.recommendations_to_repeat or ["None"])  # Add default 'None' if empty

        print(f"[DEBUG] Final formatted report:\n{formatted_report}")  # Debug: Print final report
        return formatted_report

    async def change_status(self, id, status):
        print(f"[DEBUG] change_status called with id: {id}, status: {status}")  # Debug: Print change_status call details
        return self.rag_manager.change_status(id, status)
