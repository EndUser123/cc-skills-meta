#!/usr/bin/env python
"""
Simple upload script - runs without prompts.
"""

import asyncio
import re
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright


async def main():
    repo_url = "https://github.com/EndUser123/gitready"
    video_path = Path("P:/packages/gitready/assets/videos/github-ready_explainer_video.mp4")
    session_file = Path.home() / ".github_video_uploader_session.json"

    print('🚀 Starting upload...')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state=str(session_file) if session_file.exists() else None,
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        try:
            issue_url = f"{repo_url}/issues/new"
            print(f'📍 Navigating to: {issue_url}')
            await page.goto(issue_url, wait_until='domcontentloaded', timeout=30000)

            # Handle authentication if needed
            if 'login' in page.url:
                print('🔐 Authentication required - please log in')
                await page.wait_for_url('**/issues/new', timeout=180000)
                await context.storage_state(path=str(session_file))
                print('✅ Logged in, session saved')

            # Wait and fill title
            await asyncio.sleep(3)
            print('📝 Filling issue title...')

            # Try multiple approaches to fill title
            title_filled = False
            selectors = ['input[name="issue[title]"]', '#issue_title', 'input[aria-label*="title"]', 'input[id*="title"]']

            for selector in selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.fill(selector, 'Video upload for README')
                        title_filled = True
                        print('✅ Title filled')
                        break
                except:
                    continue

            # Upload video
            print(f'📤 Uploading {video_path.name}...')
            file_input = page.locator('input[type="file"]').first
            await file_input.set_input_files(str(video_path))
            print('⏳ Waiting for GitHub to process upload...')

            # Wait for upload to complete
            await asyncio.sleep(20)

            # Look for user-images URL in various places
            user_images_url = None

            # Method 1: Check textarea
            textarea_selectors = ['textarea[name="issue[body]"]', '#issue_body', 'textarea[aria-label*="body"]']
            for selector in textarea_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        content = await page.locator(selector).input_value()
                        match = re.search(r'https://user-images\.githubusercontent\.com/[^\s\)\"]*\.mp4', content)
                        if match:
                            user_images_url = match.group(0)
                            print('✅ Found URL in textarea')
                            break
                except:
                    continue

            # Method 2: Check page source
            if not user_images_url:
                page_source = await page.content()
                match = re.search(r'https://user-images\.githubusercontent\.com/[^\s\)\"]*\.mp4', page_source)
                if match:
                    user_images_url = match.group(0)
                    print('✅ Found URL in page source')

            if user_images_url:
                # Verify URL works
                print(f'🔍 Verifying URL: {user_images_url}')
                result = subprocess.run(['curl', '-I', user_images_url], capture_output=True, text=True, timeout=10)

                if '200' in result.stdout or '206' in result.stdout:
                    print('\n' + '='*70)
                    print('✅ SUCCESS! Video URL obtained:')
                    print('='*70)
                    print(user_images_url)
                    print('='*70)
                    print('\nUse this in README.md:')
                    print(f'<video src="{user_images_url}" controls style="max-width: 730px;">')
                    print('</video>')
                    print('\n⚠️  Close browser WITHOUT submitting issue')
                    print('Waiting 30 seconds before closing...')
                    await asyncio.sleep(30)
                else:
                    print(f'❌ URL not accessible: {result.stdout[:200]}')
            else:
                print('❌ Could not find video URL')
                print('Check if video appeared in issue body and copy URL manually')
                print('Waiting 60 seconds...')
                await asyncio.sleep(60)

        except Exception as e:
            print(f'❌ Error: {e}')
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
