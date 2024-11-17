import os
import csv
from groq import Groq
from utils import generate_content
from modules.questions_generator import generate_question_prompt
import json
from database_manager import retrieve_context_from_chromadb, add_pdf_to_chromadb
import chromadb
from dotenv import load_dotenv
load_dotenv()

# Define the list of 50 themes
themes = [
    "Supervised Learning", "Unsupervised Learning", "Reinforcement Learning", "Neural Networks", "Deep Learning",
    "Convolutional Neural Networks", "Recurrent Neural Networks", "Natural Language Processing", "Computer Vision",
    "Transfer Learning", "Generative Adversarial Networks", "Support Vector Machines", "Decision Trees", "Random Forests",
    "Gradient Boosting", "K-Nearest Neighbors", "Clustering Algorithms", "Dimensionality Reduction", "Feature Engineering",
    "Model Evaluation", "Hyperparameter Tuning", "Cross-Validation", "Overfitting and Underfitting", "Regularization Techniques",
    "Ensemble Methods", "Time Series Analysis", "Anomaly Detection", "Bayesian Networks", "Markov Decision Processes",
    "Reinforcement Learning Algorithms", "Sequence Models", "Attention Mechanisms", "Autoencoders", "Semi-Supervised Learning",
    "Self-Supervised Learning", "Meta-Learning", "Multi-Task Learning", "Few-Shot Learning", "Zero-Shot Learning",
    "Explainable AI", "Fairness in AI", "Ethics in AI", "AI in Healthcare", "AI in Finance", "AI in Autonomous Vehicles",
    "AI in Robotics", "AI in Gaming", "AI in Natural Sciences", "AI in Social Sciences", "AI in Industry 4.0"
]

client = chromadb.HttpClient(host='localhost', port=8000)
chromadb_connection = client.get_or_create_collection(name="chromadb_final_2024")
# Add PDF to ChromaDB
add_pdf_to_chromadb('datasets/PDF_ML.pdf', chromadb_connection, theme='ML_EN')

async def generate_questions_for_testing():
    global chromadb_connection
    context_chunks = retrieve_context_from_chromadb(query=theme, collection=chromadb_connection, n_results=1)
    prompt = generate_question_prompt(context_chunks, 1)
    questions_response = await generate_content(prompt)
    questions_response = questions_response.strip().lstrip("```json").rstrip("```")
    try:
        question_data = json.loads(questions_response.strip())
    except json.JSONDecodeError:
        question_data = None
            
    return question_data

# Function to generate content (questions)
def judge_1(theme, question_data):
    print(question_data)
    prompt = f"Evaluate {question_data} and return SINGLE NUMBER 1 if it is related to the theme: {theme}, 0 otherwise."
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
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
    return completion['choices'][0]['message']['content']

# Generate questions and evaluate them
results = []
for theme in themes:
    question = generate_content(theme)
    is_related = judge_1(theme, question)
    results.append({"chunk": theme, "theme": theme, "generated_question": question, "is_related": is_related})

# Save results to a CSV file
with open('benchmark_results.csv', 'w', newline='') as csvfile:
    fieldnames = ['chunk', 'theme', 'generated_question', 'is_related']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        writer.writerow(result)

print("Benchmark results saved to benchmark_results.csv")