// Reading List Sync - Popup Script
// Syncs Chrome Reading List to Supabase PostgreSQL

let readingListItems = [];

// Initialize on popup load
document.addEventListener('DOMContentLoaded', async () => {
  await loadStatus();
  await loadReadingList();
  setupEventListeners();
});

// Load sync status
async function loadStatus() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'get_status' });

    const statusEl = document.getElementById('sync-status');
    const labelEl = document.getElementById('sync-label');
    const detailsEl = document.getElementById('sync-details');

    // Check if Supabase is configured
    if (!response.configured) {
      statusEl.className = 'sync-status error';
      labelEl.textContent = 'Not Configured';
      detailsEl.textContent = 'Update SUPABASE_ANON_KEY in background.js';
      return;
    }

    const today = new Date().toISOString().split('T')[0];
    const isSyncedToday = response.lastSyncDate === today;

    if (isSyncedToday) {
      statusEl.className = 'sync-status synced';
      labelEl.textContent = 'Synced Today';
      const dbInfo = response.dbCount !== null ? ` • ${response.dbCount} in DB` : '';
      detailsEl.textContent = `Last sync: ${response.lastSyncDate} • ${response.itemCount} items${dbInfo}`;
    } else if (response.lastSyncDate === 'Never') {
      // Check if DB already has data (synced before, but storage was cleared)
      if (response.dbCount !== null && response.dbCount > 0) {
        statusEl.className = 'sync-status pending';
        labelEl.textContent = 'Previously Synced';
        detailsEl.textContent = `${response.dbCount} items in DB • Click sync to update`;
      } else {
        statusEl.className = 'sync-status pending';
        labelEl.textContent = 'Never Synced';
        detailsEl.textContent = 'Click "Sync to Database" to sync for the first time';
      }
    } else {
      statusEl.className = 'sync-status pending';
      labelEl.textContent = 'Sync Pending';
      const dbInfo = response.dbCount !== null ? ` • ${response.dbCount} in DB` : '';
      detailsEl.textContent = `Last sync: ${response.lastSyncDate}${dbInfo} • Will auto-sync on next browser restart`;
    }
  } catch (error) {
    console.error('Error getting status:', error);
    const statusEl = document.getElementById('sync-status');
    const labelEl = document.getElementById('sync-label');
    statusEl.className = 'sync-status error';
    labelEl.textContent = 'Error loading status';
  }
}

// Load reading list using chrome.readingList API
async function loadReadingList() {
  try {
    if (!chrome.readingList) {
      showMessage('error', 'Reading List API not available. Make sure you\'re using Chrome 120+');
      document.getElementById('total-count').textContent = 'N/A';
      return;
    }

    readingListItems = await chrome.readingList.query({});

    // Update stats
    const totalCount = readingListItems.length;
    const readCount = readingListItems.filter(item => item.hasBeenRead).length;
    const unreadCount = totalCount - readCount;

    document.getElementById('total-count').textContent = totalCount;
    document.getElementById('read-count').textContent = readCount;
    document.getElementById('unread-count').textContent = unreadCount;

    renderItemsList();

  } catch (error) {
    console.error('Error loading reading list:', error);
    showMessage('error', `Error: ${error.message}`);
  }
}

// Render the items list
function renderItemsList() {
  const listContainer = document.getElementById('items-list');

  if (readingListItems.length === 0) {
    listContainer.innerHTML = '<p style="color: #888; font-size: 13px; text-align: center;">No items in Reading List</p>';
    return;
  }

  const html = readingListItems.map(item => `
    <div class="item">
      <div class="item-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</div>
      <div class="item-url" title="${escapeHtml(item.url)}">${escapeHtml(item.url)}</div>
      <div class="item-status ${item.hasBeenRead ? 'read' : 'unread'}">
        ${item.hasBeenRead ? 'Read' : 'Unread'}
        ${item.creationTime ? ` • Added: ${formatDate(item.creationTime)}` : ''}
      </div>
    </div>
  `).join('');

  listContainer.innerHTML = html;
}

// Setup button event listeners
function setupEventListeners() {
  document.getElementById('sync-btn').addEventListener('click', manualSync);
  document.getElementById('export-btn').addEventListener('click', exportToJSON);
  document.getElementById('copy-btn').addEventListener('click', copyToClipboard);
  document.getElementById('toggle-list-btn').addEventListener('click', toggleItemsList);
}

