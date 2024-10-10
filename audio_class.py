import torch
from TTS.api import TTS
#import gradio as gr
import os 
import shutil
import soundfile as sf
import io



class AudioGenerator:
    """
    This class is used to store all the nessecary Variables for the audio generation part
    of the Project AlchemyArt. It uses the coquiTTS Library for all the audio generation
    and Modeltraining.
    The Model used is set to the xtts_v2. Only Set to use the english language.
    """


    ############ Constructor ############
    
    def __init__(self):
        

        # Member variables
        self.tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to(device="cpu")
        self.speaker_dir = "./input_audio/"
        self.all_speaker = ""
        self.text = ""       
        self.speaker_wav = io.BytesIO()  
        self.audio = io.BytesIO()
 
        # Testing here #--------------------------------
        self.audio = self.tts.tts(text="This is some sample text",
                                  speaker_wav=self.speaker_dir + "Okan_voice_sammple.wav",
                                  language="en",
                                  file_path=self.audio)

        self.audio.seek(0)        


        # Initialize all the nessecary TTS parameters
        # tts_models/multilingual/multi-dataset/xtts_v2


    ############ Member functions ############

    # TODO: Check if the speaker drop down return the names with the extension .wav or not
    def set_speaker(self,new_speaker = "Okan_voice_sample.wav"):
        speaker = self.speaker_dir + new_speaker
        self.speaker_wav, sample_rate = sf.read(speaker)
    
    # this method assignes an audio value to the audio member variable
    def generate_audio(self,text):
        
        # Convert to a format Gradio can handle (16-bit PCM, 22050 Hz)
        wav = TTS.tts(self.text)
        self.audio = sf.write(self.audio,wav,22050,format="WAV")
        self.seek(0)    # Reset the pointer to the beginning of the buffer

    # Returns file names (with extensions) of all files in  self.speaker_dir directory
    def get_speaker_names(self):
        files_in_dirs = os.listdir(self.speaker_dir)
        self.all_speaker = [f for f in files_in_dirs if os.path.isfile(os.path.join(self.speaker_dir,f))]

        return self.all_speaker
    
    #def play_audio(self):
    #    self.
    






#class AudioGenerator:
#
#    def __init__(self, model_path: str, speaker_dir: str):
#        """
#        Initialize the TTS generator with the specified model and speaker directory.
#        :param model_path: Path to the TTS model (xtts-v2).
#        :param speaker_dir: Directory containing speaker embeddings or voice samples.
#        """
#        
#
#        self.model = TTS(model_path)  # Initialize the TTS model.
#        self.speaker_dir = "./input_audio/"  # Directory where speaker embeddings are stored.
#        self.current_speaker = None  # Placeholder for current speaker.
#        self.speaker = self._load_speakers()  # Load all available speakers from the directory.
#
#
#    def set_speaker(self, speaker_names):
#        self.speaker_dir  
#
#    
#    def get_speaker_names(self):
#        # get the names for the dropdown menu
#
#        speaker_files = os.listdir(self.speaker_dir)
#        # assuming files are named like "Name_voice_sample.wav" // os.path.splitext(file)[0]
#        speaker_names = [os.path.splitext(file)[0] for file in speaker_files if file.endswith('.wav')]
#        return speaker_names
#
#
#    def generate_audio(self,text,speaker):
#        
#    # speaker setup
#        speaker_wav = os.path.join(speaker_directory, f"{speaker}.wav")






#    def set_speaker(self, speaker_wav):
#        """
#        Set the path to the speaker's voice sample for voice cloning.
#        
#        Parameters:
#            speaker_wav (str): Path to the speaker's voice sample (WAV file).
#        """
#        if os.path.exists(speaker_wav):
#            self.speaker_wav = speaker_wav
#        else:
#            raise FileNotFoundError(f"Speaker file {speaker_wav} does not exist.")
#
#
#
#    def generate_audio(self, text):
#        """
#        Generate audio from the given text using the loaded TTS model.
#        
#        Parameters:
#            text (str): The text to convert into speech.
#            
#        Returns:
#            BytesIO: An in-memory WAV file as a BytesIO object.
#        """
#        
#        if self.speaker_wav:
#            # Generate audio with the specified speaker voice sample
#            wav = self.model.tts(text, speaker_wav=self.speaker_wav)
#        else:
#            # Generate audio without a speaker sample (default model voice)
#            wav = self.model.tts(text)
#        
#
#        # Generate audio waveform (NumPy array)
#        wav = self.model.tts(text)
#        
#        # Write the audio to an in-memory buffer (BytesIO) in WAV format
#        wav_bytes_io = io.BytesIO()
#        sf.write(wav_bytes_io, wav, self.sample_rate, format='WAV')
#        
#        # Reset the buffer pointer to the beginning
#        wav_bytes_io.seek(0)
#        
#        return wav_bytes_io
#    
#
#
#    def save_audio_to_file(self, text, file_path):
#        """
#        Generate audio from the given text and save it to a file.
#        
#        Parameters:
#            text (str): The text to convert into speech.
#            file_path (str): The path where the audio file should be saved.
#        """
#        # Generate the audio waveform
#        if self.speaker_wav:
#            wav = self.model.tts(text, speaker_wav=self.speaker_wav)
#        else:
#            wav = self.model.tts(text)
#        
#        # Save the audio to a WAV file
#        sf.write(file_path, wav, self.sample_rate, format='WAV')
#        print(f"Audio saved to {file_path}")
