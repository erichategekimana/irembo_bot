# automation_app/automation_engine/navigation.py
import time

class NavigationMixin:
    def navigate_to_booking_form(self, national_id, verification_data):
        print(f"[Engine] Navigating to Irembo home page...")
        self.page.goto("https://irembo.gov.rw/", wait_until="networkidle")

        self.page.locator('text="Polisi"').click()
        time.sleep(1)

        print("[Engine] Selecting driving registration menu entry layout links...")
        self.page.locator('text="Kwiyandikisha gukora ikizamini cyo gutwara ibinyabiziga"').first.click()
        self.page.wait_for_selector("mat-dialog-container", timeout=10000)

        if self.booking_record and self.booking_record.provisional_number:
            print("[Engine Split] Detected Provisional ID. Configuring Definitive License (BURANDU) application.")
            target_service = "Kwiyandikisha gukora ikizamini cy'uruhushya rwa burundu rwo gutwara ikinyabiziga"
        else:
            print("[Engine Split] No Provisional ID found. Configuring Category Upgrade (UPGRADE) application.")
            target_service = "Kwiyandikisha gukora ikizamini cy'uruhushya rw'icyiciro kisumbuye"

        self.page.locator("mat-dialog-container ng-select").click()
        self.page.locator(f'.ng-dropdown-panel .ng-option:has-text("{target_service}")').click()
        time.sleep(0.5)

        self.page.locator('mat-dialog-container button:has-text("Saba")').click()
        self.page.wait_for_load_state("networkidle")

        self.handle_identity_verification(national_id, verification_data)

        if self.booking_record and self.booking_record.provisional_number:
            print(f"[Engine] Filling Provisional License ID: {self.booking_record.provisional_number}")
            prov_field = self.page.locator('input[formcontrolname="provisionalLicenseNumberFormControl"]')
            prov_field.wait_for(state="visible", timeout=10000)
            prov_field.fill(self.booking_record.provisional_number)
            prov_field.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
            prov_field.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))")
            time.sleep(0.5)

            print("[Engine] Submitting provisional license details...")
            prov_field.press("Enter")
            time.sleep(0.5)

            search_btn = self.page.locator(
                'input[formcontrolname="provisionalLicenseNumberFormControl"] ~ button, '
                'button.inline-btn, button.x-small-button, '
                'button:has-text("Shakisha"), form.ng-valid button.btn-primary, button.btn-primary'
            ).first
            try:
                search_btn.wait_for(state="visible", timeout=3000)
                print("[Engine] Clicking search/submit button...")
                search_btn.click()
            except Exception as e:
                print(f"[Engine] Search button not visible or not found after 3s ({e}). Continuing...")

            time.sleep(2)
            self.check_for_errors()