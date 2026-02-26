#!/usr/bin/env python3
"""
LinkedIn Connection Remover
Automatically removes LinkedIn connections marked as "Remove" in the CSV.

Uses LinkedIn's internal Voyager API for reliable removal instead of
fragile DOM clicking.

Requirements:
    pip install playwright python-dotenv
    playwright install chromium
"""

import asyncio
import csv
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")


# Configuration
CSV_FILE = Path(__file__).parent / "LinkedIn Connections.csv"
BACKUP_FILE = Path(__file__).parent / "LinkedIn Connections_backup.csv"
HEADLESS = False  # Set to True to run in background (higher detection risk)
MIN_DELAY = 3  # Minimum seconds between actions
MAX_DELAY = 8  # Maximum seconds between actions


def backup_csv():
    """Create a backup of the original CSV."""
    if not BACKUP_FILE.exists():
        import shutil
        shutil.copy(CSV_FILE, BACKUP_FILE)
        print(f"Backup created at: {BACKUP_FILE}")


def get_connections_to_remove():
    """Get all connections marked for removal that haven't been processed."""
    connections = []

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Connection') == 'Remove':
                status = row.get('Removal Status', '')
                url = row.get('URL', '').strip()

                if url and status not in ('Removed', 'Skipped'):
                    connections.append(row)

    return connections


