#!/usr/bin/env python
"""
GitHub Video Uploader - Browser Automation (Improved)

Uploads videos to GitHub's user-images CDN via drag-and-drop in web editor.
Extracts CDN links and updates README.md with embedded video tags.

Features:
- Saves browser session (no need to login every time)
- Handles GitHub's CodeMirror editor
- Automatic retry with better error handling
"""

import asyncio
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright


class GitHubVideoUploader:
    """Automate GitHub video uploads via browser automation."""

    def __init__(self, repo_url: str, readme_path: Path, video_dir: Path, session_file: Path = None):
        self.repo_url = repo_url
        self.readme_path = readme_path
        self.video_dir = video_dir
        self.session_file = session_file or Path.home() / ".github_session.json"
        self.cdn_links = {}

    async def get_page_content(self, page) -> str:
        """Extract page content from GitHub's editor (new or old)."""
        try:
            # Method 1: Try new contenteditable editor (2025+)
            content = await page.evaluate("""
                () => {
                    const editor = document.querySelector('[contenteditable="true"]');
                    return editor ? editor.innerText : '';
                }
            """)
            if content:
                return content
        except:
            pass

        try:
            # Method 2: Try CodeMirror (old GitHub editor)
            content = await page.evaluate("""
                () => {
                    const cm = document.querySelector('.CodeMirror');
                    return cm ? cm.CodeMirror.getValue() : '';
                }
            """)
            if content:
                return content
        except:
            pass

        # Method 3: Try textarea fallback
        try:
            textarea = await page.locator('textarea[name="value"]').input_value()
            if textarea:
                return textarea
        except:
            pass

        return ""

    async def upload_video(self, page, video_path: Path) -> str:
        """
        Upload a single video via drag-and-drop.
        Returns the CDN link.
        """
        print(f"Uploading {video_path.name}...")

        # Wait for page to load completely
        try:
            await page.wait_for_load_state('domcontentloaded', timeout=10000)
        except:
            pass  # Page might already be loaded

        # Wait for editor to be available (new or old)
        try:
            # Try new contenteditable editor first
            try:
                await page.wait_for_selector('[contenteditable="true"]', timeout=5000)
                print("  ✓ Found new GitHub editor (contenteditable)")
            except:
                # Fallback to old CodeMirror editor
                await page.wait_for_selector('.CodeMirror', timeout=5000)
                print("  ✓ Found old GitHub editor (CodeMirror)")
        except Exception as e:
            raise Exception(f"Could not find GitHub editor: {e}")

        # Try multiple upload methods
        upload_success = False

        # Method 1: File input (GitHub's hidden input)
        try:
            file_input = page.locator('input[type="file"]').first
            if await file_input.count() > 0:
                print("  ✓ Found file input, uploading...")
                await file_input.set_input_files(str(video_path))
                upload_success = True
                print("  ✓ File input set")
        except Exception as e:
            print(f"  ⚠️  File input method failed: {e}")

        if not upload_success:
            raise Exception("All upload methods failed")

        # Get editor content BEFORE upload (for comparison)
        content_before = await self.get_page_content(page)

        # Wait for upload to complete - GitHub needs time to process and insert the link
        print("  ⏳ Waiting for GitHub to process upload (this may take 10-30 seconds)...")
        await asyncio.sleep(10)  # Give GitHub more time to upload

        # Check multiple times for the link to appear
        for attempt in range(6):  # Try 6 times (30 seconds total)
            print(f"  🔍 Checking for uploaded file... (attempt {attempt + 1}/6)")

            # Get editor content AFTER upload
            content_after = await self.get_page_content(page)

            # Find NEW URLs that weren't there before
            urls_before = set(re.findall(r'https?://[^\s\)"\>]+', content_before))
            urls_after = set(re.findall(r'https?://[^\s\)"\>]+', content_after))
            new_urls = urls_after - urls_before

            # Debug: Show what we found
            if len(new_urls) > 0:
                print(f"  🆕 Found {len(new_urls)} new URL(s)")
                for url in new_urls:
                    if 'user-attachments/assets' in url or 'user-images.githubusercontent.com' in url:
                        print(f"  ✅ Found upload URL: {url}")
                        return url

            # Debug: Show a snippet of content
            if len(content_after) > 0:
                preview = content_after[:300] if len(content_after) > 300 else content_after
                print(f"  📄 Editor content preview: {preview}...")

            # Wait before next attempt
            if attempt < 5:
                print("  ⏳ Link not found yet, waiting 5 more seconds...")
                await asyncio.sleep(5)

        raise Exception("Could not find uploaded file URL in editor content after 30 seconds")

        # Fallback: Parse from page content
        await asyncio.sleep(2)
        content = await self.get_page_content(page)
        match = re.search(r'https://user-images\.githubusercontent\.com/[^\s\)"\>]+', content)

        if match:
            cdn_link = match.group(0)
            print(f"  ✅ CDN link from content: {cdn_link}")
            return cdn_link

        # Last resort: Check page source
        page_source = await page.content()
        match = re.search(r'https://user-images\.githubusercontent\.com/[^\s\)"\>]+\.mp4', page_source)

        if match:
            cdn_link = match.group(0)
            print(f"  ✅ CDN link from source: {cdn_link}")
            return cdn_link

        raise Exception("Could not extract CDN link")

    async def run(self, headless: bool = False):
        """Main upload workflow."""
        video_files = {
            'github-ready_explainer_video.mp4': 'explainer_video',
            'github-ready_explainer_podcast.mp4': 'explainer_podcast'
        }

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )

            # Load or create browser context
            context = None
            if self.session_file.exists():
                print(f"📂 Loading saved session from {self.session_file}")
                try:
                    context = await browser.new_context(
                        storage_state=str(self.session_file),
                        viewport={'width': 1280, 'height': 800},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    )
                except Exception as e:
                    print(f"⚠️  Could not load session: {e}")
                    context = None

            if not context:
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )

            page = await context.new_page()

            try:
                # Navigate to README edit page
                edit_url = f"{self.repo_url}/edit/main/README.md"
                print(f"Navigating to: {edit_url}")

                try:
                    await page.goto(edit_url, wait_until='domcontentloaded', timeout=30000)
                except Exception as e:
                    print(f"⚠️  Navigation failed: {e}")
                    print("Retrying with networkidle...")
                    await page.goto(edit_url, wait_until='commit', timeout=60000)

                # Check if authentication is needed
                if 'login' in page.url or 'session' in page.url:
                    print("\n" + "="*60)
                    print("🔐 AUTHENTICATION REQUIRED")
                    print("="*60)
                    print("Please log in to GitHub in the browser window.")
                    print("The script will continue after you're logged in.")
                    print("Your session will be saved for future use.")
                    print("="*60 + "\n")

                    # Wait for user to log in
                    await page.wait_for_url(
                        "**/edit/main/README.md",
                        timeout=180000  # 3 minutes
                    )
                    print("✅ Authentication successful!")

                    # Save session for future use
                    print(f"💾 Saving session to {self.session_file}")
                    await context.storage_state(path=str(self.session_file))
                else:
                    print("✅ Using saved session or public repo accessible")

                # Upload each video
                for video_filename, video_key in video_files.items():
                    video_path = self.video_dir / video_filename

                    if not video_path.exists():
                        print(f"⚠️  Video not found: {video_path}")
                        continue

                    try:
                        cdn_link = await self.upload_video(page, video_path)
                        self.cdn_links[video_key] = cdn_link
                    except Exception as e:
                        print(f"❌ Failed to upload {video_filename}: {e}")
                        continue

                # Print results
                print("\n" + "="*60)
                print("UPLOAD RESULTS")
                print("="*60)
                for video_key, cdn_link in self.cdn_links.items():
                    print(f"{video_key}: {cdn_link}")
                print("="*60 + "\n")

                # Generate updated README section
                self.generate_readme_update()

                return len(self.cdn_links) > 0

            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                return False

            finally:
                await browser.close()

    def generate_readme_update(self):
        """Generate the updated README section with CDN links."""

        if not self.cdn_links:
            print("⚠️  No CDN links extracted, cannot update README")
            return

        print("README Update Instructions:")
        print("="*60)

        # Explainer Video
        if 'explainer_video' in self.cdn_links:
            cdn_link = self.cdn_links['explainer_video']
            print("\n### 🎬 Explainer Video (22 seconds)")
            print("Replace the video tag with:")
            print(f'<video src="{cdn_link}" controls="controls" style="max-width: 730px; margin: 10px 0;">')
            print("</video>")
            print("\nThen delete the badge link section below it.")

        # Podcast
        if 'explainer_podcast' in self.cdn_links:
            cdn_link = self.cdn_links['explainer_podcast']
            print("\n### 🎙️ Podcast Overview (2m 20s)")
            print("Replace the video tag with:")
            print(f'<video src="{cdn_link}" controls="controls" style="max-width: 730px; margin: 10px 0;">')
            print("</video>")
            print("\nThen delete the badge link section below it.")

        print("\n" + "="*60)


async def main():
    """Main entry point."""
    repo_url = "https://github.com/EndUser123/gitready"
    readme_path = Path("P:/packages/gitready/README.md")
    video_dir = Path("P:/packages/gitready/assets/videos")
    session_file = Path.home() / ".github_video_uploader_session.json"

    uploader = GitHubVideoUploader(repo_url, readme_path, video_dir, session_file)

    # Run with headed browser for initial authentication
    print("Starting GitHub video uploader...")
    print("Note: Browser window will open for authentication if needed.\n")
    print("Your session will be saved automatically after first login.")
    print("Future runs will not require authentication.\n")

    success = await uploader.run(headless=False)

    if success:
        print("\n✅ Upload completed successfully!")
        print("Follow the instructions above to update your README.")
    else:
        print("\n❌ Upload failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
