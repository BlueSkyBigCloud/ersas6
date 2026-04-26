from celery import shared_task
from playwright.async_api import async_playwright
import asyncio
import os

@shared_task
def scheduled_login():
    async def run():
        USERNAME = os.environ.get("APP_USERNAME")
        PASSWORD = os.environ.get("APP_PASSWORD")

        if not USERNAME or not PASSWORD:
            print("Environment variables missing. Check .env")
            return

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto("https://tradesec.us/accounts/login/")
            await page.fill('input[name="login"]', USERNAME)
            await page.fill('input[name="password"]', PASSWORD)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle")

            print("Login successful.")

            await browser.close()

    asyncio.run(run())