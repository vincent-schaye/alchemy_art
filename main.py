# main.py
import os
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

# Importing other modules
from story_generator import generate_bedtime_story
from utils import get_user_input
from vector_db_operation import summarize_and_upsert_story

def display_segment(segment):
    print("\n--- New Story Segment ---")
    print(segment['text'])
    if segment['images']:
        print("\nImages for this segment:")
        for image in segment['images']:
            print(f"- {image}")
    if segment['choices']:
        print("\nChoices:")
        for i, choice in enumerate(segment['choices'], 1):
            print(f"{i}. {choice}")


def main():
    user_id = get_user_input("Please enter your user ID")

    while True:
        print("\n--- Bedtime Story Menu ---\n")
        print("1. Start a new story")
        print("2. Continue from your previous story")
        print("3. Exit the program")
        choice = get_user_input("Choose an option (1, 2 or 3)").strip()

        if choice in ['1', '2', '3']:
            if choice in ['1', '2']:
                try:
                    # Generate the story with segments using the generator
                    story_generator = generate_bedtime_story(user_id, is_continued=(choice == '2'))

                    # Loop through the segments as they are yielded by the generator
                    for story_data in story_generator:
                        # Display each segment's text, images, and choices
                        print(f"\n{story_data['segments'][-1]['text']}\n")
                        print("Images used in this segment:", story_data['segments'][-1]['images'])
                        if story_data['segments'][-1]['choices']:
                            print("Choices:")
                            for i, choice in enumerate(story_data['segments'][-1]['choices'], 1):
                                print(f"{i}. {choice}")

                        # Check if the story is complete
                        if story_data.get('complete', False):
                            print("The story is complete.")
                            break

                except Exception as e:
                    print(f"Error generating story: {e}")
            else:
                print("Exiting the program. Goodbye!")
                break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()