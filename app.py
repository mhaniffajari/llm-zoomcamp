import streamlit as st
from openai import OpenAI
import os
import json
from elasticsearch import Elasticsearch

# Initialize Elasticsearch client
es_client = Elasticsearch('http://127.0.0.1:9200')

# Environment variables
api_key = os.getenv('OPEN_AI_API_KEY')
if not api_key:
    st.error("OPEN_AI_API_KEY environment variable is not set.")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Load documents
with open('documents.json', 'rt') as f_in:
    docs_raw = json.load(f_in)
documents = []

for course_dict in docs_raw:
    for doc in course_dict['documents']:
        doc['course'] = course_dict['course']
        documents.append(doc)

# Ensure Elasticsearch index exists
index_name = 'your_index_name_here'  # Set your index name here
if not es_client.indices.exists(index=index_name):
    es_client.indices.create(index=index_name)

# Index documents
for doc in documents:
    es_client.index(index=index_name, document=doc)

def elastic_query(query):
    search_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question^3", "text", "section"],
                        "type": "best_fields"
                    }
                },
                "filter": {
                    "term": {
                        "course": "data-engineering-zoomcamp"
                    }
                }
            }
        }
    }
    response = es_client.search(index=index_name, body=search_query)
    result_docs = [hit['_source'] for hit in response['hits']['hits']]
    return result_docs

def build_prompt(query, search_results):
    prompt_template = """
    You are Course Assistant. You answer the question based on context. Use only fact the CONTEXT for answering the question.
    
    QUESTION: {question}
    CONTEXT : 
    {context}
    """.strip()
    context = ""
    for doc in search_results:
        context += f"section: {doc['section']}\nquestion: {doc['question']}\nanswer: {doc['text']}\n\n"
    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt

def llm_open_api(prompt):
    response = client.chat.completions.create(model='gpt-3.5-turbo-16k',messages = [{'role':'user',"content":prompt}])
    return response.choices[0].message.content

def rag(query):
    search_results = elastic_query(query)
    prompt = build_prompt(query, search_results)
    answer = llm_open_api(prompt)
    return answer

# Streamlit app
def main():
    st.title('RAG Chatbot')

    user_input = st.text_input("You: ", "")

    if user_input:
        # Generate response using the RAG model
        response = rag(user_input)
        st.text_area("Bot:", value=response, height=300, max_chars=None, key=None)

if __name__ == "__main__":
    main()
