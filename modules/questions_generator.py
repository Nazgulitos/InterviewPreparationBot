import json
from database_manager import retrieve_context_from_chromadb
from utils import generate_content
from collections import defaultdict

generated_questions_cache = defaultdict(list)

def generate_question_prompt(context_chunk, n_questions):
    """
    Constructs a prompt for generating a question based on the context chunk.
    """
    prompt = (
        f"""
        You are an expert in educational content creation. Based on the following information, generate a question 
        for a test related to the theme. Ensure the question is clear, concise, and relevant:
        
        Context:
        {context_chunk}
        
        Generate strongly in JSON format {n_questions} questions in this format:
        "question": "<Your question here>",
        "answer": "<Suggested answer here>"
        """
    )
    return prompt

async def create_questions_by_theme(theme, collection, n_questions):
    """
    Generates `n_questions` questions based on the context retrieved from ChromaDB for a given `theme`.
    Checks cache first for existing questions to avoid redundant generation.
    """
    # Check if the questions for this theme are already in the cache
    if theme in generated_questions_cache and len(generated_questions_cache[theme]) >= n_questions:
        print(f"Returning cached questions for theme: {theme}")
        return generated_questions_cache[theme][:n_questions]

    print(f"Retrieving context for theme: {theme}")
    context_chunks = retrieve_context_from_chromadb(query=theme, collection=collection, n_results=n_questions)

    if not context_chunks or context_chunks == "No relevant context found.":
        print("No context found. Please ensure the collection has relevant data.")
        return []

    max_retries = 5
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1} to generate questions")
        # Generate questions from the context
        prompt = generate_question_prompt(context_chunks, n_questions)
        questions_response = await generate_content(prompt)
        questions_response = questions_response.strip().lstrip("```json").rstrip("```")

        try:
            # Parse the response assuming it's in JSON format
            question_data = json.loads(questions_response.strip())
            if isinstance(question_data, list):
                # Add questions to the cache
                generated_questions_cache[theme].extend(question_data)
                # Trim cache to avoid excessive memory usage
                if len(generated_questions_cache[theme]) > 100:  # Limit cache size per theme
                    generated_questions_cache[theme] = generated_questions_cache[theme][-100:]

                return question_data  # Return newly generated questions
            else:
                print(f"Response is not in the expected format: {questions_response}")
        except json.JSONDecodeError:
            print(f"Failed to decode the response for question generation: {questions_response}")

    print("Max retries reached. Unable to generate questions.")
    return []

# Example usage
# if __name__ == "__main__":
#     theme = 'ML_EN'
#     collection = chromadb.Client().get_or_create_collection('pdf_collection4')
#     
#     # Run the async function to generate questions
#     generated_questions = asyncio.run(create_questions_by_theme(theme, collection, n_questions=5))
#     
#     for question in generated_questions:
#         print(f"\nID: {question['id']}")
#         print(f"Theme: {question['theme']}")
#         print(f"Question: {question['question']}")
#         print(f"Answer: {question['answer']}")
#         print(f"Level: {question['level']}")
#         print(f"Status: {question['status']}")
