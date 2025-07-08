from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # headless=False to see the browser open
    page = browser.new_page()
    page.goto("https://razorpay.com/careers/", timeout=60000)

    page.wait_for_timeout(7000)  # wait for full JS rendering

    # Print entire rendered HTML
    content = page.content()
    print(content[:2000])  # print first 2000 characters of the rendered HTML

    browser.close()
