# Interactive Bedtime Story Generator

This project is an interactive bedtime story generator that uses AI to create unique, customizable stories for children. It features a user-friendly interface built with Gradio, allowing users to input story parameters and make choices that influence the narrative.

Project was split between text-text (LLM) and RAG (Pinecone) development, visual Gen-AI (diffusion model) based art generation, and TTS generation

## Features

- Generate unique bedtime stories based on user input
- Interactive storytelling with user choices affecting the narrative
- Image integration for visual storytelling
- Save and continue stories
- Suitable for various age groups
- Doodle to Gen AI art
- TTS

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Steps

1. Clone the repository:

Models used are the [Base Stable Diffusion, SD XL](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0), [TencentARC's t2i-adapter-sketch](https://huggingface.co/TencentARC/t2i-adapter-sketch-sdxl-1.0), [Coqui's XTTS-v2](https://huggingface.co/coqui/XTTS-v2)

## Requirements:

- pyenv with Python: 3.11.3

### Setup

Use the requirements file in this repo to create a new environment.

```BASH
make setup

#or

pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_dev.txt
```

The `requirements.txt` file contains the libraries needed .


