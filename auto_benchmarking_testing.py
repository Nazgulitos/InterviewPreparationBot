import sqlite3
import random
import csv
import chromadb
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from modules.report_generator import ReportGenerator
from groq import Groq
from dotenv import load_dotenv
import asyncio
from rag_manager import RAGManager
load_dotenv()


# Pydantic model for output data
class EvaluationResult(BaseModel):
    id: str
    question: str
    proper_answer: str
    judge_answer: str
    llm_score: str
    is_accurate: bool

# Function to fetch 50 random questions from the database
def get_random_questions(conn, num_questions=50):
    cursor = conn.cursor()
    cursor.execute('SELECT id, question, answer FROM questions ORDER BY RANDOM() LIMIT ?', (num_questions,))
    rows = cursor.fetchall()
    return [{'id': row[0], 'question': row[1], 'answer': row[2]} for row in rows]

def generate_with_judge_1(questions):
    prompt = (
    f"Given the question: {questions}, generate two distinct 1-2 sentence answers. "
    f"One should be the correct and accurate answer (proper_answer), and the other should be an incorrect or misleading response (wrong_answer). "
    f"Return the result strictly in JSON format with the structure: {{'proper_answer': str, 'wrong_answer': str}}. "
    f"Ensure that the JSON formatting is precise and valid."
    )
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(  # Do NOT await here
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
    )
    result = completion.choices[0].message.content
    return result

def evalauate_report(report):
    schema = json.dumps(EvaluationResult.model_json_schema(), indent=2)
    prompt = f"Evaluate the following report: {report}, generate STRONGLY JSON in the following {schema}"
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(  # Do NOT await here
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        response_format={"type": "json_object"},
    )
    result = completion.choices[0].message.content
    return result