// Manual sync to Supabase
async function manualSync() {
  const btn = document.getElementById('sync-btn');
  const originalText = btn.innerHTML;
  btn.innerHTML = '<span class="loading"></span> Syncing...';
  btn.disabled = true;

  try {
    const response = await chrome.runtime.sendMessage({ action: 'manual_sync' });

    if (response.status === 'success') {
      let message = '';
      if (response.count === 0) {
        message = `DB cleared (reading list is empty)`;
      } else {
        const failedInfo = response.failed > 0 ? ` (${response.failed} failed)` : '';
        message = `Synced ${response.synced || response.count} items to DB${failedInfo}`;
      }
      showMessage('success', message);
      await loadStatus();
    } else if (response.status === 'skipped') {
      showMessage('info', `Already synced today`);
    } else if (response.reason === 'supabase_not_configured') {
      showMessage('error', 'Supabase not configured. Update SUPABASE_ANON_KEY in background.js');
    } else {
      showMessage('error', `Sync failed: ${response.reason || 'Unknown error'}`);
    }
  } catch (error) {
    console.error('Sync error:', error);
    showMessage('error', `Sync error: ${error.message}`);
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

// Export reading list to JSON file (with Save As dialog)
async function exportToJSON() {
  if (readingListItems.length === 0) {
    showMessage('error', 'No items to export');
    return;
  }

  const exportData = {
    exported_at: new Date().toISOString(),
    source: 'Chrome Reading List Extension',
    count: readingListItems.length,
    items: readingListItems.map(item => ({
      title: item.title,
      url: item.url,
      hasBeenRead: item.hasBeenRead,
      creationTime: item.creationTime,
      lastUpdateTime: item.lastUpdateTime
    }))
  };

  const jsonString = JSON.stringify(exportData, null, 2);
  const base64Data = btoa(unescape(encodeURIComponent(jsonString)));
  const dataUrl = `data:application/json;base64,${base64Data}`;

  const filename = `reading_list_${formatDateForFilename(new Date())}.json`;

  try {
    await chrome.downloads.download({
      url: dataUrl,
      filename: filename,
      saveAs: true // Show save dialog
    });

    showMessage('success', `Exported ${readingListItems.length} items!`);
  } catch (error) {
    console.error('Download error:', error);
    showMessage('error', `Download failed: ${error.message}`);
  }
}

// Copy reading list to clipboard
async function copyToClipboard() {
  if (readingListItems.length === 0) {
    showMessage('error', 'No items to copy');
    return;
  }

  const exportData = {
    exported_at: new Date().toISOString(),
    source: 'Chrome Reading List Extension',
    count: readingListItems.length,
    items: readingListItems.map(item => ({
      title: item.title,
      url: item.url,
      hasBeenRead: item.hasBeenRead,
      creationTime: item.creationTime,
      lastUpdateTime: item.lastUpdateTime
    }))
  };

  const jsonString = JSON.stringify(exportData, null, 2);

  try {
    await navigator.clipboard.writeText(jsonString);
    showMessage('success', 'Copied to clipboard!');
  } catch (error) {
    console.error('Clipboard error:', error);
    showMessage('error', `Copy failed: ${error.message}`);
  }
}

// Toggle items list visibility
function toggleItemsList() {
  const listContainer = document.getElementById('items-list');
  const toggleBtn = document.getElementById('toggle-list-btn');

  if (listContainer.classList.contains('hidden')) {
    listContainer.classList.remove('hidden');
    toggleBtn.textContent = 'Hide Items';
  } else {
    listContainer.classList.add('hidden');
    toggleBtn.textContent = 'Show Items';
  }
}

// Show message
function showMessage(type, text) {
  const messageEl = document.getElementById('message');
  messageEl.className = `message ${type}`;
  messageEl.textContent = text;
  messageEl.classList.remove('hidden');

  setTimeout(() => {
    messageEl.classList.add('hidden');
  }, 5000);
}

// Utility functions
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text || '';
  return div.innerHTML;
}

function formatDate(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleDateString();
}

function formatDateForFilename(date) {
  return date.toISOString().slice(0, 10);
}
