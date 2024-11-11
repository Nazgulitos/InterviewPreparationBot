from modules.base_module import TrackModule
from utils import generate_content
import json

class iOSTrackModule:
    def __init__(self, user_preferences, rag_manager):
        self.user_preferences = user_preferences
        self.rag_manager = rag_manager
    
    def get_questions_by_theme(self):
        # Retrieve questions related to the given theme using embeddings or any other logic
        return self.rag_manager.get_questions_by_theme(self.user_preferences['theme'], self.user_preferences['number_of_questions'])

    def get_questions_by_level(self):
        # Fetch questions for a particular level
        print(self.user_preferences['level'], self.rag_manager.sglite, self.user_preferences['number_of_questions'])
        return self.rag_manager.get_questions_by_level(self.user_preferences['level'], self.user_preferences['number_of_questions'])
    
    def fetch_questions(self):
        # Fetch iOS-specific questions based on level and theme
        if self.user_preferences['theme']:
            questions = self.get_questions_by_theme()
        else:
            questions = self.get_questions_by_level()
        return questions

    async def generate_report(self, answers, questions):
        # Compare answers, calculate score, and generate report
        prompt = f"""Write report based on user's answers: {answers}. 
        The questions and proper answers are: {questions}.

        Return report in json format with the following keys:
            "question_and_scores": list of dictionaries with keys "question" and "score"(might be + or -) and "error"(if score is negative you need to explain where is error and say proper answer, otherwise None)
            "total_score": number of '+' divided by number of questions.
            "recommendations to repeat": (list of themes in which user made a mistake)

        """
        prompt = f"""Write report based on user's answers: {answers}. 
        The questions and proper answers are: {questions}.
        Report must be in the following format:

        1. Question: 
        Score + 
        2. Question: 
        Score - 
        User's mistake 
        Proper Answer
        ...

        Total score: number of '+' divided by number of questions.
        Recommendations to repeat: (list of themes in which user made a mistake)
        """
        content = generate_content(prompt)
        # # Await the result of the async function
        # content = await generate_content(prompt)
        # print(f"Generated content: {content}") 
        # content = content.lstrip('"""json').rstrip('"""')
        # # Parse JSON response
        # report_json = json.loads(content)

        # # Format the report as a user-friendly string
        # formatted_report = "Report:\n\n"
        # for idx, item in enumerate(report_json["question_and_scores"], start=1):
        #     formatted_report += f"{idx}. Question: {item['question']}\n"
        #     formatted_report += f"   Score: {item['score']}\n"
        #     if item['score'] == '-':
        #         formatted_report += f"   User's mistake: {item['error']}\n"
        #         formatted_report += f"   Proper Answer: {questions[idx - 1]['answer']}\n"
        #     formatted_report += "\n"

        # formatted_report += f"Total score: {report_json['total_score']:.2f}\n\n"
        # formatted_report += "Recommendations to repeat:\n"
        # formatted_report += "\n".join(report_json["recommendations to repeat"])

        # return formatted_report