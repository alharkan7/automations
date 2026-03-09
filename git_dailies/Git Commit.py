import os
import subprocess
import datetime
import time

# Get the current datetime
now = datetime.datetime.now()

file_path = r"/Users/alharkan/Documents/Repositories/Archive/notes"
# Set the path to your local repository
repo_path = "/Users/alharkan/Documents/Repositories/Archive/notes"
datetime_filename = "Datetime.txt"
datetime_filepath = os.path.join(file_path, datetime_filename)

# Change directory to the repository path
os.chdir(repo_path)

# Sync with remote repository first
print("Pulling changes from remote...")
pull_result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
print(pull_result.stdout)
print(pull_result.stderr)

# Check for conflicts in Datetime.txt
status_output = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8')
conflict_marker = f"UU {datetime_filename}"

if conflict_marker in status_output:
    print(f"Conflict detected in {datetime_filename}. Resolving using remote version.")
    # Resolve conflict by taking the remote version
    subprocess.call(['git', 'checkout', '--theirs', datetime_filepath])
    # Stage the resolved file
    subprocess.call(['git', 'add', datetime_filepath])
else:
    print("No conflict detected in Datetime.txt or pull successful.")

# Open the file in append mode
print(f"Appending datetime to {datetime_filename}...")
with open(datetime_filepath, 'a') as f:
    # Write the current datetime to the file
    f.write(str(now) + '\n')

time.sleep(10) # Optional: keep or remove depending on need

# Set the commit message
commit_message = 'Daily commit - ' + now.strftime('%Y-%m-%d %H:%M:%S')

# Add and commit all changes (includes the resolved/updated Datetime.txt)
print("Adding changes...")
subprocess.call(['git', 'add', '.'])

print("Committing changes...")
# Use run instead of call to check commit status if needed
commit_result = subprocess.run(['git', 'commit', '-m', commit_message], capture_output=True, text=True)
print(commit_result.stdout)
print(commit_result.stderr)

# Check if commit was successful (e.g., not "nothing to commit")
if "nothing to commit" not in commit_result.stdout and commit_result.returncode == 0:
    # Push the changes to the remote repository
    print("Pushing changes...")
    push_result = subprocess.run(['git', 'push'], capture_output=True, text=True)
    print(push_result.stdout)
    print(push_result.stderr)
    if push_result.returncode != 0:
        print("Error during push.")
elif "nothing to commit" in commit_result.stdout:
     print("No changes to commit.")
else:
    print("Error during commit.")

print("Script finished.")

# Removed the old status check logic as commit handles the "no changes" case
# if status: ... else: print('No changes to commit.')