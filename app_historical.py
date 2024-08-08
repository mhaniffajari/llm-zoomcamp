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

index_settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "text": {"type": "text"},
            "section": {"type": "text"},
            "question": {"type": "text"},
            "course": {"type": "keyword"} 
        }
    }
}
index_name = 'course_question_chatbot'
# Check if index exists and create if not
if not es_client.indices.exists(index=index_name):
    es_client.indices.create(index=index_name, body=index_settings)
else:
    pass

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
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(model='gpt-3.5-turbo-16k',messages = [{'role':'user',"content":prompt}])
    return response.choices[0].message.content


def rag(query):
    search_results = elastic_query(query)
    prompt = build_prompt(query, search_results)
    answer = llm_open_api(prompt)
    return search_results, prompt, answer

# Streamlit app
def main():
    st.title('RAG Chatbot')

    chat_history_file = 'chat_history.txt'

    # Load chat history from file
    if os.path.exists(chat_history_file):
        with open(chat_history_file, 'r') as f:
            chat_history = f.readlines()
    else:
        chat_history = []

    # Input box for user query
    user_input = st.text_input("You: ", "")

    if user_input:
        # Add user input to chat history
        with open(chat_history_file, 'a') as f:
            f.write(f"You: {user_input}\n")

        # Generate response using the RAG model
        search_results, prompt, response = rag(user_input)

        # Add bot response to chat history
        with open(chat_history_file, 'a') as f:
            f.write(f"Bot: {response}\n")

        # Append chat to history list
        chat_history.append(f"You: {user_input}")
        chat_history.append(f"Bot: {response}")

        # Display Answer
        st.subheader("Answer")
        st.text_area("Answer:", value=response, height=200, max_chars=None, key="answer_area")

    # Display chat history
    st.subheader("Chat History")
    for chat in chat_history:
        st.write(chat)

if __name__ == "__main__":
    main()
