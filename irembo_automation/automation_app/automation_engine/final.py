# automation_app/automation_engine/final.py
import re
import time
import os
from .utils import run_in_db_thread   # thread-safe ORM dispatch


class FinalizationMixin:
    """
    Handles everything that happens after a slot is secured:
      1. Fill in the phone number
      2. Confirm the "info is legit" terms checkbox
      3. Submit the application
      4. Collect the billing number from the confirmation page
      5. Save it to the DB, mark SUCCESS, play the alert sound, take a screenshot
    No OTP step is involved.
    """

    def finalize_booking(self, phone_number):
        """
        Complete the application after the slot has been locked.
        Called immediately after evaluate_and_select_slot() returns True.
        """
        print(f"[Final] Starting finalization for phone: {phone_number}")

        # ── Step 1: Select phone number notification channel ─────────────────
        try:
            phone_checkbox = self.page.locator('mat-checkbox:has-text("Nomero ya telefoni (Rwanda)")')
            phone_checkbox.wait_for(state="visible", timeout=8000)
            if not phone_checkbox.locator('input').is_checked():
                phone_checkbox.click()
                time.sleep(0.4)
        except Exception as e:
            print(f"[Final] Phone channel checkbox not found or already selected: {e}")

        # ── Step 2: Fill in the phone number ─────────────────────────────────
        try:
            phone_input = self.page.locator(
                'input[placeholder*="07"], input[type="tel"], input[formcontrolname*="phone"]'
            ).first
            phone_input.wait_for(state="visible", timeout=8000)
            phone_input.fill(phone_number)
            time.sleep(0.3)
            print(f"[Final] Phone number entered: {phone_number}")
        except Exception as e:
            print(f"[Final] Could not fill phone number field: {e}")

        # ── Step 3: Accept the "info is correct" terms checkbox ───────────────
        exact_terms = "Nemeje ko amakuru yose natanze ahangaha ari ukuri kandi ajyanye n'igihe."
        try:
            terms_box = self.page.locator(
                f'mat-checkbox:has-text("{exact_terms}") .mat-checkbox-inner-container'
            )
            terms_box.wait_for(state="visible", timeout=8000)
            terms_box.click()
            time.sleep(0.4)
            print("[Final] Terms checkbox accepted.")
        except Exception as e:
            # Fallback — try any unchecked checkbox near the bottom of the form
            print(f"[Final] Terms checkbox primary locator failed ({e}). Trying fallback...")
            try:
                fallback = self.page.locator('mat-checkbox input[type="checkbox"]').last
                if not fallback.is_checked():
                    fallback.check()
                    time.sleep(0.4)
            except Exception as fe:
                print(f"[Final] Fallback checkbox also failed: {fe}")

        # ── Step 4: Submit the application ────────────────────────────────────
        try:
            # Use the ID-based selector – it's unique and reliable
            submit_btn = self.page.locator('#submit_btn')
            submit_btn.wait_for(state="visible", timeout=10000)
            # Wait for it to become enabled (not disabled)
            start = time.time()
            while time.time() - start < 10:
                if not submit_btn.is_disabled():
                    break
                time.sleep(0.3)
            else:
                raise Exception("Submit button remained disabled after 10 seconds.")
            submit_btn.click()
            print("[Final] Application submitted. Waiting for confirmation page...")
        except Exception as e:
            print(f"[Final] Submit button error: {e}")
            self.update_database_state("FAILED")
            return None

                # ── Step 5: Collect billing number ──────────────────────────
        # First, wait for any element that contains the billing label or a number starting with 88
        billing_code = None
        try:
            # Wait for the confirmation container to appear
            self.page.wait_for_selector(".success-container, .billing-info-box, .confirmation-page, .alert-success", timeout=20000)
            # Now try to locate the billing code
            # Option 1: look for the label and extract the number from its parent
            label_selectors = [
                'text="Kode yo kwishyuriraho"',
                'text="Kode you kwishyuriraho"',
                ':has-text("Kode yo kwishyuriraho")',
                ':has-text("Kode you kwishyuriraho")'
            ]
            found = False
            for sel in label_selectors:
                try:
                    label = self.page.locator(sel).first
                    if label.is_visible():
                        # Get the parent element and extract text
                        parent = label.locator("xpath=..")
                        full_text = parent.inner_text()
                        match = re.search(r'(88\d+)', full_text)
                        if match:
                            billing_code = match.group(1)
                            found = True
                            break
                except:
                    continue
            if not found:
                # Fallback: search the entire page for the pattern
                body_text = self.page.locator("body").inner_text()
                matches = re.findall(r'(88\d+)', body_text)
                if matches:
                    billing_code = matches[0]  # take the first
        except Exception as e:
            print(f"[Final] Billing code extraction error: {e}")

        if billing_code:
            print(f"[Final] Billing code captured: {billing_code}")
            record = self.booking_record
            if record:
                def _save_billing():
                    record.billing_number = billing_code
                    record.save(update_fields=["billing_number"])
                run_in_db_thread(_save_billing)

            self.update_database_state("SUCCESS")

            # ── Step 6: Alert sound + screenshot ──────────────────
            self.trigger_windows_alerts()
            self.capture_confirmation_receipt()

            # ── Step 7: Keep browser open for 5 minutes ──────────
            print("[Final] Booking completed. Browser will stay open for 5 minutes before closing.")
            time.sleep(300)  # 5 minutes

            return billing_code
        else:
            print("[Final] Billing code not found.")
            self.update_database_state("MANUAL_REVIEW_NEEDED")
            return None

    def capture_confirmation_receipt(self):
        """Screenshot the confirmation page."""
        try:
            self.page.wait_for_selector(
                ".success-container, .billing-info-box, .confirmation-page",
                timeout=10000,
            )
            national_id = self.booking_record.national_id if self.booking_record else "unknown_client"
            filename = f"receipt_{national_id}_{int(time.time())}.png"
            media_dir = os.path.abspath(os.path.join(os.getcwd(), "media", "receipts"))

            if not os.path.exists(media_dir):
                os.makedirs(media_dir)

            screenshot_path = os.path.join(media_dir, filename)
            self.page.screenshot(path=screenshot_path, full_page=True)
            print(f"[Final] Receipt saved: {screenshot_path}")
            return filename
        except Exception as e:
            print(f"[Final] Screenshot capture failed: {e}")
            return None