from playwright.async_api import async_playwright
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

class ScraperAgent:
    def __init__(self, url: str):
        self.url = url
    
    async def _scrape_async(self) -> dict:
        os.makedirs("data/screenshots", exist_ok=True)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.url)
            content = await page.inner_text("body")
            screenshot_path = "data/screenshots/chapter1.png"
            await page.screenshot(path=screenshot_path)
            await browser.close()
        
        return {
            "text": content,
            "screenshot": screenshot_path
        }
    
    def scrape(self) -> dict:
        """Run async scraper in isolated thread to avoid event loop conflicts"""
        def run_in_thread():
            # Set Windows-specific event loop policy
            import sys
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._scrape_async())
            finally:
                loop.close()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_in_thread)
            return future.result()