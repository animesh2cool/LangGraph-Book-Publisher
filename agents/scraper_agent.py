from playwright.async_api import async_playwright
import asyncio

class ScraperAgent:
    def __init__(self, url: str):
        self.url = url

    async def scrape(self) -> dict:
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