def update_status(url, status, error_msg=""):
    """Update the removal status for a connection."""
    rows = []

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # Add new columns if they don't exist
        if 'Removal Status' not in fieldnames:
            fieldnames += ['Removal Status']
        if 'Removal Error' not in fieldnames:
            fieldnames += ['Removal Error']
        if 'Removal Date' not in fieldnames:
            fieldnames += ['Removal Date']

        for row in reader:
            if row.get('URL') == url:
                row['Removal Status'] = status
                row['Removal Error'] = error_msg
                if status == 'Removed':
                    from datetime import datetime
                    row['Removal Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows.append(row)

    # Write back
    with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated: {url} -> {status}")


async def human_delay(page=None):
    """Add a random human-like delay."""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    print(f"Waiting {delay:.1f}s...")
    await asyncio.sleep(delay)

    # Optional: random mouse movements if page is provided
    if page:
        try:
            await page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
        except:
            pass


async def get_csrf_token(page):
    """Extract the CSRF token from LinkedIn cookies."""
    cookies = await page.context.cookies()
    for cookie in cookies:
        if cookie['name'] == 'JSESSIONID':
            return cookie['value'].strip('"')
    return None


async def remove_via_api(page, profile_url, name, csrf_token):
    """
    Remove a connection using LinkedIn's Voyager API.

    Strategy:
    1. Navigate to the profile page
    2. Extract the member's internal profile URN from the page
    3. Call the Voyager API to disconnect
    """
    print(f"\nProcessing: {name} - {profile_url}")

    # Extract public identifier from URL
    # e.g., "fara-amanda-safira-530a0316b" from ".../in/fara-amanda-safira-530a0316b"
    public_id = profile_url.rstrip('/').split('/in/')[-1]

    # Navigate to the profile to establish context and extract the member URN
    await page.goto(profile_url, wait_until='domcontentloaded', timeout=60000)
    await asyncio.sleep(random.uniform(2, 4))

    # Check if we are logged in
    if 'login' in page.url or 'authwall' in page.url:
        raise Exception("Session expired - not logged in")

    # Try API-based removal using the publicIdentifier
    result = await page.evaluate("""async (args) => {
        const { publicId, csrfToken } = args;
        const headers = {
            'csrf-token': csrfToken,
            'x-restli-protocol-version': '2.0.0',
            'x-li-lang': 'en_US',
            'x-li-track': '{"clientVersion":"1.13.8","mpVersion":"1.13.8","osName":"web","timezoneOffset":7,"timezone":"Asia/Jakarta","deviceFormFactor":"DESKTOP","mpName":"voyager-web"}',
        };

        // ---------------------------------------------------------------
        // Method 1: Get profile info -> extract profileId -> disconnect
        // ---------------------------------------------------------------
        try {
            // First, get the profile to find the internal profileId/URN
            const profileResp = await fetch(
                `https://www.linkedin.com/voyager/api/identity/profiles/${publicId}`,
                { headers }
            );

            if (profileResp.ok) {
                const profileData = await profileResp.json();
                // The entityUrn looks like "urn:li:fsd_profile:ACoAABxxxxxxxx"
                const entityUrn = profileData.entityUrn || profileData.data?.entityUrn;
                const miniProfile = profileData.miniProfile || profileData.data?.miniProfile;
                const profileUrn = entityUrn
                    || (miniProfile && miniProfile.entityUrn)
                    || null;

                if (profileUrn) {
                    // Try the disconnect action
                    const disconnectResp = await fetch(
                        `https://www.linkedin.com/voyager/api/identity/profiles/${publicId}/profileActions?action=disconnect`,
                        {
                            method: 'POST',
                            headers: {
                                ...headers,
                                'Content-Type': 'application/json; charset=UTF-8',
                            },
                        }
                    );

                    if (disconnectResp.ok || disconnectResp.status === 200) {
                        return { success: true, method: 'profileActions_disconnect' };
                    }

                    // Try alternative: remove via connections endpoint
                    const encodedUrn = encodeURIComponent(profileUrn);
                    const removeResp = await fetch(
                        `https://www.linkedin.com/voyager/api/relationships/connections/${encodedUrn}`,
                        {
                            method: 'DELETE',
                            headers: {
                                ...headers,
                                'Content-Type': 'application/json; charset=UTF-8',
                            },
                        }
                    );

                    if (removeResp.ok || removeResp.status === 200) {
                        return { success: true, method: 'connections_delete' };
                    }

                    return {
                        success: false,
                        error: `disconnect: ${disconnectResp.status} ${disconnectResp.statusText}, delete: ${removeResp.status} ${removeResp.statusText}`,
                        profileUrn: profileUrn
                    };
                }
            }
        } catch (e) {
            // Continue to next method
        }

        // ---------------------------------------------------------------
        // Method 2: Use the networkinfo endpoint to get connection details
        // ---------------------------------------------------------------
        try {
            const netResp = await fetch(
                `https://www.linkedin.com/voyager/api/identity/profiles/${publicId}/networkinfo`,
                { headers }
            );

            if (netResp.ok) {
                const netData = await netResp.json();
                const connectionUrn = netData.entityUrn || netData.data?.entityUrn;

                if (connectionUrn) {
                    const encodedUrn = encodeURIComponent(connectionUrn);
                    const removeResp = await fetch(
                        `https://www.linkedin.com/voyager/api/relationships/connections/${encodedUrn}`,
                        {
                            method: 'DELETE',
                            headers: {
                                ...headers,
                                'Content-Type': 'application/json; charset=UTF-8',
                            },
                        }
                    );

                    if (removeResp.ok) {
                        return { success: true, method: 'networkinfo_delete' };
                    }
                }
            }
        } catch (e) {
            // Continue
        }

        // ---------------------------------------------------------------
        // Method 3: Try direct disconnect with public ID
        // ---------------------------------------------------------------
        try {
            const resp = await fetch(
                `https://www.linkedin.com/voyager/api/identity/profiles/${publicId}/profileActions?action=disconnect`,
                {
                    method: 'POST',
                    headers: {
                        ...headers,
                        'Content-Type': 'application/json; charset=UTF-8',
                    },
                }
            );

            if (resp.ok) {
                return { success: true, method: 'direct_disconnect' };
            }

            return { success: false, error: `All API methods failed. Last: ${resp.status} ${resp.statusText}` };
        } catch (e) {
            return { success: false, error: `Exception: ${e.message}` };
        }
    }""", {"publicId": public_id, "csrfToken": csrf_token})

    if result and result.get('success'):
        print(f"  ✓ Removed via API ({result.get('method')})")
        return True
    else:
        error = result.get('error', 'Unknown error') if result else 'No result returned'
        print(f"  ✗ API removal failed: {error}")
        # Fall back to UI-based removal
        print("  Falling back to UI-based removal...")
        return await remove_via_ui(page, name)


async def remove_via_ui(page, name):
    """
    Fallback: Remove connection via UI interaction on the current profile page.
    Uses a more robust approach with explicit waits and verification.
    """
    # Step 1: Click the "More" button
    more_clicked = False

    # Try clicking the More button
    try:
        # Wait for the profile actions area to load
        await page.wait_for_selector(
            'button:has-text("More"), button[aria-label="More"]',
            timeout=5000
        )

        # Use JS to click the More button in the profile actions area
        more_clicked = await page.evaluate("""() => {
            // Look specifically in the top profile card area
            const cards = document.querySelectorAll('.pv-top-card, .scaffold-layout__main, section.artdeco-card');
            for (const card of cards) {
                const btns = card.querySelectorAll('button');
                for (const btn of btns) {
                    const text = btn.textContent.trim();
                    const label = btn.getAttribute('aria-label') || '';
                    if (text === 'More' || label === 'More' || label.includes('More actions')) {
                        btn.click();
                        return true;
                    }
                }
            }
            // Broader fallback
            const allBtns = Array.from(document.querySelectorAll('button'));
            const moreBtn = allBtns.find(b => {
                const span = b.querySelector('span.artdeco-button__text');
                return (span && span.textContent.trim() === 'More') ||
                       b.getAttribute('aria-label') === 'More';
            });
            if (moreBtn) { moreBtn.click(); return true; }
            return false;
        }""")
    except:
        pass

    if not more_clicked:
        raise Exception("Could not click 'More' button")

    await asyncio.sleep(2)

    # Step 2: Click "Remove connection" from the dropdown
    remove_clicked = await page.evaluate("""() => {
        // Look for any clickable element containing "Remove connection"
        const items = document.querySelectorAll(
            'div[role="menuitem"], li, button, a, span'
        );
        for (const item of items) {
            const text = item.textContent.trim();
            if (text === 'Remove connection' || text === 'Remove from network') {
                item.click();
                return true;
            }
        }
        // Try aria-label approach
        const labeled = document.querySelector('[aria-label="Remove connection"]');
        if (labeled) { labeled.click(); return true; }
        return false;
    }""")

    if not remove_clicked:
        raise Exception("Could not find 'Remove connection' option in menu")

    print("  Clicked 'Remove connection'")
    await asyncio.sleep(2)

    # Step 3: Confirm in the modal dialog
    confirmed = await page.evaluate("""() => {
        // Look for confirmation button in a modal/dialog
        const modals = document.querySelectorAll(
            'div[role="dialog"], div[role="alertdialog"], ' +
            'artdeco-modal, div.artdeco-modal, div[data-test-modal]'
        );
        for (const modal of modals) {
            const buttons = modal.querySelectorAll('button');
            for (const btn of buttons) {
                const text = btn.textContent.trim();
                if (text === 'Remove' || text === 'Yes, remove' || text === 'Confirm') {
                    btn.click();
                    return true;
                }
            }
        }
        // Broader fallback: any visible primary button saying "Remove"
        const allBtns = Array.from(document.querySelectorAll('button'));
        const removeBtn = allBtns.find(b => {
            const text = b.textContent.trim();
            return text === 'Remove' && b.offsetParent !== null;
        });
        if (removeBtn) { removeBtn.click(); return true; }
        return false;
    }""")

    if not confirmed:
        # Last resort: press Enter
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
        print("  Confirmed via Enter key (last resort)")
    else:
        print("  Confirmed removal in modal")

    await asyncio.sleep(2)

    # Verify: check if the page now shows "Connect" instead of "Remove"
    is_removed = await page.evaluate("""() => {
        // After removal, the profile should show "Connect" button instead
        const btns = Array.from(document.querySelectorAll('button'));
        const connectBtn = btns.find(b => b.textContent.trim() === 'Connect');
        // If we see "Connect", removal was successful
        if (connectBtn) return true;
        // If we don't see "Message" anymore, also likely successful
        const messageBtn = btns.find(b => b.textContent.trim() === 'Message');
        return !messageBtn;
    }""")

    if is_removed:
        print("  ✓ Verified: connection removed (Connect button appeared)")
        return True
    else:
        print("  ⚠ Could not verify removal - may not have worked")
        raise Exception("Removal not verified - Connect button did not appear")


async def main():
    # Create backup
    backup_csv()

    # Get connections to remove
    connections = get_connections_to_remove()

    if not connections:
        print("No connections found to remove (or all already processed)!")
        return

    print(f"Found {len(connections)} connections to remove")
    print("Starting browser...")

    # Get credentials
    email = os.getenv('LINKEDIN_EMAIL') or input("Enter LinkedIn email: ")
    password = os.getenv('LINKEDIN_PASSWORD') or input("Enter LinkedIn password: ")

    async with async_playwright() as p:
        # Launch browser with anti-detection settings
        browser = await p.chromium.launch(
            headless=HEADLESS,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        )

        # Remove webdriver property
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()

        try:
            # Navigate to LinkedIn login
            print("Navigating to LinkedIn...")
            await page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)

            await human_delay()

            # Login
            print("Logging in...")
            await page.fill('input#username', email)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.fill('input#password', password)

            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.click('button[type="submit"]')

            # Wait for navigation - check various successful login indicators
            try:
                await page.wait_for_url('**/feed/**', timeout=10000)
            except:
                # Not on feed, check if we're logged in elsewhere
                current_url = page.url
                print(f"Current URL: {current_url}")

                # Check if we hit a security challenge or 2FA
                if 'challenge' in current_url or 'checkpoint' in current_url:
                    print("\n" + "="*50)
                    print("SECURITY CHALLENGE DETECTED")
                    print("Please complete the verification in the browser window.")
                    print("Waiting for challenge to complete...")
                    print("="*50 + "\n")

                    # Poll for URL change (challenge completion)
                    print("You have 5 minutes to complete the verification...")
                    for i in range(300):  # Wait up to 5 minutes
                        await asyncio.sleep(1)
                        new_url = page.url
                        if 'challenge' not in new_url and 'checkpoint' not in new_url and 'login' not in new_url:
                            print(f"Challenge complete! New URL: {new_url}")
                            current_url = new_url
                            break
                        # Print progress every 30 seconds
                        if i > 0 and i % 30 == 0:
                            print(f"Still waiting... ({i//60} minutes elapsed)")
                    else:
                        raise Exception("Security challenge timeout - please try again later")

                # Check if login was successful (not on login page anymore)
                if 'login' not in current_url and 'authwall' not in current_url:
                    print("Logged in successfully!")
                else:
                    raise Exception("Login may have failed - still on login page")

            await human_delay()

            # Get CSRF token for API calls
            csrf_token = await get_csrf_token(page)
            if csrf_token:
                print(f"Got CSRF token: {csrf_token[:20]}...")
            else:
                print("WARNING: Could not get CSRF token, will use UI-only approach")

            # Process each connection
            success_count = 0
            failed_count = 0
            api_method_stats = {}

            for i, conn in enumerate(connections, 1):
                name = f"{conn.get('First Name', '')} {conn.get('Last Name', '')}".strip()
                url = conn.get('URL', '').strip()

                print(f"\n{'='*60}")
                print(f"[{i}/{len(connections)}] {name}")
                print(f"{'='*60}")

                try:
                    if csrf_token:
                        result = await remove_via_api(page, url, name, csrf_token)
                    else:
                        # Navigate to profile and use UI
                        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                        await asyncio.sleep(random.uniform(2, 4))
                        result = await remove_via_ui(page, name)

                    if result:
                        update_status(url, 'Removed')
                        success_count += 1
                except Exception as e:
                    error_msg = str(e)[:100]  # Truncate long errors
                    update_status(url, 'Failed', error_msg)
                    failed_count += 1
                    print(f"  FAILED: {error_msg}")

                    # If we hit a rate limit or auth error, stop
                    if 'auth' in error_msg.lower() or 'limit' in error_msg.lower() or 'session expired' in error_msg.lower():
                        print("\nStopping due to auth/rate limit issue")
                        break

                # Longer pause every 10 removals to be safer
                if i % 10 == 0:
                    print(f"\n=== Pausing for 30 seconds (batch of 10 completed) ===")
                    print(f"Progress: {success_count} removed, {failed_count} failed")
                    await asyncio.sleep(30)
                else:
                    await human_delay()

            print(f"\n{'='*60}")
            print(f"=== SUMMARY ===")
            print(f"Successfully removed: {success_count}")
            print(f"Failed: {failed_count}")
            print(f"Remaining: {len(connections) - success_count - failed_count}")
            print(f"{'='*60}")

        finally:
            # Keep browser open for a bit to see final state
            print("\nKeeping browser open for 10 seconds...")
            await asyncio.sleep(10)
            await browser.close()


if __name__ == '__main__':
    print("=" * 50)
    print("LinkedIn Connection Remover")
    print("=" * 50)
    asyncio.run(main())
