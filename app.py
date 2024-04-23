import datetime  
import logging
import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAI


app = Flask(__name__)
logging.basicConfig(
    filename="log.txt",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
if app.debug:
    app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(logging.INFO)



# Load PDF document
def load_pdf(file_path):
    pdf_reader = PdfReader(file_path)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() 
    return text

# Split text into chunks
def split_text(text):
    text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len
    )  

    chunks = text_splitter.split_text(text)
    return chunks

# Create question-answering agent
def create_qa_agent(vector_store, query) :
    docs = vector_store.similarity_search(query)

    llm = OpenAI()
    chain = load_qa_chain(llm, chain_type="stuff")
    response = chain.run(input_documents=docs, question=query, return_source_documents=True,
    )
    return response
# Post answer to Slack
def post_answer_to_slack(slack_bot_url, response_payload):
    slack_response = requests.post(slack_bot_url, data = response_payload)
    return slack_response
@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    load_dotenv()
   
    request_in_time = datetime.datetime.now()
    request_json = request.json
    openai_api_key  = os.environ["OPENAI_API_KEY"]
    slack_bot_url = os.environ["SLACK_BOT_URL"]
   
    app.logger.info(f"Request In Time : {request_in_time}")
    app.logger.info(f"Request body : {request_json}")
    if not request_json:
        app.logger.info("Error: Invalid Request")
        return jsonify({"Status": 400, "Message": "Invalid Request"})
    try:
        file_path = request_json['QueryData']['FilePath']
        questions = request_json['QueryData']['Questions']
    except Exception as e:
        app.logger.info(f"Error: {str(e)}")
        return jsonify({"Status": 400, "Message": str(e)})
    

    if not file_path.lower().endswith(".pdf"):
        app.logger.info(f"Error: {str(e)}")
        return jsonify({"Status": 400, "Message": "Please use PDF file"})
    # Load PDF document
    documents = load_pdf(file_path)

    # Split text into chunks
    chunks = split_text(documents)
  
    # Generate embeddings
    try:
        embeddings = OpenAIEmbeddings()
    except Exception as e:
        app.logger.info(f"Error: {str(e)}")
        return jsonify({"Status": 400, "Message": str(e)})

    # Create vector store
    try :
        vector_store = FAISS.from_texts(chunks, embeddings)
        app.logger.info(f"Vectorization Successful")
    except Exception as e:
        app.logger.info(f"Error: {str(e)}")
        return jsonify({"Status": 400, "Message": str(e)})

    # Create question-answering agent
    response_json= []
    for query in questions:
       
        try:
            response = create_qa_agent(vector_store, query)
            app.logger.info(f"Question: {str(query)}, Response:{str(response)}")
        except Exception as e:
            app.logger.info(f"Error: {str(e)}")
            return jsonify({"Status": 400, "Message": str(e)})
        
        response = response.replace("'", "").replace('"', "")
        response_json.append({"Question":query, "Response":str(response)})
        
    # Posting response to Slack
    try:
        response_payload = '{"text":"%s"}' % response_json
        slack_response = post_answer_to_slack(slack_bot_url,response_payload)
        app.logger.info(f"Slack Response: {str(slack_response)}")
    except Exception as e:
        app.logger.info(f"Error: {str(e)}")
        return jsonify({"Status": 400, "Message": str(e)})
    
   
    response_out_time = datetime.datetime.now()
    app.logger.info(f"Response Out Time : {response_out_time}")
    app.logger.info(f"Response Body : {response_json}")
    app.logger.info("$"*100)
    return jsonify({"Status": 200, "Message": "Success", "Data":response_json})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port= 80)