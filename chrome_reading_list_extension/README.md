# Chrome Reading List → Supabase Sync Extension

An automated Chrome extension that syncs your Reading List to Supabase PostgreSQL once per day using the official `chrome.readingList` API.

## ✨ Features

- 🔄 **Auto-sync on browser startup** (once per day, first launch only)
- 📊 View Reading List statistics (total, read, unread)
- 💾 Syncs directly to Supabase PostgreSQL
- 📥 Manual export to JSON
- 📋 Copy to clipboard

## 🛠 Setup

### Step 1: Create the Database Table

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Open the **SQL Editor**
3. Run the SQL from `create_reading_list_table.sql`:

```sql
CREATE TABLE IF NOT EXISTS reading_list (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    has_been_read BOOLEAN DEFAULT FALSE,
    creation_time BIGINT,
    last_update_time BIGINT,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE reading_list ENABLE ROW LEVEL SECURITY;

-- Allow public read/write access
CREATE POLICY "Allow public read access" ON reading_list FOR SELECT USING (true);
CREATE POLICY "Allow public insert" ON reading_list FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update" ON reading_list FOR UPDATE USING (true);
```

### Step 2: Get Your Supabase Credentials

1. Go to **Project Settings** > **API**
2. Copy your:
   - **Project URL**: `https://[project-id].supabase.co`
   - **anon public key**: The `anon` key (safe for client-side use)

### Step 3: Configure the Extension

1. Open `background.js`
2. Update the configuration at the top:

```javascript
const SUPABASE_URL = 'https://your-project-id.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key-here';
```

### Step 4: Load the Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `chrome_reading_list_extension` folder

## 📁 How It Works

### Automatic Daily Sync

1. **First Chrome launch of the day**: Extension automatically syncs your Reading List
2. **Data sent to**: Your Supabase PostgreSQL `reading_list` table
3. **Upsert behavior**: New items are inserted, existing items are updated (matched by URL)
4. **Subsequent launches**: Skipped (already synced today)
5. **Next day**: Cycle repeats

### Database Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Auto-incrementing primary key |
| `url` | TEXT UNIQUE | Reading list item URL (unique constraint) |
| `title` | TEXT | Page title |
| `has_been_read` | BOOLEAN | Whether item has been read |
| `creation_time` | BIGINT | Chrome timestamp (ms since epoch) |
| `last_update_time` | BIGINT | Last update in Chrome (ms since epoch) |
| `synced_at` | TIMESTAMPTZ | Last sync timestamp |
| `created_at` | TIMESTAMPTZ | First time added to DB |
| `updated_at` | TIMESTAMPTZ | Last update in DB |

## 🔍 Query Examples

```sql
-- Get all unread items
SELECT title, url FROM reading_list WHERE has_been_read = FALSE;

-- Get recently added items
SELECT title, url, synced_at 
FROM reading_list 
ORDER BY creation_time DESC 
LIMIT 10;

-- Count by read status
SELECT 
  COUNT(*) FILTER (WHERE has_been_read = TRUE) as read,
  COUNT(*) FILTER (WHERE has_been_read = FALSE) as unread,
  COUNT(*) as total
FROM reading_list;
```

## 🔧 Troubleshooting

### "⚠️ Not Configured"

Update `SUPABASE_ANON_KEY` in `background.js` with your actual Supabase anon key.

### "Supabase error: 401"

Your anon key is invalid or expired. Get a new one from Supabase Dashboard.

### "Supabase error: 404"

The `reading_list` table doesn't exist. Run the SQL migration first.

### Extension not auto-syncing

1. Check the service worker logs:
   - Go to `chrome://extensions/`
   - Click "Service Worker" under the extension
   - View the console for logs

2. Check if already synced today by opening the popup

### "Reading List API not available"

Make sure you're using **Chrome 120 or later**.

## 📋 Requirements

- **Chrome 120+** (Reading List API requirement)
- **Supabase account** (free tier works fine)
- **macOS, Windows, or Linux**

## 🔐 Security Notes

- ✅ Uses Supabase anon key (public, safe for client-side)
- ✅ Row Level Security (RLS) enabled on table
- ✅ Only operations allowed by RLS policies are permitted
- ✅ No sensitive credentials exposed
- ⚠️ For production, consider using a service role key with server-side sync

## 🗂 Files

| File | Purpose |
|------|---------|
| `manifest.json` | Chrome extension manifest |
| `background.js` | Service worker with sync logic and Supabase API |
| `popup.html/js` | Extension popup UI |
| `create_reading_list_table.sql` | SQL migration for Supabase |
