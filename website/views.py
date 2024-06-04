from flask import Blueprint, render_template,redirect,url_for,request, flash,Flask
from flask_login import login_required
# from dotenv import load_dotenv
import os
# from website import db,create_app
import subprocess
import webbrowser
from langchain_community.document_loaders import AssemblyAIAudioTranscriptLoader
import os
# from langchain import HuggingFaceHub
# from langchain.llms import GooglePalm
from flask import jsonify, request
import sys


import asyncio
# import chainlit as cl
import requests
from dotenv import load_dotenv
from flask_restful import Resource
# import torch
load_dotenv()


palm_api_key=os.environ.get('PALM_API_TOKEN')
# huggingface_api_token=os.environ.get('HUGGINGFACEHUB_API_TOKEN')
# print(palm_api_key)

# relativePath=os.getcwd()
# absPath='\\Database\\qna.csv'
# print((relativePath+absPath).replace('\\','\\\\'))
# repo_id='HuggingFaceH4/zephyr-7b-alpha'












# load_dotenv()

# client_id= os.getenv("CLIENT_ID")
# client_secret = os.getenv("CLIENT_SECRET")

views = Blueprint('views', __name__)


@views.route("/",methods=["POST","GET"])
def home():
    if request.method=="GET":
        return render_template("home.html")
@views.route("/termsandconditions",methods=["POST","GET"])
def termsandconditions():
    return render_template('termsNconditions/T&C.html')


# @views.route('/streamlit')
# def run_streamlit():
#     try:
#         # subprocess.Popen(["streamlit", "run", "streamlitchatbot.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
#         # webbrowser.open("http://localhost:8501")
#         return render_template("chatbot/chatbot.html")
#     except Exception as e:
#         return f"Error: {str(e)}"




huggingface_api_token=os.environ.get('HUGGINGFACEHUB_API_TOKEN')
assemblyai_key_token=os.environ.get('ASSEMBLY_AI_KEY')
palm_api_key=os.environ.get('PALM_API_TOKEN')
repo_id='HuggingFaceH4/zephyr-7b-alpha'

# llm= GooglePalm(google_api_key=palm_api_key, temperature=0.7)
# def transcriber(audio_path):
    

#         return transcription

import assemblyai as aaii
from assemblyai.transcriber import Transcriber
@views.route('/transcribe', methods=["GET","POST"])
async def transcribe_audio():
    if request.method=="GET":
        return render_template("transcriber/transcribe.html")
    if request.method=="POST":
            aaii.settings.api_key=os.environ['ASSEMBLY_AI_KEY']
            # Extract audio file name from the request
            audio_file = request.files['audio_file']
            # Save the uploaded file temporarily
            audio_path = os.path.join(os.getcwd(), 'website\\static\\music', audio_file.filename)
            
            audio_file.save(audio_path)

            transcriber = Transcriber()
            # transcript = await asyncio.to_thread(transcriber.transcribe(audio_path))
            transcript = transcriber.transcribe(audio_path)
            print("reached")


            
            loader = AssemblyAIAudioTranscriptLoader(file_path=audio_path, api_key=assemblyai_key_token)
            docs = loader.load()
            print("transcribed")

            if docs and docs[0].page_content:
                transcription = docs[0].page_content
                print("hello")
                print(transcription)

                os.remove(audio_path)

            
            print(audio_path)
            
            # print(transcript.text)

            return jsonify({"transcription":transcript.text})
            # return data, render_template("transcriber/transcribe.html", data=data)


from .chatbot import mushifyllm


@views.route('/mushifyllm/chat', methods=["GET","POST"])
async def mushifyllm_view():
    if request.method == "GET":
        return render_template("chatbot/chatbot.html")
    elif request.method=="POST":
        input = request.get_json()
        message = input.get('message','')
        print(message)
        reply = mushifyllm(message)
        reply = await asyncio.to_thread(mushifyllm, message)
        print(reply)
        return jsonify({'reply':reply})
        

from openai import OpenAI


@views.route('/generatecover', methods=["GET","POST"])
async def generateimage():
    if request.method=="GET":
        return render_template("transcriber/transcribe.html")
    if request.method=="POST":
        input=request.form['prompt']
        print(input)
        api_key=os.environ.get('OPENAI_API_KEY')
        print(api_key)
        client = OpenAI(api_key=api_key)

        response = client.images.generate(
        model="dall-e-3",
        prompt=input,
        size="1024x1024",
        quality="standard",
        n=1,
        )

        image_url = response.data[0].url
        print("Generated image url: ", image_url)
        return jsonify({'imgUrl':image_url})






@views.route('/verifycreator', methods=["GET","POST"])
@login_required
def verifydetails():
    if request.method=="GET":
        return render_template("verifiedfeature/verify.html")
    

#######################################################################################
#Apis
from .models import Song, Album
from . import api
# class GetDataResource(Resource):
#     def get(self):
#         print('hello')
#         songs = Song.query.all()
#         albums=Album.query.all()
#         song_data=[{'id': song.id, 'songname': song.name, 'songartist': song.artist, 'genre' : song.genre, 'like_count': song.likes} for song in songs]
#         album_data=[{'id': album.id, 'albumname': album.name , 'creatorname': album.creator_name, 'genre': album.genre, 'likes_count': album.like} for album in albums]
#         response_data={'songs': song_data, 'albums': album_data}
#         return jsonify(response_data)
# api.add_resource(GetDataResource, '/api/getdata')
@views.route('/api/getdata', methods=['GET'])
def getdata():
        if request.method=='GET':
            songs = Song.query.all()
            albums=Album.query.all()
            song_data=[{'id': song.id, 'songname': song.name, 'songartist': song.artist, 'genre' : song.genre, 'like_count': song.likes} for song in songs]
            album_data=[{'id': album.id, 'albumname': album.name , 'creatorname': album.creator_name, 'genre': album.genre, 'likes_count': album.like} for album in albums]
            response_data={'songs': song_data, 'albums': album_data}
            return jsonify(response_data)





   