# automation_app/automation_engine/utils.py
import sys
import time

class UtilsMixin:
    def _pause_on_error(self, reason):
        print(f"[Engine PAUSED] {reason}")
        if self.booking_record:
            self.booking_record.application_number = f"[ERROR] {reason}"
            self.update_database_state("FAILED")
        raise ValueError(reason)

    def update_database_state(self, new_status):
        if self.booking_record:
            self.booking_record.status = new_status
            self.booking_record.save()

    def trigger_windows_alerts(self):
        if sys.platform == "win32":
            import winsound
            for _ in range(3):
                winsound.Beep(2500, 800)
                time.sleep(0.2)
        else:
            print("\a[Linux System Notification Alert] Target locked successfully.")

    def run_health_check(self):
        try:
            self.page.goto("https://irembo.gov.rw/", wait_until="networkidle")
            time.sleep(2)
            return self.page.locator("text=Sign Out").is_visible() or "dashboard" in self.page.url.lower()
        except Exception:
            return False

    def close(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()