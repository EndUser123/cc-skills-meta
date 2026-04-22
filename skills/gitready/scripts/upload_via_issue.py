#!/usr/bin/env python
"""
Upload video to GitHub via issue comment to get user-images CDN URL.

This method creates a temporary issue, uploads the video as an attachment,
and extracts the resulting user-images.githubusercontent.com URL.
"""

import asyncio
import re
import subprocess
from pathlib import Path

from playwright.async_api import async_playwright


async def upload_video_via_issue(video_path: Path, repo_url: str, session_file: Path):
    """Upload video via GitHub issue to get permanent user-images URL."""

    issue_url = f"{repo_url}/issues/new"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state=str(session_file),
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        try:
            # Navigate to new issue page
            print(f'Navigating to: {issue_url}')
            await page.goto(issue_url, wait_until='domcontentloaded', timeout=30000)

            # Check if authentication is needed
            if 'login' in page.url or 'session' in page.url:
                print('\n' + '='*60)
                print('🔐 AUTHENTICATION REQUIRED')
                print('='*60)
                print('Please log in to GitHub in the browser window.')
                print('='*60 + '\n')

                await page.wait_for_url('**/issues/new', timeout=180000)
                print('✅ Authentication successful!')

                # Save session for future use
                await context.storage_state(path=str(session_file))

            # Wait for page to load
            await asyncio.sleep(2)

            # Try multiple selectors for issue title
            title_selectors = [
                'input[name="issue[title]"]',
                '#issue_title',
                'input[aria-label="Title"]',
                'input[id*="title"]'
            ]

            title_filled = False
            for selector in title_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.fill(selector, 'Video upload for README (temporary issue)')
                    title_filled = True
                    print(f'✅ Filled title using selector: {selector}')
                    break
                except:
                    continue

            if not title_filled:
                # Try clicking in the title field directly
                print('⚠️  Standard selectors failed, trying alternative approach...')
                try:
                    # Look for any input that might be the title field
                    inputs = await page.locator('input').all()
                    for inp in inputs:
                        placeholder = await inp.get_attribute('placeholder')
                        if placeholder and 'title' in placeholder.lower():
                            await inp.click()
                            await inp.fill('Video upload for README (temporary issue)')
                            title_filled = True
                            print('✅ Filled title via placeholder text')
                            break
                except Exception as e:
                    print(f'⚠️  Alternative approach failed: {e}')

            if not title_filled:
                print('❌ Could not find issue title field. Page may have changed.')
                print('Please fill in the title manually and press Enter...')
                input()

            # Upload video
            print(f'\nUploading video: {video_path.name}')

            # Wait for file input
            try:
                await page.wait_for_selector('input[type="file"]', timeout=10000)
                file_input = page.locator('input[type="file"]').first
                await file_input.set_input_files(str(video_path))
                print('✅ File uploaded, waiting for processing...')
            except Exception as e:
                print(f'❌ File upload failed: {e}')
                await browser.close()
                return None

            # Wait for GitHub to process the upload
            await asyncio.sleep(15)

            # Check multiple locations for the URL
            user_images_url = None

            # Method 1: Check the textarea markdown content
            try:
                body_selectors = [
                    'textarea[name="issue[body]"]',
                    '#issue_body',
                    'textarea[aria-label="Body"]',
                    'textarea[id*="body"]'
                ]

                for selector in body_selectors:
                    try:
                        content = await page.locator(selector).input_value()
                        match = re.search(r'https://user-images\.githubusercontent\.com/[^\s\)\"]*\.mp4', content)
                        if match:
                            user_images_url = match.group(0)
                            print(f'✅ Found URL in body: {user_images_url}')
                            break
                    except:
                        continue
            except Exception as e:
                print(f'⚠️  Method 1 failed: {e}')

            # Method 2: Check page source
            if not user_images_url:
                try:
                    page_source = await page.content()
                    match = re.search(r'https://user-images\.githubusercontent\.com/[^\s\)\"]*\.mp4', page_source)
                    if match:
                        user_images_url = match.group(0)
                        print(f'✅ Found URL in page source: {user_images_url}')
                except Exception as e:
                    print(f'⚠️  Method 2 failed: {e}')

            # Verify URL is accessible
            if user_images_url:
                print('\n🔍 Verifying URL is accessible...')
                result = subprocess.run(
                    ['curl', '-I', user_images_url],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if '200' in result.stdout or '206' in result.stdout:
                    print('✅ URL is accessible!')
                    print(f'\n{"="*60}')
                    print('USER-IMAGES CDN URL')
                    print('='*60)
                    print(f'{user_images_url}')
                    print('='*60)

                    print('\n✅ Success! You can now use this URL in your README:')
                    print(f'<video src="{user_images_url}" controls="controls" style="max-width: 730px; margin: 10px 0;">')
                    print('</video>')

                    print('\n⚠️  IMPORTANT: Close the browser WITHOUT submitting the issue.')
                    print('   We don\'t need to actually create the issue.')
                    input('\nPress Enter when ready to close browser...')

                    return user_images_url
                else:
                    print('⚠️  URL returned non-200 status:')
                    print(result.stdout[:300])
            else:
                print('❌ Could not find uploaded video URL')
                print('Please check if the video appears in the issue body, then copy the URL manually.')
                input('\nPress Enter to close browser...')

        except Exception as e:
            print(f'❌ Error: {e}')
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

    return None


async def main():
    """Main entry point."""
    repo_url = "https://github.com/EndUser123/gitready"
    video_path = Path("P:/packages/gitready/assets/videos/github-ready_explainer_video.mp4")
    session_file = Path.home() / ".github_video_uploader_session.json"

    if not video_path.exists():
        print(f'❌ Video not found: {video_path}')
        return

    print('='*60)
    print('GITHUB ISSUE VIDEO UPLOADER')
    print('='*60)
    print('This script will:')
    print('1. Open a browser to create a new GitHub issue')
    print('2. Upload the video as an attachment')
    print('3. Extract the user-images CDN URL')
    print('4. Verify the URL is accessible')
    print('='*60)
    print('\n⚠️  You will need to log in to GitHub if not already authenticated.')
    print('⚠️  DO NOT submit the issue - just close the browser when done.\n')

    input('Press Enter to continue...')

    url = await upload_video_via_issue(video_path, repo_url, session_file)

    if url:
        print(f'\n✅ Successfully obtained user-images URL: {url}')
    else:
        print('\n❌ Failed to obtain user-images URL')


if __name__ == "__main__":
    asyncio.run(main())
