export default {
	async scheduled(event, env, ctx) {
	  ctx.waitUntil(doGitUpdate(env));
	},
  };
  
  async function doGitUpdate(env) {
	const owner = env.GITHUB_REPO_OWNER;
	const repo = env.GITHUB_REPO_NAME;
	const path = env.TARGET_FILE_PATH;
	const token = env.GITHUB_TOKEN; // Access the secret
  
	const githubApiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;
	const headers = {
	  'Authorization': `token ${token}`,
	  'Accept': 'application/vnd.github.v3+json',
	  'User-Agent': 'Cloudflare-Worker-Git-Commit', // Good practice to identify your client
	  'Content-Type': 'application/json',
	};
  
	// Create a simpler headers object for the GET request
	const getHeaders = {
	  'Authorization': headers.Authorization,
	  'Accept': headers.Accept,
	  'User-Agent': headers.UserAgent,
	};
  
	let currentContent = '';
	let currentSha = null;
  
	try {
	  // Log the URL being fetched
	  console.log(`Attempting to fetch: ${githubApiUrl}`);

	  // Construct headers for logging (MASK THE TOKEN!)
	  const logHeaders = {
		  ...headers, // Copy original headers
		  'Authorization': headers.Authorization ? 'token [REDACTED]' : 'Token header missing', // Redact token
	  };
	  console.log('Request Headers (Token Redacted):', JSON.stringify(logHeaders));

	  // 1. Get current file content and SHA
	  // Use the simpler getHeaders for the GET request
	  const getResponse = await fetch(githubApiUrl, { headers: getHeaders });
  
	  if (getResponse.ok) {
		const data = await getResponse.json();
		currentContent = atob(data.content); // Decode base64 content
		currentSha = data.sha;
	  } else if (getResponse.status !== 404) {
		// Handle errors other than "file not found"
		console.error(`Error fetching file: ${getResponse.status} ${getResponse.statusText}`);
		const errorBody = await getResponse.text();
		console.error("Error body:", errorBody);
		return; // Stop execution on error
	  }
	  // If 404, currentContent remains "" and currentSha remains null, we'll create the file
  
	  // 2. Prepare new content
	  const now = new Date();
	  const timestamp = now.toISOString(); // Use ISO format for clarity
	  const newContent = currentContent + timestamp + '\n';
	  const newContentBase64 = btoa(newContent); // Encode content to base64
  
	  // 3. Create or update the file
	  const commitMessage = `Daily timestamp log - ${now.toISOString()}`;
	  const body = JSON.stringify({
		message: commitMessage,
		content: newContentBase64,
		sha: currentSha, // Include SHA if updating an existing file
	  });
  
	  const putResponse = await fetch(githubApiUrl, {
		method: 'PUT',
		headers: headers,
		body: body,
	  });
  
	  if (putResponse.ok) {
		console.log(`Successfully updated ${path} at ${timestamp}`);
	  } else {
		console.error(`Error updating file: ${putResponse.status} ${putResponse.statusText}`);
		const errorBody = await putResponse.text();
		console.error("Error body:", errorBody);
	  }
	} catch (error) {
	  console.error("Error during GitHub update process:", error);
	}
  }