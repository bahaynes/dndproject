from playwright.sync_api import sync_playwright, expect
import time

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Use a unique username/email for each run to ensure registration is always new
        unique_id = int(time.time())
        test_username = f"testuser_{unique_id}"
        test_email = f"test_{unique_id}@example.com"
        test_password = "password123"

        try:
            # --- Registration ---
            print("Navigating to /register...")
            page.goto("http://localhost:5173/register", timeout=60000)

            print("Filling out registration form...")
            page.get_by_placeholder("Username").fill(test_username)
            page.get_by_placeholder("Email").fill(test_email)
            page.get_by_placeholder("Password").nth(0).fill(test_password)
            page.get_by_placeholder("Confirm Password").fill(test_password)

            print("Submitting registration form...")
            page.get_by_role("button", name="Register").click()

            # Wait for the success message and redirect
            expect(page.get_by_text("Registration successful!")).to_be_visible(timeout=10000)
            print("Registration successful.")

            # --- Login ---
            print("Navigating to /login (or waiting for redirect)...")
            # The page should redirect to /login, but we'll navigate just in case
            page.wait_for_url("**/login", timeout=10000)

            print("Filling out login form...")
            page.get_by_placeholder("Username").fill(test_username)
            page.get_by_placeholder("Password").fill(test_password)

            print("Submitting login form...")
            page.get_by_role("button", name="Login").click()

            # --- Dashboard Verification ---
            print("Verifying dashboard access...")
            # After login, user should be on the dashboard
            page.wait_for_url("**/dashboard", timeout=10000)

            # Check for a welcome message or a dashboard-specific element
            welcome_message = page.get_by_text(f"Welcome, {test_username}")
            # The welcome message is in the layout, so it might take a moment to update
            expect(welcome_message).to_be_visible(timeout=10000)

            print("Dashboard verification successful.")
            page.screenshot(path="jules-scratch/verification_part2/dashboard_after_login.png")
            print("Screenshot of dashboard taken successfully.")

        except Exception as e:
            print(f"An error occurred during auth flow verification: {e}")
            page.screenshot(path="jules-scratch/verification_part2/auth_flow_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()
