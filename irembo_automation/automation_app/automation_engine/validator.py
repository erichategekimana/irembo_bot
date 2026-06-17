# automation_app/automation_engine/validator.py
import time

class ValidatorMixin:
    def validate_agent_session(self, page):
        """
        Check if the current session is a logged-in agent with active 'Uhagarariye' role.
        Returns True if agent mode is active, False otherwise.
        Logs warnings but does not raise exceptions.
        """
        print("[Validator] Running session validation...")
        try:
            # Wait for the page to be loaded (assuming we are on the home page)
            # We expect to see a user dropdown or sign out link.
            # Look for sign-out link to confirm login.
            sign_out = page.locator('a.dropdown-item:has-text("Sohoka ku rubuga")')
            if not sign_out.is_visible():
                print("[Validator] WARNING: Not logged in or session expired. Please refresh session using record_session.py.")
                return False

            # Now check role: look for 'Uhagarariye' text in dropdown or role indicator.
            # The role might be displayed in the authority-top label or the role switch link.
            # If the current role is 'Umuturage', the label will show that.
            # If the agent has switched to agent mode, there might be a different label.
            # We'll look for an element that indicates agent mode.
            # For example, the dropdown item for agent role might have a specific class.
            # Or the label might change.
            # Simplest: check if any element contains "Uhagarariye" and is not hidden.
            # But that might be present in the switch link even if not active.
            # Better: check the current role label.
            # In the HTML, there is <label class="label-role">UMUTURAGE</label>.
            # That indicates the current role. We'll check if it says "UHAGARARIYE" or something.
            # If it says "UMUTURAGE", then not agent mode.
            role_label = page.locator('.label-role')
            if role_label.is_visible():
                role_text = role_label.inner_text().strip().upper()
                if role_text == "UHAGARARIYE" or role_text == "UHAGARARIYE":
                    print("[Validator] Agent mode is active (Uhagarariye).")
                    return True
                else:
                    print(f"[Validator] Current role is {role_text}. Not agent mode.")
                    # Optionally, we could try to switch to agent mode automatically.
                    # But we will not do that to avoid breaking.
                    return False
            else:
                # If label not found, fallback: check for presence of 'Uhagarariye' in the dropdown.
                # But that might indicate switch availability, not active.
                # So we'll just warn.
                print("[Validator] Could not determine role; assuming not agent.")
                return False

        except Exception as e:
            print(f"[Validator] Validation failed with error: {e}")
            return False