#!/usr/bin/env python
"""
This script generates a image-slideshow video with a Obama-style voiceover from an input title prompt.
Component script, image, audio, and video files are saved in addition to the final video output.
At each step, users can terminate the program.
"""

# Imported libraries
import openai
from elevenlabslib import *
from elevenlabslib.helpers import *
import ffmpeg
import os
import re
import glob
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from constants import *

# Constants
openai.api_key = OPENAI_API_KEY
TEST_FLAG = False

def create_script(input=""):
    """Takes in a text prompt, and queries GPT3.5 to return a 20-second video script"""
    if not os.path.isdir('./videoAutoGen'):
        os.mkdir('./videoAutoGen')
    if TEST_FLAG:
        if not os.path.isfile("./videoAutoGen/script/script.txt"):
            print("Unable to find ./videoAutoGen/script/script.txt in test mode")
        else:
            file = open("./videoAutoGen/script/script.txt","r")
            return file.read()
    else:
        script_prompt = "Write a script for a simple 20-second video on the given topic. Number the scenes and preface all voiceovers with 'Voiceover:'. Topic: " + input
        try: 
            response = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo",
                temperature = 0,
                max_tokens = 800,
                messages = [
                    {"role": "system", "content": "You are a helpful script-writing assistant."},
                    {"role": "user", "content": script_prompt}
                ],
                request_timeout = 120
            )
            script = response["choices"][0]["message"]["content"].strip()

            # Save script
            if not os.path.isdir('./videoAutoGen/script'):
                os.mkdir('./videoAutoGen/script')
            with open("./videoAutoGen/script/script.txt","w") as f:
                f.write(script)

            return script
        
        except Exception as e:
            print(e)

def create_descriptions(script):
    """Takes in a script string, and queries GPT3.5 to return descriptions of an image that matches each scene, formatted as a Python list"""
    description_prompt = "For each scene in the script below, write a short phrase (7 words or less) describing an image that would go well with it. Put this in Python list form. \n\n"
    try: 
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            temperature = 0,
            max_tokens = 800,
            messages = [
                {"role": "system", "content": "You are a helpful image-describing assistant."},
                {"role": "user", "content": description_prompt + script}
            ],
            request_timeout = 120
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(e)

def stable_diffusion(image_description):
    """ Takes in a list of image descriptions in string form, queries cuda-hosted Stable Diffusion v2.1 for image responses, and downloads the images in .png."""
    model_id = "stabilityai/stable-diffusion-2-1"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("cuda")
    image_list = eval(image_description)
    if not os.path.isdir('./videoAutoGen/images'):
        os.mkdir('./videoAutoGen/images')
    for i in range(len(image_list)):
        prompt = image_list[i]
        prompt_digital = "Style: glow effects, octane render, cinema 4d, blender, atmospheric 4k ultra detailed, cinematic sensual, sharp focus, big depth of field, masterpiece, colors, modelshoot style"
        image = pipe(prompt+prompt_digital).images[0]
        image.save(f"./videoAutoGen/images/{i}.png")

def generate_audio(script):
    """ Takes in a script string, queries Eleven Labs to generate a voiceover for each line in Obama's voice, and downloads the audio files in .wav."""
    pattern = 'Voiceover: (.*)'
    script_list = []
    for match in re.findall(pattern, script):
        script_list.append(match)
    if not os.path.isdir('./videoAutoGen/audio'):
        os.mkdir('./videoAutoGen/audio')    
    try:
        user = ElevenLabsUser(ELEVEN_LABS_API_KEY)
        premadeVoice:ElevenLabsVoice = user.get_voices_by_name("Obama")[0]
        for i in range(len(script_list)):
            path = "./videoAutoGen/audio/" + str(i) + ".wav"
            mp3Data = premadeVoice.generate_audio_bytes(script_list[i],stability=0.3)
            save_bytes_to_path(path, mp3Data)
    except Exception as e:
        print(e)

def generate_scene(i):
    """ Takes in a numeric reference, finds the reference voiceover and image file, makes a video of the scene with FFMPEG, and saves it in .mp4."""
    if os.path.isfile(f'./videoAutoGen/images/{i}.png'):
        image = ffmpeg.input(f'./videoAutoGen/images/{i}.png')
    else:
        print(f"Unable to find ./videoAutoGen/images/{i}.png")
        return
    
    if os.path.isfile(f'./videoAutoGen/audio/{i}.wav'):
        audio = ffmpeg.input(f'./videoAutoGen/audio/{i}.wav')
    else:
        print(f"Unable to find ./videoAutoGen/audio/{i}.wav")
        return

    if not os.path.isdir('./videoAutoGen/video'):
        os.mkdir('./videoAutoGen/video')

    out = ffmpeg.output(audio, image, f'./videoAutoGen/video/{i}.mp4')
    out.run()

def generate_video():
    """ Creates individual scene videos, joins them with FFMPEG, and saves the final file as combined.mp4.
    Counts the number of audio (.wav) and image (.png) files available, and generates the lower number of scenes."""

    # Check for audio and image directories
    audio_dir = './videoAutoGen/audio'
    if not os.path.isdir(audio_dir):
        print(f"Unable to find ./videoAutoGen/audio")
        return
    
    image_dir = './videoAutoGen/images'
    if not os.path.isdir(image_dir):
        print(f"Unable to find ./videoAutoGen/images")
        return

    # Create individual scene videos
    wavCounter = len(glob.glob1(audio_dir,"*.wav"))
    pngCounter = len(glob.glob1(image_dir,"*.png"))
    num_videos = min(wavCounter, pngCounter)
    for i in range(0,num_videos):
        generate_scene(i)

    # Join all scene videos into a combined video
    video_dir = '../videoAutoGen/video'
    if not os.path.isdir('./videoAutoGen/video'):
        print(f"Unable to find ./videoAutoGen/video")
        return
    
    input_paths = []
    for i in range(0,num_videos):
        video_path = video_dir + f"/{i}.mp4"
        input_paths.append("'" + video_path + "'")
    open('./videoAutoGen/concat.txt', 'w').writelines([('file %s\n' % input_path) for input_path in input_paths])
    ffmpeg.input('./videoAutoGen/concat.txt', format='concat', safe=0).output('./videoAutoGen/combined.mp4', c='copy').run()
    
    # Clean up temporary files
    if os.path.isfile('./videoAutoGen/concat.txt'): 
        os.remove('./videoAutoGen/concat.txt')

if TEST_FLAG:
    script = create_script()
else:
    user_input = input("What is the title of your short video? ")
    script = create_script(user_input)
print(script)

check_user = input("Do you want to continue to generate descriptions? ")
descriptions = create_descriptions(script) 
print(descriptions)

check_user = input("Do you want to continue to download images? ")
stable_diffusion(descriptions)

check_user = input("Do you want to continue to generate audio? ")
generate_audio(script)

check_user = input("Do you want to continue to generate video? ")
generate_video()