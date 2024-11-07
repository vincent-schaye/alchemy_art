import os
import random
import numpy as np
import PIL.Image as Image
from PIL import ImageOps
import torch
import torchvision.transforms.functional as TF
import spaces
from diffusers import (
    AutoencoderKL,
    EulerAncestralDiscreteScheduler,
    StableDiffusionXLAdapterPipeline,
    T2IAdapter,
)

style_list = [
    {
        "name": "(No style)",
        "prompt": "{prompt}",
        "negative_prompt": "",
    },
    {
        "name": "3D Model",
        "prompt": "3d style {prompt} . professional 3d model, smooth surfaces, cartoon character, highly detailed, vibrant colors, futuristic robot, dramatic lighting, studio anime, cute, whimsical, octane render, dramatic lighting, playful design, anime artwork, volumetric, key visual",
        "negative_prompt": "ugly, deformed, disfigured, noisy, low poly, blurry, painting, photo, black and white, realism, low contrast, harsh shadows, photorealistic",
    },
    {
        "name": "Anime",
        "prompt": "anime artwork {prompt} . anime style, key visual, vibrant, studio anime,  highly detailed",
        "negative_prompt": "photo, deformed, black and white, realism, disfigured, low contrast",
    },
    {
        "name": "Digital Art",
        "prompt": "concept art {prompt} . digital artwork, illustrative, painterly, matte painting, highly detailed",
        "negative_prompt": "photo, photorealistic, realism, ugly",
    },
    {
        "name": "Photographic",
        "prompt": "cinematic photo {prompt} . 35mm photograph, film, bokeh, professional, 4k, highly detailed",
        "negative_prompt": "drawing, painting, crayon, sketch, graphite, impressionist, noisy, blurry, soft, deformed, ugly",
    },
    {
        "name": "Pixel art",
        "prompt": "pixel-art {prompt} . low-res, blocky, pixel art style, 8-bit graphics",
        "negative_prompt": "sloppy, messy, blurry, noisy, highly detailed, ultra textured, photo, realistic",
    },
    {
        "name": "Fantasy art",
        "prompt": "ethereal fantasy concept art of {prompt} . magnificent, celestial, ethereal, painterly, epic, majestic, magical, fantasy art, cover art, dreamy",
        "negative_prompt": "photographic, realistic, realism, 35mm film, dslr, cropped, frame, text, deformed, glitch, noise, noisy, off-center, deformed, cross-eyed, closed eyes, bad anatomy, ugly, disfigured, sloppy, duplicate, mutated, black and white",
    },
    {
        "name": "Neonpunk",
        "prompt": "neonpunk style {prompt} . cyberpunk, vaporwave, neon, vibes, vibrant, stunningly beautiful, crisp, detailed, sleek, ultramodern, magenta highlights, dark purple shadows, high contrast, cinematic, ultra detailed, intricate, professional",
        "negative_prompt": "painting, drawing, illustration, glitch, deformed, mutated, cross-eyed, ugly, disfigured",
    },
    {
        "name": "Manga",
        "prompt": "manga style {prompt} . vibrant, high-energy, detailed, iconic, Japanese comic style",
        "negative_prompt": "ugly, deformed, noisy, blurry, low contrast, realism, photorealistic, Western comic style",
    },
]

styles = {k["name"]: (k["prompt"], k["negative_prompt"]) for k in style_list}
STYLE_NAMES = list(styles.keys())
DEFAULT_STYLE_NAME = "(No style)"

MAX_SEED = np.iinfo(np.int32).max

def apply_style(style_name: str, positive: str, negative: str = "") -> tuple[str, str]:
    p, n = styles.get(style_name, styles[DEFAULT_STYLE_NAME])
    return p.replace("{prompt}", positive), n + " " + negative

def randomize_seed_fn(seed: int, randomize_seed: bool) -> int:
    if randomize_seed:
        seed = random.randint(0, MAX_SEED)
    return seed

