import os
from dotenv import load_dotenv
from utils import estimate_reading_time, clean_text
from typing import Dict, List, Optional, Tuple
from vector_db_operation import retrieve_and_continue_story
# from LINH import image_description @ LINH

# OpenAI and ChatGPT
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Placeholder for now to test everything else working
image_description = ["eye-monster", "magic-cupcake", "purple-unicorn"] # this is a placeholder for now until Linh import above works for image_description list.



def create_system_prompt(user_data: Dict[str, any]) -> str:
    continuation_reminder = "This is a continuation of a previous story. Refer to elements from the previous adventures when appropriate." if user_data.get(
        'is_continued') else ""
    return f"""
    You are a storyteller creating an interactive bedtime story for young children.
    {continuation_reminder}
    Each segment of the story should be detailed but brief, creating vivid scenes and interactions for the main character.
    The story should be {user_data['tone']} and teach a moral lesson about {user_data['moral']}.
    Keep the language simple and appropriate for a {user_data['age']}-year-old.
    Each segment should be approximately 1 minute long when read aloud.
    End each segment with a clear decision point where the user has to make a choice for the main character.
    Provide exactly three distinct options for the next steps the character can take, related to the story and the moral.
    Format the options as follows:
    \n\nWhat will {user_data['name']} do next?\n
    1. [First option]\n
    2. [Second option]\n
    3. [Third option]\n
    The entire story should be approximately {user_data['length']} minutes long when read aloud.
    """


def create_initial_prompt(user_data: Dict[str, any], is_continued: bool) -> str:
    if is_continued:
        return (f"Continue the story of {user_data['name']} in {user_data['place']}. "
                f"Here's a summary of what happened before: {user_data.get('summary', 'No previous summary available')}. "
                f"Now, let's pick up the story and see what new adventures await {user_data['name']}.")
    else:
        return f"Start a brief bedtime story about {user_data['name']} in {user_data['place']}. Opening segment should end with a need for the main character to make a choice."


def generate_story_part(messages: List[Dict[str, str]], name: str, unused_images: List[str], max_tokens: int = 300,
                        is_final: bool = False, is_continued: bool = False) -> Tuple[
    str, int, List[str], List[str], List[str]]: # Receives the unused_images list

    print(f"** DEBUG: generate_story_part called with is_final={is_final}")

    # function here incorproates up to two images from unused_images. These image descriptions are included in the prompt sent to the AI
    image_prompt = f"In this segment, incorporate these elements: {', '.join(unused_images[:2])}" if unused_images else "Continue the story without introducing new visual elements."

    if is_final:
        messages.append({
            "role": "system",
            "content": f"{image_prompt} This is the final part of the story. Provide a complete and satisfying conclusion that wraps up all plot points and reinforces the moral of the story. Ensure all sentences are complete. Do not include any choices, questions, or decision points. The story should end here without any further user input."
        })
    elif is_continued:
        messages.append({
            "role": "system",
            "content": f"{image_prompt} Continue the ongoing story about {name}. Refer to previous events and characters when appropriate. The story segment should be engaging and descriptive, but brief (about 1 minute when read aloud). It is crucial that you end this segment with a clear decision point for the user, presenting exactly three distinct options. Format the options as follows:\n\nWhat will {name} do next?\n1. [First option]\n2. [Second option]\n3. [Third option]"
        })
    else:
        messages.append({
            "role": "system",
            "content": f"{image_prompt} Begin a new story about {name}. The opening segment should introduce the character and setting, and set up an initial situation or challenge. The story segment should be engaging but brief, no longer than 6 sentences at the most. It is crucial that you end this segment with a clear decision point for the user, presenting exactly three distinct options. Format the options as follows:\n\nWhat will {name} do next?\n1. [First option]\n2. [Second option]\n3. [Third option]"
        })

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=max_tokens,
    )

    content = response.choices[0].message.content

    # Add a clear segment separator so I can choose to show latest segment only, instead of using "\n\n" as a strip cut which doesnt always work
    content = f"<segment>{content.strip()}</segment>"

    choices = extract_choices(content) if not is_final else []

    # If choices are not generated and it's not the final segment, add a note in the debug log
    if not is_final and not choices:
        print("** DEBUG: No choices generated in this segment. This may need manual review.")

    return content, response.usage.total_tokens, unused_images[2:], unused_images[:2], choices # After generating content, returns the used image descriptions


