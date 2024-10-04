import torch
from TTS.api import TTS
import gradio as gr
import os 
import shutil


# Setup 
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Directory with speaker audio files
speaker_directory = "./input_audio/"
output_directory = "./output_audio/"



def get_speaker_names():
    # get the names for the dropdown menu

    speaker_files = os.listdir(speaker_directory)
    # assuming files are named like "Name_voice_sample.wav" // os.path.splitext(file)[0]
    speaker_names = [os.path.splitext(file)[0] for file in speaker_files if file.endswith('.wav')]
    return speaker_names

def save_recording(audio_file_path):
    # function saves user recordings to the speaker directory

    if audio_file_path is None:
        return "No audio file recorded."

    new_file_path = os.path.join(speaker_directory, 'user_voice.wav')

    shutil.move(audio_file_path,new_file_path)
    
    return f"saved new voice as 'user_voice_wav'."

def generate_audio(text,speaker):
    # TTS function

    model_manager = TTS().list_models()
    tts_models = model_manager.list_tts_models()
    
    # load in model
    tts = TTS(tts_models[0]).to('cpu')

    # File setup
    speaker_wav = os.path.join(speaker_directory, f"{speaker}.wav")


    # check if the speaker file exists before trying to process it
    if not os.path.exists(speaker_wav):
        raise FileNotFoundError(f"Speaker audio file {speaker_wav} does not exist.")

    audio_output = 'output_audio/gen_audio_1.wav'

    # generate audio using the selected speaker
    tts.tts_to_file(text=text, speaker_wav=speaker_wav, language='en', file_path=audio_output)

    return audio_output

def refresh_speaker_list():
    # refresh dropdown menu 
    return gr.Dropdown.update(choices=get_speaker_names())

