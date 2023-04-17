# videoAutoGen
Automatic creation of image-slideshow video with voiceover from an input prompt by integrating GPT3.5, Stable Diffusion, Eleven Labs and FFMPEG

## Licenses
Open-source, strictly intended for research purposes only

## Getting started is simple
Download videoAutoGen.py, install dependencies (see below), create constants.py to hold OpenAI and ElevenLabs API keys, and run via command line

### Tech stack
- GPT3.5 via OpenAI (key required)
- Stable Diffusion via HuggingFace Diffusers
- ElevenLabs API (key required)
- FFMPEG-Python (wrapper for FFMPEG)
- Other Python libraries: torch, os, re, glob

### How it works
1. User enters input prompt into command line. Connects via OpenAI to GPT3.5 to generate a short video script
2. Given the video script, connect via OpenAI to GPT3.5 to generate image descriptions for each scene
3. Feed the image descriptions into Hugging Face’s Diffusers library, using Stable Diffusion v2.1 to generate matching images
4. Parse the script for the voiceover text, passing into Eleven Labs to create voiceovers in Obama’s voice
5. Use FFMPEG to match image to voiceover to make one video per scene, then join all the videos together into the final video
6. Output video (combined.mp4) as well as component script, image, audio and video files are generated

### Output format
    .
    ├── videoAutoGen.py            
    ├── constants.py            # User's personal file to store API keys (note: do not upload or share!)  
    ├── videoAutoGen            # Directory created to store output
      ├── audio                 # Directory with individual audio files (.wav), numbered from 0
      ├── images                # Directory with individual image files (.png), numbered from 0
      ├── script                # Directory with script.txt
      ├── video                 # Directory with individual video files (.mp4), numbered from 0
    ├── combined.mp4            # Final video output
