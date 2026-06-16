# automation_app/automation_engine/polling.py
import random
import time

class PollingMixin:
    def evaluate_and_select_slot(self, target_center="BUSANZA"):
        badge_element = self.page.locator('.appointments-header h2.title span.badge')
        if not badge_element.is_visible():
            return False

        available_slots_count = int(badge_element.inner_text().strip())
        if available_slots_count == 0:
            return False

        slots = self.page.locator(".appointments-list .appointment-slot").all()
        for slot in slots:
            center_details = slot.locator(".center").inner_text().upper()
            capacity_text = slot.locator(".capacity-circle").inner_text().strip()

            try:
                capacity = int(capacity_text)
            except ValueError:
                capacity = 0

            if target_center in center_details and capacity > 0:
                print(f"[Slot Match] Locking center location: {center_details} ({capacity} seats)")
                slot.click()
                time.sleep(0.5)

                if "selected" in slot.get_attribute("class") or slot.locator(".selected-text").is_visible():
                    self.page.locator("#next_btn").click()
                    return True
        return False

    def start_slot_polling(self, target_center="BUSANZA AUTOMATED CENTER"):
        print("[Engine] Polling engine activated. Monitoring availability maps...")

        if self.booking_record and self.booking_record.category:
            print(f"[Engine] Setting category selection to: {self.booking_record.category}")
            category_control = "categoryFormControl"
            if not self.page.locator(f'ng-select[formcontrolname="{category_control}"]').is_visible():
                category_control = "licenseCategoryFormControl"
            self.set_angular_dropdown(category_control, self.booking_record.category)
        else:
            print("[Warning] No target category specified in database record. Skipping initial category selection.")

        district_control = "locationFormControl"
        if not self.page.locator(f'ng-select[formcontrolname="{district_control}"]').is_visible():
            district_control = "districtFormControl"

        print(f"[Engine] Setting district selection (using control: {district_control}) to Kicukiro...")
        self.set_angular_dropdown(district_control, "Kicukiro")

        while True:
            try:
                slot_secured = self.evaluate_and_select_slot(target_center=target_center)

                if slot_secured:
                    print(f"[Engine] Slot secured at {target_center}! Transitioning to OTP stage...")
                    self.enter_cooperative_interrupt_state()
                    client_phone = self.booking_record.phone_number if self.booking_record else "0780000000"
                    billing_id = self.resume_and_finalize_booking(phone_number=client_phone)
                    return billing_id

                poll_delay = random.uniform(4.0, 7.5)
                print(f"[Engine] No slot found at {target_center}. Waiting {poll_delay:.2f}s before toggling district to refresh...")
                time.sleep(poll_delay)

                print(f"[Engine] Toggling district (using control: {district_control}) to refresh slots...")
                self.set_angular_dropdown(district_control, "Gasabo")
                time.sleep(random.uniform(1.2, 2.5))
                self.set_angular_dropdown(district_control, "Kicukiro")
                time.sleep(random.uniform(1.2, 2.5))

            except InterruptedError as ie:
                print(f"[Engine] Shutting down polling gracefully: {ie}")
                break
            except Exception as e:
                print(f"[Engine] Exception occurrence inside checking loop: {str(e)}")
                time.sleep(5)