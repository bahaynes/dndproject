from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto("http://localhost:5173/dashboard", timeout=60000)
            # Expect a redirect to the login page
            expect(page).to_have_url("http://localhost:5173/login", timeout=10000)
            page.screenshot(path="jules-scratch/verification_routes/dashboard_redirect.png")
            print("Dashboard correctly redirected to login.")
        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path="jules-scratch/verification_routes/dashboard_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()
