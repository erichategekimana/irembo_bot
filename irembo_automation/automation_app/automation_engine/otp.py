# automation_app/automation_engine/otp.py
import re
import time
import os

class OTPMixin:
    def enter_cooperative_interrupt_state(self):
        self.update_database_state("AWAITING_OTP")
        self.trigger_windows_alerts()

        while True:
            if self.booking_record:
                self.booking_record.refresh_from_db()
                if self.booking_record.status == "OTP_PROVIDED":
                    break
                if self.booking_record.status == "CANCELLED":
                    raise InterruptedError("Operation canceled via Agent Panel.")
            else:
                time.sleep(15)
                break
            time.sleep(1.0)

    def resume_and_finalize_booking(self, phone_number):
        print(f"[Step 10] Resuming flow validation for phone targets: {phone_number}")
        phone_checkbox = self.page.locator('mat-checkbox:has-text("Nomero ya telefoni (Rwanda)")')
        if not phone_checkbox.locator('input').is_checked():
            phone_checkbox.click()
            time.sleep(0.5)

        phone_input = self.page.locator('input[placeholder*="07"], input[type="tel"]').first
        phone_input.fill(phone_number)

        exact_form_terms = "Nemeje ko amakuru yose natanze ahangaha ari ukuri kandi ajyanye n'igihe."
        self.page.locator(f'mat-checkbox:has-text("{exact_form_terms}") .mat-checkbox-inner-container').click()
        time.sleep(0.5)

        self.page.locator('#submit_btn.btn-success:has-text("Emeza")').click()

        if self.booking_record and self.booking_record.otp_code:
            print(f"[Step 10] Injecting received operational verification OTP tokens: {self.booking_record.otp_code}")
            otp_input = self.page.locator('input[formcontrolname*="otp"], input[placeholder*="OTP"]').first
            try:
                self.page.wait_for_selector(otp_input, timeout=10000)
                otp_input.fill(self.booking_record.otp_code)
                self.page.locator('button:has-text("Emeza"), button:has-text("Genzura")').last.click()
            except Exception as e:
                print(f"[Step 10] Failed processing token entry fields layouts: {e}")

        try:
            billing_text_locator = self.page.locator('text="Kode yo kwishyuriraho", text="Kode you kwishyuriraho"')
            billing_text_locator.wait_for(timeout=15000)
            full_text = billing_text_locator.locator("xpath=..").inner_text()
            match = re.search(r'(88\d+)', full_text)

            if match and self.booking_record:
                billing_code = match.group(1)
                self.booking_record.billing_number = billing_code
                self.update_database_state("SUCCESS")
                self.capture_confirmation_receipt()
                return billing_code
            else:
                self.update_database_state("MANUAL_REVIEW_NEEDED")
                return None
        except Exception as e:
            print(f"[Step 10] Exception caught reading transaction values grids: {e}")
            self.update_database_state("FAILED")
            return None

    def capture_confirmation_receipt(self):
        try:
            self.page.wait_for_selector(".success-container, .billing-info-box", timeout=15000)
            national_id = self.booking_record.national_id if self.booking_record else "unknown_client"
            filename = f"receipt_{national_id}_{int(time.time())}.png"
            media_dir = os.path.abspath(os.path.join(os.getcwd(), "media", "receipts"))

            if not os.path.exists(media_dir):
                os.makedirs(media_dir)

            screenshot_path = os.path.join(media_dir, filename)
            self.page.screenshot(path=screenshot_path, full_page=True)
            return filename
        except Exception as e:
            print(f"[Warning] Visual data extraction tracking capture error: {e}")
            return None