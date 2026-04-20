import streamlit as st
import requests
import os
import json
import base64
import hashlib
import secrets
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv

# Load credentials from current or parent directory
load_dotenv()
if not os.getenv("X_CLIENT_ID"):
    load_dotenv("../.env")

CLIENT_ID = os.getenv("X_CLIENT_ID")
CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")
REDIRECT_URI = os.getenv("X_REDIRECT_URI", "http://127.0.0.1:8501")

# X API Endpoints
AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

# Diagnostic: Use minimal scopes to test if Client ID/Secret work at all
MINIMAL_SCOPES = ["tweet.read", "users.read"]
FULL_SCOPES = ["tweet.read", "users.read", "bookmark.read", "like.read", "offline.access"]

st.set_page_config(page_title="X Bookmarks Fetcher", page_icon="🔖", layout="wide")

st.title("🔖 X Bookmarks Fetcher")

# Scope Toggle for debugging
use_minimal = st.checkbox("Diagnostic Mode: Test connection with minimal scopes (no bookmarks)", value=False)
current_scopes = MINIMAL_SCOPES if use_minimal else FULL_SCOPES

if use_minimal:
    st.info("Using minimal scopes to see if your API tier allows basic login.")
else:
    st.warning("Requesting Bookmarks/Likes. Note: Requires a Paid X API Tier (Basic/Pro/Consumption).")

max_pages = st.slider("Max pages to fetch (100 results per page)", 1, 50, 1)
st.caption(f"Estimated cost: ~${max_pages * 0.01:.2f} USD")

if not CLIENT_ID or not CLIENT_SECRET:
    st.error("Please provide `X_CLIENT_ID` and `X_CLIENT_SECRET` in the `.env` file.")
    st.stop()

# Helper for PKCE
def create_verifier_and_challenge():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).decode("utf-8").replace("=", "")
    return code_verifier, code_challenge

# Initialize session state keys if they don't exist
for key in ["code_verifier", "oauth_state", "access_token"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Step 1: Login / Auth
if not st.session_state.access_token:
    # Check for incoming redirect from X
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        # Try to get verifier from session state, OR from the 'state' parameter as fallback
        state_param = query_params.get("state")
        verifier = st.session_state.code_verifier or state_param
        
        if not verifier:
            st.error("⚠️ **Verification Failed**: Could not find the code verifier.")
            if st.button("🔄 Restart Login"):
                st.query_params.clear()
                st.rerun()
            st.stop()

        # Build the request for the token
        auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")).decode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth}"
        }
        
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": verifier
        }
        
        with st.spinner("Exchanging code for access token..."):
            response = requests.post(TOKEN_URL, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.access_token = token_data["access_token"]
            st.query_params.clear() 
            st.success("✅ Successfully authenticated!")
            st.rerun()
        else:
            st.error("❌ **Token Exchange Failed**")
            st.json(response.json())
            if st.button("🔄 Try Again"):
                st.query_params.clear()
                st.rerun()
            st.stop()
    
    st.markdown("### Step 1: Authenticate")
    if st.button("🔐 Login with X"):
        code_verifier, code_challenge = create_verifier_and_challenge()
        st.session_state.code_verifier = code_verifier
        
        twitter = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=current_scopes)
        # Pass the code_verifier AS the state so X returns it to us
        authorization_url, state = twitter.authorization_url(
            AUTH_URL, 
            code_challenge=code_challenge, 
            code_challenge_method="S256",
            state=code_verifier
        )
        
        st.info("Log in using the link below:")
        st.markdown(f'<a href="{authorization_url}" target="_self" style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #1DA1F2; border-radius: 5px; text-decoration: none; font-weight: bold;">🔗 Authorize on X</a>', unsafe_allow_html=True)

# Step 2: Dashboard
else:
    st.success("Connected to X")
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    # Automatically get User ID to show the dashboard
    me_resp = requests.get("https://api.x.com/2/users/me", headers=headers)
    if me_resp.status_code == 200:
        user_id = me_resp.json()["data"]["id"]
        username = me_resp.json()["data"]["username"]
        st.info(f"Welcome, @{username} (ID: {user_id})")
        
        # Now fetch bookmarks & likes
        bookmarks_url = f"https://api.x.com/2/users/{user_id}/bookmarks"
        # Optional expansions
        fetch_params = {
            "expansions": "author_id",
            "tweet.fields": "created_at,text,public_metrics,entities",
            "user.fields": "name,username"
        }
        
        # Helper for paginated fetching
        def fetch_paginated(url, headers, params, max_p, name):
            all_data = []
            next_token = None
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(max_p):
                status_text.text(f"Fetching page {i+1} of {name}...")
                current_params = params.copy()
                if next_token:
                    current_params["pagination_token"] = next_token
                
                resp = requests.get(url, headers=headers, params=current_params)
                if resp.status_code != 200:
                    st.error(f"Failed on page {i+1}: {resp.text}")
                    return all_data, resp
                
                data = resp.json()
                tweets = data.get("data", [])
                all_data.extend(tweets)
                
                next_token = data.get("meta", {}).get("next_token")
                progress_bar.progress((i + 1) / max_p)
                
                if not next_token:
                    st.info(f"End of {name} reached after {i+1} pages.")
                    break
                    
            status_text.empty()
            progress_bar.empty()
            return all_data, None

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Fetch Bookmarks"):
                data_list, err_resp = fetch_paginated(bookmarks_url, headers, fetch_params, max_pages, "Bookmarks")
                
                if data_list:
                    st.write(f"✅ Found {len(data_list)} bookmarks.")
                    with open("bookmarks.json", "w") as f:
                        json.dump(data_list, f, indent=4)
                    st.success("Saved to `bookmarks.json`!")
                    st.download_button("Download JSON", json.dumps(data_list, indent=4), "bookmarks.json")
                
                if err_resp:
                    st.error(f"Stopped early due to error {err_resp.status_code}: {err_resp.text}")

        with col2:
            if st.button("❤️ Fetch Likes"):
                likes_url = f"https://api.x.com/2/users/{user_id}/liked_tweets"
                data_list, err_resp = fetch_paginated(likes_url, headers, fetch_params, max_pages, "Likes")
                
                if data_list:
                    st.write(f"✅ Found {len(data_list)} liked tweets.")
                    with open("likes.json", "w") as f:
                        json.dump(data_list, f, indent=4)
                    st.success("Saved to `likes.json`!")
                    st.download_button("Download JSON", json.dumps(data_list, indent=4), "likes.json")
                
                if err_resp:
                    st.error(f"Stopped early due to error {err_resp.status_code}: {err_resp.text}")
    else:
        st.error(f"Failed to get user info: {me_resp.text}")

    if st.button("🗑️ Logout"):
        st.session_state.access_token = None
        st.rerun()
