from flask import Blueprint, render_template,redirect,url_for,request, flash,Flask
# from dotenv import load_dotenv
import os
from urllib.parse import quote
# from website import db,create_app
from flask_mail import Mail
import subprocess
import webbrowser
import os
# from langchain import HuggingFaceHub
# from langchain.llms import GooglePalm

from flask import jsonify, request
import sys

import os
from langchain.memory import ConversationSummaryBufferMemory
import requests
from dotenv import load_dotenv
# import torch
load_dotenv()


palm_api_key=os.environ.get('PALM_API_TOKEN')

huggingface_api_token=os.environ.get('HUGGINGFACEHUB_API_TOKEN')
assemblyai_key_token=os.environ.get('ASSEMBLY_AI_KEY')
palm_api_key=os.environ.get('PALM_API_TOKEN')
repo_id='HuggingFaceH4/zephyr-7b-alpha'




from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.llms.google_palm import GooglePalm
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, CSVLoader,PyPDFDirectoryLoader, PyPDFLoader
from langchain_community.document_loaders.merge import MergedDataLoader
from langchain.chains.question_answering import load_qa_chain
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.vectorstores.deeplake import DeepLake
from langchain_community.vectorstores.annoy import Annoy
from langchain.chains import RetrievalQA, ConversationChain, ConversationalRetrievalChain
from langchain_community.embeddings.google_palm import GooglePalmEmbeddings
from langchain_community.embeddings.huggingface_hub import HuggingFaceHubEmbeddings
from langchain_community.embeddings.huggingface import HuggingFaceInferenceAPIEmbeddings
from langchain_community.embeddings.voyageai import VoyageEmbeddings
from langchain_community.embeddings.gpt4all import GPT4AllEmbeddings
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
load_dotenv()
import pprint
palm_api_key = os.environ.get('PALM_API_TOKEN')
# jarvispath=(os.getcwd()).split("Agentfuncs")
# file_path=os.path.join(jarvispath[0],"Database","PersonalData")
currentpath=os.getcwd()
database_path= os.path.join(currentpath,"website","Database")
print(database_path)
def makevectorembeddings():
    palm_api_key = os.environ.get('PALM_API_TOKEN')
    # current_path = os.getcwd()
    llm = GoogleGenerativeAI(model="gemini-pro",google_api_key=palm_api_key,temperature=0)
        

        # Load data and create vector store for deep search
    
    loader = DirectoryLoader(database_path, glob="*.txt", show_progress=True)

    loader2  = PyPDFDirectoryLoader(database_path,glob = "**/[!.]*.pdf")
    merged_data_loader = MergedDataLoader([loader,loader2])
    # data = loader.load()
    # data2= loader2.load()
    data = merged_data_loader.load()
    # print(len(data))

    # print(type(data),type(data2))
    # document_string=str(data)
    # print(document_string)
    # if len(document_string) > 5000:
    #     mididx = len(document_string)//2
    #     document_string = document_string[0:]


    # print(document_string)

    text_splitter = CharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=500,
        length_function=len
    )

    print(len(data))
    chunks = text_splitter.split_documents(documents=data)
    # print(chunks, type(chunks), len(chunks))
    print(len(chunks))
    for ele in chunks:
        print(ele)
        print("#######################################################################")
    # print(chunks)
    # print(len(str(chunks)))
    embedding_list=[HuggingFaceHubEmbeddings(huggingfacehub_api_token=os.environ.get('HUGGINGFACEHUB_API_TOKEN')),
                    GooglePalmEmbeddings(google_api_key=palm_api_key),
                    GPT4AllEmbeddings(),
                    HuggingFaceInferenceAPIEmbeddings(api_key=os.environ.get('HUGGINGFACEHUB_API_TOKEN'),model_name="BAAI/bge-base-en-v1.5")
                   ]
    embeddings= embedding_list[1]
    print(embeddings)

    # vector_stores = FAISS.from_texts(chunks, embedding=embeddings)
    vector_stores = FAISS.from_documents(documents=chunks, embedding=embeddings)
    # retriever = vector_stores.as_retriever(score_threshold = 0.7)
    #similarity search
    # similardata = vector_stores._similarity_search_with_relevance_scores(query="What is the schedule on 25th January?",search_kwargs={'K' : 6})
    # print(similardata)
    # chain = load_qa_chain(llm=llm, chain_type="stuff")
    # response = chain.run(input_documents=similardata, question=input)
    return (vector_stores, data)








# print(makevectorembeddings())


import pickle

def savevectorstores(vector_stores):
    serialized_data = vector_stores.serialize_to_bytes()
    serialized_path=os.path.join(database_path,'serialized_index.pkl')
    with open(serialized_path, "wb") as file:
        pickle.dump(serialized_data, file)

    return type(serialized_data)


