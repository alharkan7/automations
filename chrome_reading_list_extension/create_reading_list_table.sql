-- Create reading_list table for Chrome Reading List sync
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/kofyjyyvzgsqxdryngnz/sql

CREATE TABLE IF NOT EXISTS reading_list (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    has_been_read BOOLEAN DEFAULT FALSE,
    creation_time BIGINT,           -- Chrome timestamp (ms since epoch)
    last_update_time BIGINT,        -- Chrome timestamp (ms since epoch)
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on URL for faster lookups (upsert operations)
CREATE INDEX IF NOT EXISTS idx_reading_list_url ON reading_list(url);

-- Create index on has_been_read for filtering
CREATE INDEX IF NOT EXISTS idx_reading_list_read_status ON reading_list(has_been_read);

-- Enable Row Level Security (RLS)
ALTER TABLE reading_list ENABLE ROW LEVEL SECURITY;

-- Create policy to allow anonymous read access (for your website)
CREATE POLICY "Allow public read access" ON reading_list
    FOR SELECT USING (true);

-- Create policy to allow insert/update via anon key (for the extension)
-- Note: For production, you might want to use a service role key instead
CREATE POLICY "Allow public insert" ON reading_list
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update" ON reading_list
    FOR UPDATE USING (true);

CREATE POLICY "Allow public delete" ON reading_list
    FOR DELETE USING (true);

-- Optional: Create a function to handle upsert with updated_at timestamp
CREATE OR REPLACE FUNCTION update_reading_list_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at on changes
DROP TRIGGER IF EXISTS reading_list_updated_at ON reading_list;
CREATE TRIGGER reading_list_updated_at
    BEFORE UPDATE ON reading_list
    FOR EACH ROW
    EXECUTE FUNCTION update_reading_list_timestamp();

-- Verify table was created
SELECT 'reading_list table created successfully!' as status;
