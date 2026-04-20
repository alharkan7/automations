# X Bookmarks Fetcher

A simple Streamlit-based tool to fetch your personal bookmarks from X (Twitter) using the API v2.

## Setup

1.  **X Developer Portal**:
    *   Create a Project and App.
    *   Enable **User authentication settings**.
    *   Set App permissions to **Read**.
    *   Set Type of App to **Web App, Android, or iOS**.
    *   Set Callback URI to `http://127.0.0.1:8501`.
2.  **Environment Variables**:
    *   Copy `.env.example` to `.env`.
    *   Add your `X_CLIENT_ID` and `X_CLIENT_SECRET`.
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the App**:
    ```bash
    streamlit run app.py
    ```

## Usage

1.  Click **Login with X**.
2.  Authorize the app in your browser.
3.  Once redirected back, click **Fetch Bookmarks**.
4.  Your bookmarks will be saved to `bookmarks.json`.

## Requirements

*   X API **Basic** tier or higher (bookmarks are not available on the Free tier).