def pad_image_to_multiple(image: Image.Image, multiple: int = 32) -> Image.Image:
    """Pads the image symmetrically so its dimensions are divisible by the given multiple."""
    width, height = image.size
    new_width = ((width + multiple - 1) // multiple) * multiple
    new_height = ((height + multiple - 1) // multiple) * multiple

    pad_width = new_width - width
    pad_height = new_height - height

    padding = (pad_width // 2, pad_height // 2, pad_width - pad_width // 2, pad_height - pad_height // 2)
    padded_image = TF.pad(image, padding)

    return padded_image

# Initialize the model and pipeline
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
pipe = None  # Initialize pipe as None to avoid the error

if torch.cuda.is_available():
    model_id = "stabilityai/stable-diffusion-xl-base-1.0"
    adapter = T2IAdapter.from_pretrained("TencentARC/t2i-adapter-sketch-sdxl-1.0", torch_dtype=torch.float16, variant="fp16")
    scheduler = EulerAncestralDiscreteScheduler.from_pretrained(model_id, subfolder="scheduler")
    pipe = StableDiffusionXLAdapterPipeline.from_pretrained(
        model_id,
        vae=AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16),
        adapter=adapter,
        scheduler=scheduler,
        torch_dtype=torch.float16,
        variant="fp16",
    )
    pipe.to(device)

@spaces.GPU
def generate_images(
    uploaded_images,
    prompts_text: str,
    negative_prompt: str,
    style_name: str = DEFAULT_STYLE_NAME,
    num_steps: int = 25,
    guidance_scale: float = 5,
    adapter_conditioning_scale: float = 0.8,
    adapter_conditioning_factor: float = 0.8,
    seed: int = 0
):
    if pipe is None:
        raise RuntimeError("Stable Diffusion pipeline is not initialized. Please run on a system with CUDA support.")

    # Split prompts by lines and strip whitespace
    prompts = [line.strip() for line in prompts_text.strip().split('\n') if line.strip()]
    
    if len(uploaded_images) != len(prompts):
        raise ValueError("Number of uploaded images and prompts must match!")

    prompt_image_dict = {}  # Dictionary to hold {original_prompt: generated_image}
    generated_images = []

    # Debugging: Print the number of uploaded images and prompts
    print(f"Number of uploaded images: {len(uploaded_images)}")
    print(f"Number of prompts: {len(prompts)}")
    print(f"Prompts: {prompts}")
        
    generator = torch.Generator(device=device).manual_seed(seed)

    original_negative_prompt = negative_prompt
    print(f"Negative prompts: {original_negative_prompt}")

    for uploaded_image, prompt in zip(uploaded_images, prompts):
        print(f"Processing prompt: {prompt}")  # Debugging to ensure prompt is a string

        negative_prompt = original_negative_prompt
        # Store the original prompt before applying the style
        original_prompt = prompt

        # Apply style
        prompt, negative_prompt = apply_style(style_name, prompt, negative_prompt)

        image = Image.open(uploaded_image.name).convert("L")
        image = ImageOps.invert(image)
        image = image.convert("RGB")

        expected_width = 1024
        expected_height = 1024
        image = image.resize((expected_width, expected_height), Image.BICUBIC)

        image_tensor = TF.to_tensor(image) > 0.5
        image = TF.to_pil_image(image_tensor.to(torch.float32))

        with torch.no_grad():
            generated_image = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=image,
                num_inference_steps=num_steps,
                generator=generator,
                guidance_scale=guidance_scale,
                adapter_conditioning_scale=adapter_conditioning_scale,
                adapter_conditioning_factor=adapter_conditioning_factor
            ).images[0]

        # Debugging: Check shape of generated image
        print(f"Generated Image Size: {generated_image.size}")
        generated_images.append(generated_image)
        # Add original prompt and generated image to dictionary
        prompt_image_dict[original_prompt] = generated_image

    # Print the dictionary for testing purposes
    print(f"Prompt-Image Dictionary: {prompt_image_dict}")

    return generated_images