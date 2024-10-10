""" audio_generation.py 

Description
    The following file contains functions to deal with the audio elements 
    of the AlchemyArt project. 
    It uses the coquiTTS library to generate an audio file that has 
    a person of your choice (depending on the input files) read out 
    text.
"""




import torch
from TTS.api import TTS
import gradio as gr
import os 
import shutil
import io


# Setup 
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Directory with speaker audio files
speaker_dir = "./input_audio/"
output_dir = "./output_audio/"


  

def get_speaker_names():

    #if not speaker:
    #    raise ValueError("Speaker name is required.")

    # Gets list of all filenames form speaker_directory
    files_in_dirs = os.listdir(speaker_dir)
    all_speaker = [f for f in files_in_dirs if os.path.isfile(os.path.join(speaker_dir,f))]

    return all_speaker  # Output: list of strings (filenames)

def generate_audio(text,speaker: str):
    # function generates audio file in ./output_audio/ based on the text and input voice
    # returns string to audio file

    model_name = 'tts_models/multilingual/multi-dataset/xtts_v2'
    tts = TTS(model_name).to("cpu")
    audio_input  = speaker_dir + speaker
    audio_output = output_dir + "temp.wav"

    # generating the audio file based on xtts_v2
    tts.tts_to_file(text=text,
                    speaker_wav=audio_input,
                    language='en',
                    file_path=audio_output)
    
    return audio_output # path to output file 

def clean_out_output_audio():
    # Function to delete all files in the output_audio directory

    files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
    if not files:
        return

    # If there are files, delete them
    for filename in files:
        file_path = os.path.join(output_dir, filename)
        try:
            os.remove(file_path)
            print(f"Deleted {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

#def save_recording():
#    # Function to save new Speaker



