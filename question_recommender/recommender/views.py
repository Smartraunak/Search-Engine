import pandas as pd
import re
from math import log
from django.shortcuts import render
import os

# ...

csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'codeforces.csv')
data = pd.read_csv(csv_path)
# ...

# Clean the question descriptions and question names by removing special characters and converting to lowercase
data['Cleaned Description'] = data['Question Description'].apply(lambda x: re.sub(r'\W+', ' ', x.lower()))
data['Cleaned Name'] = data['Question Name'].apply(lambda x: re.sub(r'\W+', ' ', x.lower()))

# Calculate the document frequency (DF) for each term in the question descriptions and names
document_frequency = {}
for _, row in data.iterrows():
    terms = set(row['Cleaned Description'].split() + row['Cleaned Name'].split())
    for term in terms:
        document_frequency[term] = document_frequency.get(term, 0) + 1

# Calculate the inverse document frequency (IDF) for each term
inverse_document_frequency = {}
total_documents = len(data)
for term, df in document_frequency.items():
    inverse_document_frequency[term] = log(total_documents / (1 + df))

# Precompute the TF-IDF scores for each question
questions_tf_idf = {}
for idx, row in data.iterrows():
    question_terms = set(row['Cleaned Description'].split() + row['Cleaned Name'].split())
    question_tf_idf = {}
    for term in question_terms:
        term_frequency = row['Cleaned Description'].count(term) + row['Cleaned Name'].count(term)
        tf_idf_score = term_frequency * inverse_document_frequency[term]
        question_tf_idf[term] = tf_idf_score
    questions_tf_idf[idx] = question_tf_idf

# ...

def index(request):
    return render(request, 'index.html')

def recommend_questions(request):
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')  # Get the user input from the form

        # Clean the user input by removing special characters and converting to lowercase
        cleaned_user_input = re.sub(r'\W+', ' ', user_input.lower())

        # Calculate the TF-IDF scores for each term in the user input
        query_terms = cleaned_user_input.split()
        query_tf_idf = {}
        for term in query_terms:
            term_frequency = cleaned_user_input.count(term)
            query_tf_idf[term] = term_frequency * inverse_document_frequency.get(term, 0)

        # Calculate the similarity scores between the user input and each question
        similarities = []
        for idx, question_tf_idf in questions_tf_idf.items():
            similarity = sum(min(query_tf_idf.get(term, 0), question_tf_idf.get(term, 0)) for term in query_terms)
            similarities.append(similarity)

        # Create a DataFrame to store the question indices and similarities
        df_similarities = pd.DataFrame({'Question Index': data.index, 'Similarity': similarities})

        # Sort the DataFrame by similarity in descending order
        df_similarities = df_similarities.sort_values('Similarity', ascending=False)

        # Get the top 3 most similar questions
        top_questions = []
        for index in df_similarities['Question Index'][:9]:
            question = {
                'name': data['Question Name'][index],
                'url': data['Question Url'][index],
                'description':data['Question Description'][index]
            }
            top_questions.append(question)

        context = {'top_questions': top_questions, 'user_input': user_input}
        return render(request, 'return.html', context)

    return render(request, 'index.html')

# Create your views here.
