import os
from dotenv import load_dotenv
from typing import Dict, Optional, List, Tuple

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Pinecone client
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

# Check if the index exists, and if not, create it
index_name = 'bedtime-stories'
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric='euclidean',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'  # free tier region
        )
    )

# renaming it to just 'index'
index = pc.Index(index_name)

def retrieve_existing_story_titles(user_id: str) -> List[Tuple[str, Dict]]:
    results = index.query(
        vector=[0] * 1536,  # Mock vector just for filtering by metadata
        filter={"user_id": user_id},
        top_k=10,
        include_metadata=True
    )

    if results and results["matches"]:
        stories = []
        for match in results["matches"]:
            metadata = match["metadata"]
            story_name = metadata.get("story_name", "Untitled Story")
            stories.append((story_name, metadata))
        return stories
    else:
        return []

def retrieve_and_continue_story(user_id: str, story_choice: str) -> Optional[Dict[str, any]]:
    stories = retrieve_existing_story_titles(user_id)
    selected_story = next((story for story in stories if story[0] == story_choice), None)

    if selected_story:
        _, metadata = selected_story
        return {
            "name": metadata.get('name'),
            "place": metadata.get('place'),
            "tone": metadata.get('tone'),
            "moral": metadata.get('moral'),
            "length": metadata.get('length'),
            "age": metadata.get('age'),
            "summary": metadata.get('summary'),
            "image_descriptions": metadata.get('image_descriptions', []),
            "is_continued": True
        }
    else:
        print(f"No story found with title: {story_choice}")
        return None

def summarize_story(full_story: str, max_tokens: int = 150) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes bedtime stories."},
                {"role": "user", "content": f"Please summarize the following bedtime story in about {max_tokens} tokens:\n\n{full_story}"}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in summarizing story: {e}")
        return ""

def summarize_and_upsert_story(user_id: str, name: str, full_story: str, place: str, story_name: str = None, image_descriptions: List[str] = None):
    summary = summarize_story(full_story)

    embedding_response = client.embeddings.create(
        input=summary,
        model="text-embedding-ada-002"
    )
    embedding = embedding_response.data[0].embedding

    metadata = {
        "user_id": user_id,
        "name": name,
        "story_name": f"Story about {name}",
        "place": place,
        "summary": summary,
        "image_descriptions": image_descriptions or []
    }

    index.upsert(vectors=[{
        "id": story_name or name,
        "values": embedding,
        "metadata": metadata
    }])

    print(f"Story summarized and saved to database.")