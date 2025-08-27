from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Go to the homepage
            page.goto("http://localhost:5173", timeout=60000)

            # 2. Check for the main heading to ensure the page loaded
            heading = page.get_by_role("heading", name="Welcome to the DnD Westmarches Hub")
            expect(heading).to_be_visible()

            # 3. Check that the "Login" button is visible (since we are not logged in)
            # Be specific to avoid strict mode violation
            main_content = page.get_by_role("main")
            login_button = main_content.get_by_role("link", name="Login")
            expect(login_button).to_be_visible()

            # 4. Take a screenshot
            page.screenshot(path="jules-scratch/verification/verification.png")
            print("Screenshot taken successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path="jules-scratch/verification/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()
