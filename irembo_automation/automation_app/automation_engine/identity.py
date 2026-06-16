# automation_app/automation_engine/identity.py
import time

class IdentityMixin:
    def handle_identity_verification(self, national_id, client_verification_data):
        print(f"[Step 8] Injecting National ID: {national_id}")
        id_field = self.page.locator('input[formcontrolname="nationalIdFormControl"]')
        id_field.fill(national_id)
        id_field.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
        id_field.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))")
        id_field.press("Tab")
        time.sleep(0.5)

        print("[Step 8] Monitoring for the security validation modal container...")
        try:
            self.page.wait_for_selector("mat-dialog-container app-officer-action", timeout=12000)
        except Exception:
            self._pause_on_error("Identity verification modal did not appear. National ID may be invalid or session expired.")
        time.sleep(1)

        name_input = self.page.locator('input[formcontrolname="nameFormControl"]')
        date_input = self.page.locator('input[id="datePicker"]')

        print("[Step 8] Waiting for verification challenge fields to render...")
        challenge_detected = False
        start_time = time.time()
        while time.time() - start_time < 6.0:
            if name_input.is_visible() or date_input.is_visible():
                challenge_detected = True
                break
            time.sleep(0.3)

        if not challenge_detected:
            self._pause_on_error(
                "Verification challenge fields (name or birth date) did not appear inside the modal. "
                "The modal may have changed structure or an unexpected error was shown."
            )

        first_name = (
            self.booking_record.first_name
            if (self.booking_record and self.booking_record.first_name)
            else client_verification_data
        )
        if self.booking_record and self.booking_record.birth_date:
            birth_date_str = self.booking_record.birth_date.strftime("%d/%m/%Y")
        else:
            birth_date_str = client_verification_data

        if name_input.is_visible():
            print(f"[Step 8] Challenge: Name requested. Typing: {first_name}")
            self._type_into_field(name_input, first_name)
        elif date_input.is_visible():
            print(f"[Step 8] Challenge: Birth date requested. Typing: {birth_date_str}")
            self._type_into_field(date_input, birth_date_str)

        time.sleep(0.5)

        print("[Step 8] Verifying terms checkbox state...")
        checkbox = self.page.locator('mat-checkbox:has-text("Nemeye") ')
        checkbox_inner = checkbox.locator('.mat-checkbox-inner-container')
        try:
            is_checked = "mat-checkbox-checked" in (checkbox.get_attribute("class") or "")
            if not is_checked:
                print("[Step 8] Terms checkbox is unchecked. Clicking to accept...")
                checkbox_inner.click()
                time.sleep(0.5)
            else:
                print("[Step 8] Terms checkbox already checked. Skipping click.")
        except Exception as e:
            print(f"[Step 8] Warning: Could not determine checkbox state ({e}). Attempting click anyway...")
            checkbox_inner.click()
            time.sleep(0.5)

        print("[Step 8] Locating 'Genzura' confirmation button...")
        review_btn = self.page.locator('mat-dialog-container button.btn-primary')

        try:
            review_btn.wait_for(state="visible", timeout=4000)
        except Exception:
            self.check_for_errors()
            self._pause_on_error("'Genzura' button was not found in the modal. The page structure may have changed.")

        print("[Step 8] Waiting for 'Genzura' button to become enabled...")
        btn_enabled = False
        start_time = time.time()
        while time.time() - start_time < 5.0:
            if not review_btn.is_disabled():
                btn_enabled = True
                break
            time.sleep(0.3)

        if not btn_enabled:
            self.check_for_errors()
            self._pause_on_error(
                "Verification button ('Genzura') remained disabled after 5s. "
                "Check that first_name or birth_date in the database record exactly matches the ID document."
            )

        print("[Step 8] Submitting identity verification ('Genzura')...")
        review_btn.click()

        try:
            self.page.wait_for_selector("mat-dialog-container", state="detached", timeout=10000)
            print("[Step 8] Identity verification completed successfully.")
        except Exception:
            self.check_for_errors()
            self._pause_on_error(
                "Identity verification modal did not close after clicking 'Genzura'. "
                "Credentials may be incorrect or the portal returned an error."
            )