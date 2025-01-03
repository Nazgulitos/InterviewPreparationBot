from typing import List, Optional
import json
from pydantic import BaseModel
import pydantic
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

class ReportGenerator:
    def __init__(self, rag_manager):
        self.rag_manager = rag_manager

    async def generate_report(self, answers, questions, max_retries=5):
        # Compare answers, calculate score, and generate report
        schema = json.dumps(Report.model_json_schema(), indent=2)
        prompt = (
            f"""Based on the user's answers: {answers}, generate a report using the following questions and proper answers: {questions}.
            Please evaluate the user's answers very softly..
            "score" should be '+' or '-'
            "total_score" should be number of '+' divided by number of questions.
            Example of valid JSON:
                "questions_and_scores": [
                        "id": 1,
                        "question": "Explain the difference between Forward Selection and Backward Elimination feature selection techniques, highlighting their iterative processes and the criteria for stopping each.",
                        "score": "-",
                        "error": "User response: idk",
                        "proper_answer": "Forward Selection starts with no features and iteratively adds the feature that most improves the model, stopping when adding a feature no longer improves performance. Backward Elimination starts with all features and iteratively removes the feature that most improves the model, stopping when removing a feature no longer improves performance."
                    ,
                    ...
                ],
                "total_score": 0,
                "recommendations_to_repeat": [
                    "Review the concepts of Forward Selection and Backward Elimination.",
                    ...
                ]
            Don't return anything else but only JSON
            """
        )

        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                # Await the result of the async function
                content = await generate_content(prompt)
                print(f"[DEBUG] Attempt {attempt}: Generated content: {content}")  # Debug: Print raw content from the prompt
                content = content.strip().lstrip("```json").rstrip("```")

                content_json = json.loads(content)
                print(f"[DEBUG] Content JSON before validation: {json.dumps(content_json, indent=2)}")
                # report_json = Report.model_validate(content_json)
                # report_json = content_json["properties"]
                # report_json = content_json.properties
                report_json = Report.model_validate(content_json)
                break  # Exit loop if no error occurs
            except (json.JSONDecodeError, pydantic.ValidationError) as e:
                print(f"[ERROR] Attempt {attempt}: Report generation failed: {e}")
                if attempt == max_retries:
                    return f"Error: Unable to generate a valid report after {max_retries} attempts."
                print("[INFO] Retrying report generation...")

        # print(f"[DEBUG] Parsed report JSON: {report_json}")  # Debug: Print parsed JSON report

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
                # print(f"[DEBUG] Changing status for question {idx} to 'Completed'")  # Debug: Status change
                await self.change_status(item.id, "Completed")
            formatted_report += "\n"

        formatted_report += f"Total score: {report_json.total_score:.2f}\n\n"
        formatted_report += "Recommendations to repeat:\n"
        formatted_report += "\n".join(report_json.recommendations_to_repeat or ["None"])  # Add default 'None' if empty

        # print(f"[DEBUG] Final formatted report:\n{formatted_report}")  # Debug: Print final report
        return formatted_report
        # return report_json

    async def change_status(self, id, status):
        print(f"[DEBUG] change_status called with id: {id}, status: {status}")  # Debug: Print change_status call details
        return self.rag_manager.change_status(id, status)
