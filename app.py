from flask import Flask, render_template, redirect, send_from_directory
import requests
from bs4 import BeautifulSoup
import openai
from flask_apscheduler import APScheduler
import time
import datetime
import random
import os


class Config:
    SCHEDULER_API_ENABLED = True


app = Flask(__name__)
app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

latest_headline = {"text": "", "time": None}
API_KEY = os.environ.get("API_SYNCLABS")  # Placeholder for your API key
# List to store video URLs
videos = ["https://synchlabs-public.s3.amazonaws.com/Data/job_90e70bb6-1b8e-44c7-bcef-d956a314d0b0/result_90e70bb6-1b8e-44c7-bcef-d956a314d0b0.mp4"]


def scheduled_task():
    global latest_headline
    new_headline = get_latest_headline()
    # if new_headline:
    #     audio_response = generate_news_audio(new_headline)
    #     print(f"Generated audio for headline: {new_headline}")
    #     audio_response.write_to_file('static\output.mp3')
    #     audio_url = "https://anker-xi.vercel.app/video/output.mp3"
    #     video_url = "https://anker-xi.vercel.app/video/input.mp4"
    #     id = request_video_processing(audio_url, video_url)
    #     while True:
    #         status_response = requests.get(f'https://api.synclabs.so/video/{id}', headers={'x-api-key': API_KEY})
    #         status = status_response.json().get('status')
    #         if status == 'COMPLETED':
    #             download_url = status_response.json().get('url')
    #             manage_videos_list(download_url)
    #             break
    #         time.sleep(60)  # Check status every minute


def manage_videos_list(download_url):
    global videos
    if len(videos) >= 14:
        videos.pop(0)  # Remove the oldest URL
    videos.append(download_url)
    print(videos)  # Add the new URL


@app.route('/')
def index():
    return render_template('index.html')


def request_video_processing(audio_url, video_url):
    url = 'https://api.synclabs.so/video'
    headers = {
        'accept': 'application/json',
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        "audioUrl": audio_url,
        "videoUrl": video_url,
        "synergize": True,
        "maxCredits": 800,
        "webhookUrl": None,
        "model": "sync-1.5-beta"
    }
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    id = response_data.get('id')
    return id


def get_latest_headline():
    global latest_headline
    url = 'https://www.prnewswire.com/news-releases/news-releases-list/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    headlines = soup.find_all('h3')
    headline_text = headlines[0].text.strip()
    if headlines:
        headline_text = headlines[0].text.strip()
        if headline_text != latest_headline["text"]:
            latest_headline = {"text": headline_text, "time": datetime.datetime.now()}
            return headline_text
    return None

def generate_news_audio(headline):
    api_key = os.environ.get("OPENAI_API_KEY")
    client = openai.Client(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a AI News Anchor acting similar like a human in a way that cannot be easily detected by the way of speaking and generate the content only in english like a news anchor based upon the headlines received, if headlines are in other languages translate to english,generate it as 30 seconds content."},
            {"role": "user", "content": headline}
        ]
    )
    audio_content = completion.choices[0].message.content
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=audio_content
    )
    return response


@app.route('/video')
def video():
    global videos
    video_url = random.choice(videos)
    return redirect(video_url)


@app.route('/video/<path:filename>')
def serve_video(filename):
    return send_from_directory('static', filename)


@scheduler.task('interval', id='do_job_1', minutes=180, misfire_grace_time=900)
def job1():
    headline = get_latest_headline()
    if headline:
        # Proceed with generating and processing content for the new headline
        scheduled_task()
    else:
        # No new headline found, no action needed
        print("No new headline or duplicate headline found, skipping this cycle.")


if __name__ == '__main__':
    app.run(debug=False)
