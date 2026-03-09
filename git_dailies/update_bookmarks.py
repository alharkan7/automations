import os
import subprocess
import datetime

# --- Configuration ---
script_to_run = r"/Users/alharkan/Documents/Repositories/alharkan7.github.io/public/os-bookmarks/get_chrome_bookmarks.py"
liked_videos_script = r"/Users/alharkan/Documents/Repositories/alharkan7.github.io/public/os-bookmarks/get_liked_videos.py"
repo_path = r"/Users/alharkan/Documents/Repositories/alharkan7.github.io"
# --- End Configuration ---

# Get the current date for the commit message
current_date = datetime.datetime.now().strftime('%Y-%m-%d')
commit_message = f"Update Bookmarks and Liked Videos {current_date}"

# 1. Run the initial script (Bookmarks)
print(f"Running script: {script_to_run}")
try:
    # Use run instead of call to capture output and check return code
    result_bookmarks = subprocess.run(
        ['python3', script_to_run],
        check=True,  # Raise an exception if the script fails
        capture_output=True,
        text=True,
        cwd=os.path.dirname(script_to_run) # Run script from its own directory
    )
    print("Bookmark script executed successfully.")
    print("Script output:")
    print(result_bookmarks.stdout)
    if result_bookmarks.stderr:
        print("Script errors/warnings:")
        print(result_bookmarks.stderr)

except subprocess.CalledProcessError as e:
    print(f"Error running script: {script_to_run}")
    print(f"Return code: {e.returncode}")
    print(f"Output: {e.stdout}")
    print(f"Error: {e.stderr}")
    exit(1) # Exit if the script failed
except FileNotFoundError:
    print(f"Error: The script '{script_to_run}' was not found.")
    exit(1)

# 2. Run the second script (Liked Videos)
# print(f"Running script: {liked_videos_script}")
# try:
#     result_liked_videos = subprocess.run(
#         ['python3', liked_videos_script],
#         check=True,  # Raise an exception if the script fails
#         capture_output=True,
#         text=True,
#         cwd=os.path.dirname(liked_videos_script) # Run script from its own directory
#     )
#     print("Liked videos script executed successfully.")
#     print("Script output:")
#     print(result_liked_videos.stdout)
#     if result_liked_videos.stderr:
#         print("Script errors/warnings:")
#         print(result_liked_videos.stderr)
# 
# except subprocess.CalledProcessError as e:
#     print(f"Error running script: {liked_videos_script}")
#     print(f"Return code: {e.returncode}")
#     print(f"Output: {e.stdout}")
#     print(f"Error: {e.stderr}")
#     exit(1) # Exit if the script failed
# except FileNotFoundError:
#     print(f"Error: The script '{liked_videos_script}' was not found.")
#     exit(1)

# 3. Change directory to the repository path
print(f"Changing directory to: {repo_path}")
try:
    os.chdir(repo_path)
except FileNotFoundError:
    print(f"Error: The repository path '{repo_path}' does not exist.")
    exit(1)
except Exception as e:
    print(f"Error changing directory: {e}")
    exit(1)

# 4. Check for changes and commit
print("Checking for changes in the repository...")
try:
    # Check git status
    status_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, check=True)
    status_output = status_result.stdout.strip()

    if status_output:
        print("Changes detected. Staging, committing, and pushing...")

        # Add all changes
        subprocess.run(['git', 'add', '.'], check=True)
        print("Changes staged.")

        # Commit the changes
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        print(f"Changes committed with message: '{commit_message}'")

        # Pull latest changes from remote
        print("Pulling latest changes from remote repository...")
        subprocess.run(['git', 'pull', '--no-edit'], check=True)
        print("Successfully pulled latest changes.")

        # Push the changes
        # Consider specifying the remote and branch if not default (e.g., ['git', 'push', 'origin', 'main'])
        subprocess.run(['git', 'push'], check=True)
        print("Changes pushed to the remote repository.")

    else:
        print("No changes to commit.")

except subprocess.CalledProcessError as e:
    print(f"Git command failed: {' '.join(e.cmd)}")
    print(f"Return code: {e.returncode}")
    print(f"Output: {e.stdout}")
    print(f"Error: {e.stderr}")
    exit(1)
except FileNotFoundError:
    print("Error: 'git' command not found. Make sure Git is installed and in your system's PATH.")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred during git operations: {e}")
    exit(1)

print("Process completed.")