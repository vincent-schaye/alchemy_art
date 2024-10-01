import os
import tiktoken
import nltk
from typing import List

# Initialize tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

# Environment variables
WORDS_PER_MINUTE = int(os.getenv("WORDS_PER_MINUTE", "100"))

def get_user_input(prompt_text: str) -> str:
    while True:
        try:
            print(f"\n{prompt_text}")  # Print the prompt on a new line
            return input("Your input: ").strip()
        except EOFError:
            print("Error reading input. Please try again.")
"""
@ LINH we do not use this anymore. story_generator just needs the List directly from your module holding the titles of the images from current user input. 
so: image_description = ["flying-purple-dragon", "enchanted-forest", "magical-unicorn"]

def get_image_descriptions() -> List[str]:
    # Placeholder function - replace with actual image generation logic
    return ["flying-purple-dragon", "enchanted-forest", "magical-unicorn"]
"""
def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))

def estimate_reading_time(text: str) -> float:
    word_count = len(text.split())
    return word_count / WORDS_PER_MINUTE

def clean_text(text: str) -> str:
    text = text.strip()  # Remove leading/trailing whitespace
    text = ' '.join(text.split())  # Remove extra spaces between words
    sentences = nltk.sent_tokenize(text)
    cleaned_sentences = []
    for sentence in sentences:
        # Remove any trailing ellipsis
        while sentence.endswith('...') or sentence.endswith('..'):
            sentence = sentence.rstrip('.')
        # Ensure the sentence ends with proper punctuation
        if not sentence.endswith(('.', '!', '?')):
            sentence += '.'
        cleaned_sentences.append(sentence)
    return ' '.join(cleaned_sentences)