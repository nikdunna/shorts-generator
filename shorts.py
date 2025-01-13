# Import everything
from dotenv import load_dotenv
import random
import os
from openai import OpenAI
from elevenlabs import play, save
from elevenlabs.client import ElevenLabs
import os
import base64
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
os.environ["IMAGEIO_FFMPEG_EXE"] = "/opt/homebrew/bin/ffmpeg"
from moviepy.editor import *
import moviepy.video.fx.crop as crop_vid
load_dotenv()

def save_audio_from_base64(audio_base64, output_path):
    audio_data = base64.b64decode(audio_base64)
    with open(output_path, "wb") as audio_file:
        audio_file.write(audio_data)

def bounce_effect(t):
    # Base vertical position for the text (centered vertically)
    y_base = final_clip.size[1] // 2  # Vertical center
    bounce_height = 30  # Pixels to bounce

    # Calculate the vertical offset for bouncing
    y = y_base - bounce_height * abs((t % 0.5) - 0.25) * 4  # Simple bounce effect formula
    return y

# Ask for video info
title = input("\nEnter the name of the video >  ")
option = input('Do you want AI to generate content? (yes/no) >  ')

if option == 'yes':
    # Generate content using OpenAI API
    theme = input("\nEnter the theme of the video >  ")

    client = OpenAI(
     api_key=os.environ.get("OPENAI_API_KEY"),
    )

    openai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": "You are an incredibly good educational and entertainment writer and your job is to create scripts for youtube shorts and tiktoks. These shorts or tiktoks will often times contain themes like lists of cool facts, fun quizzes about science facts, or similar fun themes. You will output scripts for these videos THAT ARE AT MOST 45 SECONDS LONG. THIS IS IMPORTANT. ALL SCRIPTS MUST HAVE CONTENT FOR ONLY 30-40 SECONDS OF SPEECH The theme will be provided to you by the user. There will be no intro or outro. Get straight to the point, but in an entertaining and quick manner. The script should only contain plaintext of what is to be said by the narrator ONLY. No other decoration, stage calls, or other info needs to be included."},
            {
                "role": "user",
                "content": theme
            }
    ]
)
    print(openai_response.choices[0].message.content)

    yes_no = input('\nIs this fine? (yes/no) >  ')
    if yes_no == 'yes':
        content = openai_response.choices[0].message.content
    else:
        content = input('\nEnter >  ')
else:
    content = input('\nEnter the content of the video >  ')

# Create the directory
if os.path.exists('generated') == False:
    os.mkdir('generated')

# Type check for string of response
if not isinstance(openai_response.choices[0].message.content, str):
        raise ValueError("The response content is not a string.")

# AUDIO GEN
client = ElevenLabs(
  api_key=os.environ.get("ELEVEN_API_KEY"),
)

# audio = client.generate(
#   text=content,
#   voice="Brian",
#   model="eleven_multilingual_v2"
# )

audio = client.text_to_speech.convert_with_timestamps(
    text=content,
    voice_id="nPczCjzI2devNBz1zQrb",
    output_format="mp3_44100_128",
    model_id="eleven_multilingual_v2"
)

audio_base64 = audio["audio_base64"]
timestamps = audio["alignment"]
audio_path = "generated/speech.mp3"
if not os.path.exists("generated"):
    os.mkdir("generated")
save_audio_from_base64(audio_base64, audio_path)


print('\n')


### VIDEO EDITING ###
gp = random.choice(["1", "2"])
audio_clip = AudioFileClip("generated/speech.mp3")
audio_length = audio_clip.duration

# Trim a random part of minecraft gameplay and slap audio on it
video = VideoFileClip("gameplay/gameplay_" + gp + ".mp4")

if audio_clip.duration > video.duration:
    raise ValueError("The audio duration exceeds the video duration. Use a longer video or a shorter audio clip.")

# Randomly select a valid starting point in the video
max_start_point = int(video.duration - audio_clip.duration)
start_point = random.randint(0, max_start_point)

# Extract a subclip from the video that matches the audio duration
subclip = video.subclip(start_point, start_point + audio_clip.duration + 3)

# Attach the audio to the video subclip
# composite_audio = CompositeAudioClip([audio_clip])
final_clip = subclip.set_audio(audio_clip)

# Resize the video to 9:16 ratio
w, h = final_clip.size
target_ratio = 1080 / 1920
current_ratio = w / h

if current_ratio > target_ratio:
    # The video is wider than the desired aspect ratio, crop the width
    new_width = int(h * target_ratio)
    x_center = w / 2
    y_center = h / 2
    final_clip = crop_vid.crop(final_clip, width=new_width, height=h, x_center=x_center, y_center=y_center)
else:
    # The video is taller than the desired aspect ratio, crop the height
    new_height = int(w / target_ratio)
    x_center = w / 2
    y_center = h / 2
    final_clip = crop_vid.crop(final_clip, width=w, height=new_height, x_center=x_center, y_center=y_center)

# Add captions using alignment data
text_clips = []
characters = timestamps["characters"]
char_start_times = timestamps["character_start_times_seconds"]
char_end_times = timestamps["character_end_times_seconds"]

# Create words and their timing
current_word = ""
start_time = char_start_times[0]
for i, char in enumerate(characters):
    if char == " " or i == len(characters) - 1:  # End of a word
        if char != " ":
            current_word += char
        end_time = char_end_times[i]
        if current_word.strip():  # Add non-empty words as captions
            text_clip = TextClip(
                current_word,
                fontsize=60,
                color="white",
                stroke_color="black",  # Outline color
                stroke_width=5,  # Outline thickness
                font="Arial-Bold",
                size=(final_clip.w, None),
                method="caption"
            ).set_position("center", "center").set_start(start_time).set_duration(end_time - start_time)
            text_clips.append(text_clip)
        current_word = ""
        if i < len(characters) - 1:
            start_time = char_start_times[i + 1]
    else:
        current_word += char

# Combine video with text clips (overlay captions)
composite_clip = CompositeVideoClip([final_clip] + text_clips)

# Write the final video
composite_clip.write_videofile("generated/" + title + ".mp4", codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)