def loadvectorstores():
    serialized_path=os.path.join(database_path,'serialized_index.pkl')
    with open(serialized_path, "rb") as file:
        serialized_faiss = pickle.load(file)
    embeddings = GooglePalmEmbeddings(google_api_key=palm_api_key)
    vector_stores = FAISS.deserialize_from_bytes(serialized_faiss , embeddings=embeddings)

    return vector_stores


def create_save_vector_stores():
    vector_stores,data=makevectorembeddings()
    savevectorstores(vector_stores=vector_stores)
    vector_stores_pickled=loadvectorstores()
    return vector_stores_pickled

from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
def promptformatter():

    # Define the input variables and template for the prompt
    input_variables = ['context', 'input','memory','current_time','extra_data']
    template =""" You are an ai assistant of a company called mushify. It is a music streaming platform like spotify. Your job is to interact with the users and answer their questions from the documents given to you.
    You are built by Shaun Stark who is the CEO of the company currently.
    You have memory of the conversation with current user inside memory : {memory}.

    \nQuestion: {input},\n\n
    Context: {context},\n\n
    Extra Data: {extra_data},\n
    Answer:"""
    print(template)

    # Create a new HumanMessagePromptTemplate with the modified prompt
    human_message_template = HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=input_variables, template=template))

    # Create a new ChatPromptTemplate with the modified HumanMessagePromptTemplate
    chat_prompt_template = ChatPromptTemplate.from_messages([human_message_template])
    # print(chat_prompt_template)
    return chat_prompt_template


last_update_time=0
print('execiuted')
vector_stores = loadvectorstores()
print('execiuted')
docs=[]
from langchain.chains import StuffDocumentsChain, ConversationalRetrievalChain, LLMChain, create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from datetime import datetime
import time

def mushifyllm(query):
    global vector_stores
    global last_update_time
    global docs
    print(f"\nquery inside retrievalchainbot {query}")
    palm_api_key=os.environ.get('PALM_API_TOKEN')
    openai_api_key=os.environ.get('OPENAI_API_KEY')
    llm = ChatGoogleGenerativeAI(google_api_key=palm_api_key, model="gemini-pro", temperature=0.5, verbose=True)
    # llm = ChatOpenAI(api_key=openai_api_key, verbose=True, temperature=0.2,)
    # llm = ChatOpenAI(model="gpt-3.5-turbo",api_key=openai_api_key, temperature=0)
    current_time = time.time()
    
    elapsed_time = current_time - last_update_time
    print(f"elapsed_time :{elapsed_time}")
    if elapsed_time >= 1800:
        last_update_time=current_time
        vector_stores=create_save_vector_stores()

    
    retriever = vector_stores.as_retriever(search_type="mmr",search_kwargs={'k': 5, 'fetch_k': 50})
    similardata = vector_stores.similarity_search(query=query,k=6)
    # print(similardata,"similardata")
    # print(similardata)
    # print(docs)
    similar_data=''
    for ele in similardata:
        similar_data = similar_data+ele.page_content+'\n'

        # print(ele)
        # print("##########################")

    print("similar_data", similar_data)
    chat_context = docs
    print(chat_context)
     
    # retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    retrieval_qa_chat_prompt = promptformatter()
    # print(retrieval_qa_chat_prompt)
    combine_docs_chain = create_stuff_documents_chain(
    llm=llm, prompt=retrieval_qa_chat_prompt
    )
    current_time=datetime.now().strftime('%d/%m/%Y,%H:%M:%S')
    # print(type(combine_docs_chain), type(retriever))
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
    result = retrieval_chain.invoke({"input" : query , "memory" : chat_context[len(chat_context)-1:][::-1], "current_time":current_time , "extra_data" : similar_data} )
    docs.append({"question by user" : query , "mushify bot response" : result['answer']})
    # print(result)
    print(f'from retrievalchatbot {result["answer"]}')

    return result['answer']
# def mushifyllm(input=""):
#         output=retrievalchainbot(query=input)
#         print(output)
#         llm= GooglePalm(google_api_key=palm_api_key, temperature=0.5)
#         # llm = HuggingFaceHub(huggingfacehub_api_token=huggingface_api_token,
#         #              repo_id=repo_id, 
#         #              model_kwargs={"temperature":0.5, "max_new_tokens":2000})
#         memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)
#         memory.save_context({"input":input},{"output": output})
#         memory.load_memory_variables({})
#         print(memory.load_memory_variables({}))
#         print(memory.buffer)
#         conversation = ConversationChain(
#             llm=llm,
#             memory=memory,
#             verbose=True,
#         )
#         reply = conversation.predict(input=input)
#         print(reply)

#         return reply
    
# print(mushifyllm("Are you trained by Mushify?"))
# while True:
#     myinp=input()
#     print(myinp)
#     mushifyllm(myinp)