# Write the evaluation results to a CSV file
def write_to_csv(filename, data):
    fieldnames = ['id', 'question', 'proper_answer', 'judge_answer', 'llm_score', 'is_accurate']
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
def create_sqlite_db(path):
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id TEXT PRIMARY KEY,
                        theme TEXT,
                        question TEXT,
                        answer TEXT,
                        level TEXT,
                        status TEXT)''')
    connection.commit()
    return connection

# Main script logic
async def main():
    # SQLite database connection and table creation
    # Create or open SQLite database
    db_path = 'sglite_demo.db'
    sqlite_connection = create_sqlite_db(db_path)

    client = chromadb.HttpClient(host='localhost', port=8000)
    chromadb_connection = client.get_or_create_collection(name="chromadb_final_2024_test")

    # # Fetch 50 questions from the database
    # questions = get_random_questions(sqlite_connection)
    # qa_list = [[q['question'], q['answer']] for q in questions]
    # answers = []

    # for item in qa_list:
    #     answer = generate_with_judge_1(item)
    #     print(answer)  # Check if it's a string or dictionary

    #     # If the answer is a string, parse it
    #     if isinstance(answer, str):
    #         try:
    #             answer = json.loads(answer)  # Convert string to dictionary
    #         except json.JSONDecodeError:
    #             print("Error parsing JSON:", answer)
    #             continue  # Skip this iteration if JSON is malformed

    #     # Now handle the answer as a dictionary
    #     if isinstance(answer, dict) and "proper_answer" in answer and "wrong_answer" in answer:
    #         answers.append({
    #             'question': item[0],
    #             'proper_answer': item[1],
    #             'judge_answer': answer["proper_answer"],
    #             'y_true': 1
    #         })
    #         answers.append({
    #             'question': item[0],
    #             'proper_answer': item[1],
    #             'judge_answer': answer["wrong_answer"],
    #             'y_true': 0
    #         })
    #     else:
    #         print("Unexpected answer format or missing keys:", answer)
    # # Save the answers to a CSV file
    # csv_filename = 'benchmarking_results/answers.csv'

    # # Define the fieldnames (headers) for the CSV
    # fieldnames = ['question', 'proper_answer', 'judge_answer', 'y_true']

    # # Write to the CSV file
    # with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    #     writer = csv.DictWriter(file, fieldnames=fieldnames)

    #     # Write the header
    #     writer.writeheader()

    #     # Write the data rows
    #     writer.writerows(answers)

    # print(f"Answers saved to {csv_filename}")

    # # Generate a report from the answers
    # Read the CSV file and retrieve question and judge_answer
    # csv_filename = 'benchmarking_results/answers.csv'
    # rag_manager = RAGManager(chromadb_connection, sqlite_connection)
    # report_generator = ReportGenerator(rag_manager)
    # csv_filename_for_new = 'benchmarking_results/answers_2.csv'

    # # Define the fieldnames (headers) for the new CSV
    # fieldnames = ['question', 'proper_answer', 'judge_answer', 'y_true', 'llm_score']

    # # Open the input CSV file in read mode
    # with open(csv_filename, mode='r', encoding='utf-8') as input_file:
    #     reader = csv.DictReader(input_file)  # This reads the file into a dictionary format
    #     questions = []
    #     answers = []
    #     all_rows = []  # To store all rows with the updated scores
        
    #     # Loop through each row in the CSV
    #     for row in reader:
    #         question = row['question']
    #         judge_answer = row['judge_answer']
    #         questions.append(question)
    #         answers.append(judge_answer)
            
    #         # After every 5 questions, generate scores and store them
    #         if len(questions) == 5:
    #             scores = []
    #             # Assuming report_generator.generate_report(answers, questions) returns a result like 'question_score'
    #             report = await report_generator.generate_report(answers, questions)
    #             for question_score in report.questions_and_scores:
    #                 scores.append(question_score.score)
                
    #             # Append the score to each of the 5 rows
    #             for i in range(5):
    #                 row['llm_score'] = scores[i]  # Add the score to the row
    #                 all_rows.append(row.copy())  # Append a copy of the row with the new score

    #             # Reset questions and answers for the next batch of 5
    #             questions.clear()
    #             answers.clear()
    #     # Handle any remaining questions if the last batch has fewer than 5 questions
    # if questions:
    #     scores = []
    #     report = await report_generator.generate_report(answers, questions)
    #     for question_score in report.questions_and_scores:
    #         scores.append(question_score.score)
        
    #     # Add scores to the remaining rows
    #     for i in range(len(questions)):
    #         row = {
    #             'question': questions[i],
    #             'proper_answer': '',  # Leave this blank or fill in as needed
    #             'judge_answer': answers[i],
    #             'y_true': 0,  # Adjust this value as needed
    #             'llm_score': scores[i]  # Add the score for the remaining questions
    #         }
    #         all_rows.append(row)

    # with open(csv_filename_for_new, mode='w', newline='', encoding='utf-8') as output_file:
    #     writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        
    #     # Write the header
    #     writer.writeheader()
        
    #     # Write all the rows with the updated scores
    #     writer.writerows(all_rows)

    # print(f"Updated CSV saved to {csv_filename_for_new}")
    
    # # Simulate judge's answers
    # evaluated_data = evalauate_report(report)
    # print(evaluated_data)
    # sqlite_connection.close()

    # ... here i need to add evaluated data that is json to ouptut_cv

    # Write results to CSV
    # output_csv = 'benchmarking_results/benchmark_results_2.csv'
    # write_to_csv(output_csv, evaluated_data)
    
    # print(f"Evaluation results written to {output_csv}")

# Close the SQLite connection
# sqlite_connection.close()
asyncio.run(main())



# import os
# import csv
# from groq import Groq
# from utils import generate_content
# from modules.questions_generator import generate_question_prompt
# import json
# from database_manager import retrieve_context_from_chromadb, add_pdf_to_chromadb
# import chromadb
# from dotenv import load_dotenv
# import asyncio
# load_dotenv()

# # Define the list of 50 themes
# themes = [
#     "Supervised Learning", "Unsupervised Learning", "Reinforcement Learning", "Neural Networks", "Deep Learning",
#     "Convolutional Neural Networks", "Recurrent Neural Networks", "Natural Language Processing", "Computer Vision",
#     "Transfer Learning", "Generative Adversarial Networks", "Support Vector Machines", "Decision Trees", "Random Forests",
#     "Gradient Boosting", "K-Nearest Neighbors", "Clustering Algorithms", "Dimensionality Reduction", "Feature Engineering",
#     "Model Evaluation", "Hyperparameter Tuning", "Cross-Validation", "Overfitting and Underfitting", "Regularization Techniques",
#     "Ensemble Methods", "Time Series Analysis", "Anomaly Detection", "Bayesian Networks", "Markov Decision Processes",
#     "Reinforcement Learning Algorithms", "Sequence Models", "Attention Mechanisms", "Autoencoders", "Semi-Supervised Learning",
#     "Self-Supervised Learning", "Meta-Learning", "Multi-Task Learning", "Few-Shot Learning", "Zero-Shot Learning",
#     "Explainable AI", "Fairness in AI", "Ethics in AI", "AI in Healthcare", "AI in Finance", "AI in Autonomous Vehicles",
#     "AI in Robotics", "AI in Gaming", "AI in Natural Sciences", "AI in Social Sciences", "AI in Industry 4.0",
#     "How to Teach Machines to Learn (Basics of Supervised Learning)", "Exploring Data Without a Map (Intro to Unsupervised Learning)",
#     "Making Machines Smarter Through Rewards (Reinforcement Learning Explained)", "What Are Neural Networks",
#     "Deep Learning: The Next Level of Machine Learning", "Understanding How Image Recognition Works (CNNs Simplified)",
#     "Using Recurrent Networks to Understand Sequences (RNNs for Beginners)", "Making Sense of Human Language with Machines (Intro to NLP)",
#     "How Machines See the World (Computer Vision Basics)", "Applying What One Model Knows to Another (Transfer Learning Made Simple)",
#     "Creating Art with Machines (Understanding GANs)", "The Role of Support Vector Machines in Modern AI",
#     "Decision Trees and Why They’re Popular in ML", "Random Forests: A Forest Full of Decisions",
#     "Boosting Algorithms and Why They Improve Models", "K-Nearest Neighbors: A Simple Yet Powerful Tool",
#     "Grouping Data That Looks Similar (Clustering 101)", "Reducing Data Complexity (Dimensionality Reduction for All)",
#     "How to Select the Right Features (Feature Engineering Demystified)", "Evaluating Your Model’s Performance",
#     "How to Tune Your Model for the Best Results (Hyperparameter Tuning)", "Avoiding the Pitfalls of Overfitting and Underfitting",
#     "Understanding Regularization Techniques", "Combining Models for Better Results (Intro to Ensemble Methods)",
#     "Predicting Trends and Patterns (Time Series Analysis)", "Detecting Unusual Patterns in Data (Anomaly Detection)",
#     "What Are Bayesian Networks", "Markov Decision Processes and Where to Use Them", "Breaking Down Reinforcement Learning Algorithms",
#     "Getting to Know Sequence Models", "Attention Mechanisms: Why Your Model Needs to Focus", "How Autoencoders Help with Data Compression",
#     "The Power of Semi-Supervised Learning", "When Machines Teach Themselves (Self-Supervised Learning)",
#     "How Meta-Learning Can Make AI More Adaptive", "Handling Multiple Tasks with One Model (Multi-Task Learning)",
#     "Solving Problems with Minimal Data (Few-Shot Learning)", "AI That Understands Without Training (Zero-Shot Learning)",
#     "Explaining the Magic Behind AI (Explainable AI)", "Why Fairness in AI Matters", "Ethics in AI: Beyond Just Algorithms",
#     "Using AI to Revolutionize Healthcare", "AI’s Role in Finance and Banking", "The Tech Behind Self-Driving Cars (AI in Autonomous Vehicles)",
#     "Robots That Learn and Adapt (AI in Robotics)", "How AI Transforms Gaming Experiences", "AI’s Role in Scientific Discovery",
#     "Understanding Social Behaviors with AI (AI in Social Sciences)", "What Industry 4.0 Means for AI", "Why AI Needs Trustworthy Data",
#     "How Machines Learn to Negotiate (AI and Strategy)"
# ]

# client = chromadb.HttpClient(host='localhost', port=8000)
# chromadb_connection = client.get_or_create_collection(name="chromadb_final_2024")
# # add_pdf_to_chromadb('datasets/PDF_ML.pdf', chromadb_connection, theme='ML_EN')

# import asyncio

# async def generate_questions_for_testing(theme):
#     global chromadb_connection
#     # Use asyncio.to_thread to run the synchronous function in a separate thread
#     context_chunk = await asyncio.to_thread(retrieve_context_from_chromadb, theme, chromadb_connection, 1)
#     prompt = generate_question_prompt(context_chunk, 1)
#     question_response = await generate_content(prompt)  # This remains async
#     generated_question = question_response.strip().lstrip("```json").rstrip("```")
#     try:
#         generated_question = json.loads(generated_question.strip())
#     except json.JSONDecodeError:
#         generated_question = None
            
#     return context_chunk, generated_question

# # Function to generate content (questions)
# def evaluate_with_judge_1(chunk, generated_question):
#     prompt = f"You have only{generated_question} and return SINGLE NUMBER 1 if it is related to the next text: {chunk}, 0 otherwise."
#     GROQ_API_KEY = os.getenv('GROQ_API_KEY')
#     client = Groq(api_key=GROQ_API_KEY)
#     completion = client.chat.completions.create(  # Do NOT await here
#         model="llama-3.1-70b-versatile",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are program and you judje only returning 1 or 0",
#             },
#             {
#                 "role": "user",
#                 "content": prompt,
#             }
#         ],
#         temperature=1,
#         max_tokens=1024,
#         top_p=1,
#         stream=False,
#     )
#     result = completion.choices[0].message.content
#     return result

# async def main():
#     results = []
#     for theme in themes:
#         context_chunk, generated_question = await generate_questions_for_testing(theme)
#         is_related = evaluate_with_judge_1(context_chunk, generated_question)
#         results.append({"chunk": context_chunk, "theme": theme, "generated_question": generated_question, "is_related": is_related})

#     # Save results to a CSV file
#     with open('benchmarking_results/benchmark_results_1.csv', 'w', newline='') as csvfile:
#         fieldnames = ['chunk', 'theme', 'generated_question', 'is_related']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()
#         for result in results:
#             writer.writerow(result)

#     print("Benchmark results saved to benchmark_results.csv")

# # Run the main function with asyncio
# asyncio.run(main())