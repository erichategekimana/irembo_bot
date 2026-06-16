# automation_app/automation_engine/browser.py
import os
from playwright.sync_api import sync_playwright  # type: ignore[import]
from playwright_stealth import Stealth  # type: ignore[import]
from .config import (
    STATE_FILE_PATH,
    DEFAULT_USER_AGENT,
    DEFAULT_VIEWPORT,
    DEFAULT_DEVICE_SCALE_FACTOR,
    DEFAULT_IS_MOBILE,
    DEFAULT_HAS_TOUCH,
    DEFAULT_LOCALE,
    DEFAULT_TIMEZONE,
)

class BrowserMixin:
    def initialize_stealth_browser(self, p, headless=True):
        self.browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context_params = {
            "user_agent": DEFAULT_USER_AGENT,
            "viewport": DEFAULT_VIEWPORT,
            "device_scale_factor": DEFAULT_DEVICE_SCALE_FACTOR,
            "is_mobile": DEFAULT_IS_MOBILE,
            "has_touch": DEFAULT_HAS_TOUCH,
            "locale": DEFAULT_LOCALE,
            "timezone_id": DEFAULT_TIMEZONE
        }

        if os.path.exists(self.state_file):
            print("[Engine] Found existing state.json. Rehydrating active session tokens...")
            context_params["storage_state"] = self.state_file
        else:
            print("[Engine] WARNING: state.json not found! Running with a clean context.")

        self.context = self.browser.new_context(**context_params)
        Stealth().apply_stealth_sync(self.context)

        self.context.add_init_script("""
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
        """)

        self.page = self.context.new_page()
        self.context.route("**/*", lambda route: self._intercept_resources(route))