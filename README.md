# PDF_QA_BOT**

## About the Project

This is a Python-based API that lets you upload a PDF and inquire about its content using advanced Language Learning Models (LLMs). The tool harnesses the power of an LLM to provide answers related to your PDF. The LLM is designed to disregard questions that are irrelevant to the document. The tool scans the PDF and breaks down the text into bite-sized pieces, which are then processed by an LLM. It leverages OpenAI's embedding technology to convert these pieces into vector representations. The tool then pinpoints the pieces that share a similar meaning with the user's question and uses them as input for the LLM to generate a response.  And finally posts the results to the slack channel. Here's a demonstration of the concept in action.


## Installation

1. Clone the repo
2. Install the requirements
3. run the app.py
Add your OpenAI API key to the .env file

## Input request format

`{
    "QueryData":{
    "Questions": ["Question1?", "Question2?"],
    "FilePath": "path to your pdf"
}
}`

