from typing import List

class QuestionRetriever:
    def __init__(self, rag_manager):
        self.rag_manager = rag_manager

    async def get_questions_by_theme(self, theme: str, num_questions: int) -> List[dict]:
        return await self.rag_manager.get_questions_by_theme(theme, num_questions)

    def get_questions_by_level(self, type_name: str, level: str, num_questions: int) -> List[dict]:
        return self.rag_manager.get_questions_by_level(type_name, level, num_questions)