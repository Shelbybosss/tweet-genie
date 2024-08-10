import streamlit as st
import json
import os
from requests_oauthlib import OAuth1Session
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys and other settings from environment variables
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
GENIE_API_KEY = os.getenv('GENIE_API_KEY')

# Initialize Gemini API
genai.configure(api_key=GENIE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Functions
def generate_tweet(content):
    response = model.generate_content(f"Generate a maximum tweet length tweet on this topic use your information too {content}")
    return response.text.strip()

def post_tweet(tweet):
    payload = {"text": tweet}

    # Get request token
    request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        return "There may have been an issue with the consumer_key or consumer_secret you entered."

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")

    # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print(f"Please go here and authorize: {authorization_url}")
    verifier = input("Paste the PIN here: ")

    # Get the access token
    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    # Make the request
    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    # Making the request
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code != 201:
        return f"Request returned an error: {response.status_code} {response.text}"

    json_response = response.json()
    return json.dumps(json_response, indent=4, sort_keys=True)

# Streamlit UI
st.title('Automated Tweet Generator and Poster')

st.write('This app allows you to input a title and content, generate a tweet using Gemini LLM, and post it to Twitter automatically.')

# Input fields for generating and posting tweets
title = st.text_input('Title')
content = st.text_area('Content')

if st.button('Generate Tweet'):
    if title and content:
        full_content = f"{title} - {content}"
        tweet = generate_tweet(full_content)
        st.write(f"Generated Tweet: {tweet}")
        st.session_state.generated_tweet = tweet
    else:
        st.write("Please provide both title and content.")

if st.button('Post Tweet'):
    if 'generated_tweet' in st.session_state:
        tweet = st.session_state.generated_tweet
        post_status = post_tweet(tweet)
        st.write(f"Post Status: {post_status}")
    else:
        st.write("No tweet generated yet. Please generate a tweet first.")
