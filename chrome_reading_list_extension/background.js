// Background Service Worker for Reading List Sync
// Syncs Chrome Reading List to Supabase PostgreSQL daily

// ============================================================================
// CONFIGURATION - Update these with your Supabase credentials
// ============================================================================
const SUPABASE_URL = 'https://kofyjyyvzgsqxdryngnz.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_pA-vht_UxHBopOAXPtF1xg_BRFYoEyX'; // Get from Supabase Dashboard > Settings > API

const STORAGE_KEY = 'lastSyncDate';
const TABLE_NAME = 'reading_list';

// ============================================================================
// SUPABASE API HELPERS
// ============================================================================

async function supabaseRequest(endpoint, method = 'GET', body = null) {
    const headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    };

    const options = {
        method,
        headers
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${SUPABASE_URL}/rest/v1/${endpoint}`, options);

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Supabase error: ${response.status} - ${errorText}`);
    }

    // Return null for empty responses (like successful deletes)
    const text = await response.text();
    return text ? JSON.parse(text) : null;
}

// Upsert a single reading list item
async function upsertItem(item) {
    const data = {
        url: item.url,
        title: item.title,
        has_been_read: item.hasBeenRead || false,
        creation_time: item.creationTime,
        last_update_time: item.lastUpdateTime,
        synced_at: new Date().toISOString()
    };

    // Use Supabase upsert with on_conflict
    const headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=representation'
    };

    // Use on_conflict=url to properly upsert based on unique URL
    const response = await fetch(`${SUPABASE_URL}/rest/v1/${TABLE_NAME}?on_conflict=url`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upsert failed for ${item.url}: ${errorText}`);
    }

    return await response.json();
}

// Batch upsert all items
async function syncToSupabase(items) {
    console.log(`[Reading List Sync] Syncing ${items.length} items to Supabase...`);

    const results = {
        success: 0,
        failed: 0,
        errors: []
    };

    // Process items in batches of 50 to avoid overwhelming the API
    const BATCH_SIZE = 50;

    for (let i = 0; i < items.length; i += BATCH_SIZE) {
        const batch = items.slice(i, i + BATCH_SIZE);

        // Prepare batch data
        const batchData = batch.map(item => ({
            url: item.url,
            title: item.title,
            has_been_read: item.hasBeenRead || false,
            creation_time: item.creationTime,
            last_update_time: item.lastUpdateTime,
            synced_at: new Date().toISOString()
        }));

        try {
            const headers = {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
                'Content-Type': 'application/json',
                'Prefer': 'resolution=merge-duplicates,return=representation'
            };

            // Use on_conflict=url to properly upsert based on unique URL
            const response = await fetch(`${SUPABASE_URL}/rest/v1/${TABLE_NAME}?on_conflict=url`, {
                method: 'POST',
                headers,
                body: JSON.stringify(batchData)
            });

            if (response.ok) {
                results.success += batch.length;
                console.log(`[Reading List Sync] Batch ${Math.floor(i / BATCH_SIZE) + 1}: ${batch.length} items synced`);
            } else {
                const errorText = await response.text();
                results.failed += batch.length;
                results.errors.push(`Batch ${Math.floor(i / BATCH_SIZE) + 1}: ${errorText}`);
                console.error(`[Reading List Sync] Batch failed:`, errorText);
            }
        } catch (error) {
            results.failed += batch.length;
            results.errors.push(`Batch ${Math.floor(i / BATCH_SIZE) + 1}: ${error.message}`);
            console.error(`[Reading List Sync] Batch error:`, error);
        }
    }

    return results;
}

// Get count from Supabase
async function getSupabaseCount() {
    try {
        const headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            'Prefer': 'count=exact'
        };

        const response = await fetch(`${SUPABASE_URL}/rest/v1/${TABLE_NAME}?select=id`, {
            method: 'HEAD',
            headers
        });

        const count = response.headers.get('content-range');
        if (count) {
            const match = count.match(/\/(\d+)/);
            return match ? parseInt(match[1]) : 0;
        }
        return 0;
    } catch (error) {
        console.error('[Reading List Sync] Error getting count:', error);
        return null;
    }
}

// Delete ALL items from Supabase (for full replace sync)
async function deleteAllItems() {
    console.log('[Reading List Sync] Deleting all items from database...');

    try {
        const headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        };

        // Delete all rows by using a filter that matches everything (id > 0)
        const response = await fetch(
            `${SUPABASE_URL}/rest/v1/${TABLE_NAME}?id=gt.0`,
            {
                method: 'DELETE',
                headers
            }
        );

        if (response.ok) {
            console.log('[Reading List Sync] Successfully deleted all items');
            return { success: true };
        } else {
            const errorText = await response.text();
            console.error('[Reading List Sync] Delete all failed:', errorText);
            return { success: false, error: errorText };
        }
    } catch (error) {
        console.error('[Reading List Sync] Error deleting all items:', error);
        return { success: false, error: error.message };
    }
}


// ============================================================================
// SYNC LOGIC
// ============================================================================

// Check if we should sync today
async function shouldSyncToday() {
    const result = await chrome.storage.local.get(STORAGE_KEY);
    const lastSyncDate = result[STORAGE_KEY];
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format

    console.log(`[Reading List Sync] Last sync: ${lastSyncDate}, Today: ${today}`);

    return lastSyncDate !== today;
}

// Mark today as synced
async function markSyncComplete() {
    const today = new Date().toISOString().split('T')[0];
    await chrome.storage.local.set({ [STORAGE_KEY]: today });
    console.log(`[Reading List Sync] Marked sync complete for ${today}`);
}

// Get all reading list items from Chrome
async function getReadingListItems() {
    try {
        if (!chrome.readingList) {
            console.error('[Reading List Sync] Reading List API not available');
            return null;
        }

        const items = await chrome.readingList.query({});
        console.log(`[Reading List Sync] Found ${items.length} items in Chrome`);
        return items;
    } catch (error) {
        console.error('[Reading List Sync] Error getting reading list:', error);
        return null;
    }
}

// Main sync function - Full Replace approach
// Deletes all items from DB, then inserts current reading list
async function performSync(forceSync = false) {
    console.log('[Reading List Sync] Starting sync...');

    // Check configuration
    if (SUPABASE_ANON_KEY === 'YOUR_SUPABASE_ANON_KEY_HERE') {
        console.error('[Reading List Sync] Supabase not configured! Update SUPABASE_ANON_KEY in background.js');
        return { status: 'error', reason: 'supabase_not_configured' };
    }

    // Check if we already synced today (skip check if force sync)
    if (!forceSync && !await shouldSyncToday()) {
        console.log('[Reading List Sync] Already synced today, skipping');
        return { status: 'skipped', reason: 'already_synced_today' };
    }

    // Get reading list items
    const items = await getReadingListItems();
    if (!items) {
        return { status: 'error', reason: 'failed_to_get_items' };
    }

    // Step 1: Delete all existing items from DB
    console.log('[Reading List Sync] Step 1: Clearing database...');
    const deleteResult = await deleteAllItems();
    if (!deleteResult.success) {
        console.error('[Reading List Sync] Failed to clear database:', deleteResult.error);
        return { status: 'error', reason: 'failed_to_clear_db', error: deleteResult.error };
    }

    // Step 2: Insert all current reading list items
    if (items.length === 0) {
        console.log('[Reading List Sync] Reading list is empty - DB now cleared');
        await markSyncComplete();
        return {
            status: 'success',
            count: 0,
            message: 'Reading list empty, DB cleared'
        };
    }

    console.log(`[Reading List Sync] Step 2: Inserting ${items.length} items...`);
    try {
        const syncResult = await syncToSupabase(items);

        if (syncResult.success > 0) {
            await markSyncComplete();
            return {
                status: 'success',
                count: items.length,
                synced: syncResult.success,
                failed: syncResult.failed
            };
        } else {
            return {
                status: 'error',
                reason: 'all_items_failed',
                errors: syncResult.errors
            };
        }
    } catch (error) {
        console.error('[Reading List Sync] Sync error:', error);
        return { status: 'error', reason: error.message };
    }
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

// Run on browser startup
chrome.runtime.onStartup.addListener(async () => {
    console.log('[Reading List Sync] Browser started');

    // Small delay to ensure Chrome is fully initialized
    await new Promise(resolve => setTimeout(resolve, 2000));

    const result = await performSync();
    console.log('[Reading List Sync] Startup sync result:', result);
});

// Run on extension installation/update
chrome.runtime.onInstalled.addListener(async (details) => {
    console.log('[Reading List Sync] Extension installed/updated:', details.reason);

    // Small delay to ensure Chrome is fully initialized
    await new Promise(resolve => setTimeout(resolve, 1000));

    const result = await performSync();
    console.log('[Reading List Sync] Install sync result:', result);
});

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'manual_sync') {
        // Force sync regardless of date
        (async () => {
            const result = await performSync(true);
            sendResponse(result);
        })();
        return true; // Keep message channel open for async response
    }

    if (message.action === 'get_status') {
        (async () => {
            const result = await chrome.storage.local.get(STORAGE_KEY);
            const items = await getReadingListItems();
            const shouldSync = await shouldSyncToday();
            const dbCount = await getSupabaseCount();
            sendResponse({
                lastSyncDate: result[STORAGE_KEY] || 'Never',
                itemCount: items ? items.length : 0,
                dbCount: dbCount,
                shouldSyncToday: shouldSync,
                configured: SUPABASE_ANON_KEY !== 'YOUR_SUPABASE_ANON_KEY_HERE'
            });
        })();
        return true;
    }

    if (message.action === 'reset_sync') {
        chrome.storage.local.remove(STORAGE_KEY);
        sendResponse({ status: 'reset' });
    }

    if (message.action === 'get_items') {
        (async () => {
            const items = await getReadingListItems();
            sendResponse({ items: items || [] });
        })();
        return true;
    }
});

// Export for testing
if (typeof module !== 'undefined') {
    module.exports = { performSync, getReadingListItems, syncToSupabase };
}