def extract_choices(content: str) -> List[str]:
    import re
    choices_pattern = r"\n\nWhat will .+ do next\?\n\n1\. (.+)\n2\. (.+)\n3\. (.+)"
    matches = re.search(choices_pattern, content, re.DOTALL)
    if matches:
        return list(matches.groups())
    return []


def generate_bedtime_story(user_id: str, image_descriptions: List[str], is_continued: bool = False, story_choice: str = None, **kwargs):
    print(
        f"Debug: generate_bedtime_story called with user_id={user_id}, is_continued={is_continued}, story_choice={story_choice}, kwargs={kwargs}")
    if is_continued:
        user_data = retrieve_and_continue_story(user_id, story_choice)
        if user_data is None:
            print("Debug: No existing story found, starting a new one")
            is_continued = False
            user_data = kwargs
        else:
            print(f"Debug: Retrieved existing story data: {user_data}")
            # Update the retrieved data with new inputs
            user_data.update(kwargs)
    else:
        user_data = kwargs

    # Ensure all required fields are present
    required_fields = ['name', 'place', 'tone', 'moral', 'length', 'age']
    for field in required_fields:
        if field not in user_data:
            print(f"Debug: Missing required field: {field}")
            raise ValueError(f"Missing required field: {field}")

    system_prompt = create_system_prompt(user_data)
    initial_prompt = create_initial_prompt(user_data, is_continued)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": initial_prompt}
    ]

    full_story = ""
    all_segments = []
    current_length = 0
    total_tokens = 0
    unused_images = image_descriptions.copy() # So image_descriptions, a list of image names to be used, gets put in as an argument whe generate_bedtime_story called. This then creates a copy of image_description
    max_tokens = max(800, int(user_data['length'] * 300))
    story_concluding = False

    while current_length < user_data['length']:
        print(f"Debug: Generating story part. Current length: {current_length}, Target length: {user_data['length']}")
        try:
            story_part, part_tokens, unused_images, segment_images, choices = generate_story_part(
                messages=messages,
                name=user_data['name'],
                unused_images=unused_images,
                max_tokens=300,
                is_final=story_concluding,
                is_continued=is_continued
            )
            print(f"Debug: Story part generated. Tokens: {part_tokens}")
        except Exception as e:
            print(f"Debug: Error in generate_story_part: {str(e)}")
            raise

        part_length = estimate_reading_time(story_part)
        current_length += part_length
        total_tokens += part_tokens

        print(f"Debug: Updated length: {current_length}, Total tokens: {total_tokens}")

        # Extract content between segment tags
        narrative = story_part.split("<segment>")[-1].split("</segment>")[0]

        # ...and extract content before choices
        narrative = story_part.split("\n\nWhat will")[0].strip()  # Separate narrative from choices

        full_story += narrative.strip() + "\n\n"

        #  Functions receives data from generate_story_part and updates the segment information
        all_segments.append({
            "text": narrative.strip(),
            "images": segment_images,
            "choices": choices
        })

        if current_length >= user_data['length'] * 0.8 and not story_concluding:
            print("Debug: Story is nearing conclusion")
            story_concluding = True

        print("Debug: Yielding current story state")
        user_choice = yield {
            "story": full_story,
            "segments": all_segments,
            "complete": False,
            "choices": choices
        }

        if story_concluding:
            break

        print(f"Debug: Received user choice: {user_choice}")

        if user_choice.lower() == 'exit story':
            print("Debug: User requested to exit story")
            break

        try:
            next_prompt = f"\n{user_data['name']} decides to {user_choice}. Continue the story based on this action, and end with a new set of choices or decision points."
            messages.append({"role": "assistant", "content": story_part})
            messages.append({"role": "user", "content": next_prompt})
            print("Debug: Added user choice to messages")
        except Exception as e:
            print(f"Debug: Error processing user choice: {str(e)}")
            raise

        is_continued = True  # Set to True after the first iteration

    print("Debug: Generating final segment")
    final_segment, final_tokens, _, final_images, _ = generate_story_part(
        messages=messages,
        name=user_data['name'],
        unused_images=unused_images,
        max_tokens=300,
        is_final=True,
        is_continued=True
    )

    full_story += final_segment.strip() + "\n\n"
    all_segments.append({
        "text": final_segment.strip(),
        "images": final_images,
        "choices": []
    })

    print("Debug: Story complete")
    yield {
        "story": full_story,
        "segments": all_segments,
        "complete": True,
        "choices": []
    } # Updated story state is yielded to Gradio Interface