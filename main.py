import json
import threading
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


# ============================================================
# VIBES ONLY
# V1 ENGINE CLIENT
# ============================================================

APP_NAME = "Vibes Only"
APP_VERSION = "13.0"

BASE_DIR = Path(__file__).resolve().parent
ASSETS = BASE_DIR / "assets"

# ------------------------------------------------------------
# V1 CONFIGURATION
# ------------------------------------------------------------

V1_CONFIG = BASE_DIR / "v1_config.json"

DEFAULT_V1_CONFIG = {
    "enabled": True,

    # Change this to your real V1 API endpoint.
    "endpoint": "http://10.0.2.2:8000/v1/chat",

    "timeout": 30,

    "engine": "V1",

    "fallback_enabled": True
}


def load_v1_config():
    """
    Loads V1 configuration from v1_config.json.
    Creates a default configuration if it does not exist.
    """

    try:
        if not V1_CONFIG.exists():
            V1_CONFIG.write_text(
                json.dumps(
                    DEFAULT_V1_CONFIG,
                    indent=4
                ),
                encoding="utf-8"
            )
            return DEFAULT_V1_CONFIG.copy()

        data = json.loads(
            V1_CONFIG.read_text(
                encoding="utf-8"
            )
        )

        config = DEFAULT_V1_CONFIG.copy()
        config.update(data)

        return config

    except Exception:
        return DEFAULT_V1_CONFIG.copy()


# ============================================================
# ASSETS
# ============================================================

BG_PATH = ASSETS / "background.png"
CHAT_BG_PATH = ASSETS / "chat_bg.png"
MENU_PATH = ASSETS / "menu.png"
OVERVIEW_PATH = ASSETS / "overview.png"
SEND_PATH = ASSETS / "send.png"


# ============================================================
# COLORS
# ============================================================

WHITE = (1, 1, 1, 1)
BLACK = (0, 0, 0, 1)
TRANSPARENT = (0, 0, 0, 0)
ACCENT = (0.55, 0.30, 1, 1)


# ============================================================
# V1 ENGINE
# ============================================================

class V1Engine:
    """
    Client responsible for communicating with Engine V1.

    Expected request:

    {
        "engine": "V1",
        "message": "Hello",
        "history": [...]
    }

    Expected response can contain one of:

    {
        "response": "Hello!"
    }

    or:

    {
        "reply": "Hello!"
    }

    or:

    {
        "message": "Hello!"
    }
    """

    def __init__(self):
        self.config = load_v1_config()

    def reload(self):
        self.config = load_v1_config()

    def ask(self, message, history=None):
        if not self.config.get("enabled", True):
            raise RuntimeError("V1 engine is disabled.")

        endpoint = str(
            self.config.get(
                "endpoint",
                ""
            )
        ).strip()

        if not endpoint:
            raise RuntimeError(
                "V1 endpoint is not configured."
            )

        payload = {
            "engine": "V1",
            "message": message,
            "history": history or []
        }

        body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            method="POST"
        )

        timeout = int(
            self.config.get(
                "timeout",
                30
            )
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout
            ) as response:

                raw = response.read().decode(
                    "utf-8"
                )

                data = json.loads(raw)

                return self.extract_response(data)

        except urllib.error.HTTPError as error:

            try:
                details = error.read().decode(
                    "utf-8"
                )
            except Exception:
                details = str(error)

            raise RuntimeError(
                f"V1 HTTP {error.code}: {details}"
            )

        except urllib.error.URLError as error:

            raise RuntimeError(
                f"Could not connect to V1: {error.reason}"
            )

        except TimeoutError:

            raise RuntimeError(
                "V1 request timed out."
            )

        except json.JSONDecodeError:

            raise RuntimeError(
                "V1 returned invalid JSON."
            )

    @staticmethod
    def extract_response(data):
        if isinstance(data, str):
            return data

        if not isinstance(data, dict):
            return str(data)

        for key in (
            "response",
            "reply",
            "message",
            "text",
            "content"
        ):

            value = data.get(key)

            if isinstance(value, str):
                return value

        # Support OpenAI-style response structures.
        try:
            choices = data.get("choices")

            if choices:

                first = choices[0]

                if isinstance(first, dict):

                    message = first.get(
                        "message"
                    )

                    if isinstance(message, dict):

                        content = message.get(
                            "content"
                        )

                        if isinstance(
                            content,
                            str
                        ):
                            return content

                    text = first.get("text")

                    if isinstance(text, str):
                        return text

        except Exception:
            pass

        return json.dumps(
            data,
            indent=2
        )


# ============================================================
# ICON BUTTON
# ============================================================

class IconButton(Button):

    def __init__(
        self,
        icon_path=None,
        fallback_text="",
        **kwargs
    ):

        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.background_color = TRANSPARENT
        self.border = (0, 0, 0, 0)

        self.text = fallback_text
        self.font_size = dp(22)

        if icon_path and icon_path.exists():

            self.text = ""

            icon = Image(
                source=str(icon_path),
                size_hint=(0.55, 0.55),
                pos_hint={
                    "center_x": 0.5,
                    "center_y": 0.5
                },
                allow_stretch=True,
                keep_ratio=True
            )

            self.add_widget(icon)


# ============================================================
# CHAT MESSAGE
# ============================================================

class ChatMessage(BoxLayout):

    def __init__(
        self,
        message,
        sender="ai",
        **kwargs
    ):

        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [
            dp(12),
            dp(8)
        ]
        self.spacing = dp(3)

        self.bind(
            minimum_height=self.setter(
                "height"
            )
        )

        sender_label = Label(
            text=(
                "You"
                if sender == "user"
                else "V1"
            ),
            size_hint_y=None,
            height=dp(20),
            color=(0.75, 0.75, 0.8, 1),
            font_size=dp(11),
            halign="left",
            valign="middle"
        )

        sender_label.bind(
            size=lambda obj, value:
            setattr(
                obj,
                "text_size",
                value
            )
        )

        message_label = Label(
            text=str(message),
            size_hint_y=None,
            color=WHITE,
            font_size=dp(15),
            halign="left",
            valign="top",
            padding=[
                dp(12),
                dp(10)
            ]
        )

        message_label.text_size = (
            Window.width * 0.72,
            None
        )

        message_label.bind(
            texture_size=lambda obj, value:
            setattr(
                obj,
                "height",
                value[1] + dp(20)
            )
        )

        time_label = Label(
            text=datetime.now().strftime(
                "%H:%M"
            ),
            size_hint_y=None,
            height=dp(17),
            color=(0.55, 0.55, 0.6, 1),
            font_size=dp(9),
            halign="right"
        )

        time_label.bind(
            size=lambda obj, value:
            setattr(
                obj,
                "text_size",
                value
            )
        )

        self.add_widget(sender_label)
        self.add_widget(message_label)
        self.add_widget(time_label)


# ============================================================
# MAIN APPLICATION
# ============================================================

class VibesApp(App):

    def build(self):

        self.title = APP_NAME

        Window.clearcolor = BLACK

        self.v1 = V1Engine()

        self.history = []

        self.is_waiting = False

        self.root_layout = FloatLayout()

        # ----------------------------------------------------
        # BACKGROUND
        # ----------------------------------------------------

        if BG_PATH.exists():

            self.root_layout.add_widget(
                Image(
                    source=str(BG_PATH),
                    size_hint=(1, 1),
                    allow_stretch=True,
                    keep_ratio=False
                )
            )

        # ----------------------------------------------------
        # TOP BAR
        # ----------------------------------------------------

        self.top_bar = FloatLayout(
            size_hint=(1, 0.09),
            pos_hint={
                "x": 0,
                "top": 1
            }
        )

        self.menu_button = IconButton(
            MENU_PATH,
            "☰",
            size_hint=(0.16, 1),
            pos_hint={
                "x": 0,
                "y": 0
            }
        )

        self.menu_button.bind(
            on_release=self.open_menu
        )

        self.top_bar.add_widget(
            self.menu_button
        )

        title = Label(
            text="Vibes Only • V1",
            size_hint=(0.60, 1),
            pos_hint={
                "center_x": 0.5,
                "y": 0
            },
            color=WHITE,
            font_size=dp(19),
            bold=True,
            halign="center",
            valign="middle"
        )

        title.bind(
            size=lambda obj, value:
            setattr(
                obj,
                "text_size",
                value
            )
        )

        self.top_bar.add_widget(title)

        self.overview_button = IconButton(
            OVERVIEW_PATH,
            "⋮",
            size_hint=(0.16, 1),
            pos_hint={
                "right": 1,
                "y": 0
            }
        )

        self.overview_button.bind(
            on_release=self.open_overview
        )

        self.top_bar.add_widget(
            self.overview_button
        )

        self.root_layout.add_widget(
            self.top_bar
        )

        # ----------------------------------------------------
        # CHAT
        # ----------------------------------------------------

        self.chat_scroll = ScrollView(
            size_hint=(0.96, 0.77),
            pos_hint={
                "center_x": 0.5,
                "top": 0.89
            },
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(3)
        )

        self.chat_messages = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[
                dp(8),
                dp(10),
                dp(8),
                dp(20)
            ],
            size_hint_y=None
        )

        self.chat_messages.bind(
            minimum_height=self.chat_messages.setter(
                "height"
            )
        )

        self.chat_scroll.add_widget(
            self.chat_messages
        )

        self.root_layout.add_widget(
            self.chat_scroll
        )

        # ----------------------------------------------------
        # INPUT AREA
        # ----------------------------------------------------

        self.chat_wrap = FloatLayout(
            size_hint=(0.94, 0.10),
            pos_hint={
                "center_x": 0.5,
                "y": 0.015
            }
        )

        if CHAT_BG_PATH.exists():

            self.chat_wrap.add_widget(
                Image(
                    source=str(CHAT_BG_PATH),
                    size_hint=(1, 1),
                    allow_stretch=True,
                    keep_ratio=False
                )
            )

        self.input_layout = BoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            padding=[
                dp(10),
                dp(8),
                dp(8),
                dp(8)
            ],
            size_hint=(1, 1)
        )

        self.message_input = TextInput(
            hint_text="Message V1...",
            multiline=False,
            background_normal="",
            background_active="",
            background_color=TRANSPARENT,
            foreground_color=WHITE,
            hint_text_color=(0.65, 0.65, 0.7, 1),
            cursor_color=ACCENT,
            font_size=dp(15),
            padding=[
                dp(8),
                dp(8),
                dp(8),
                dp(8)
            ],
            size_hint_x=0.82
        )

        self.message_input.bind(
            on_text_validate=self.send_message
        )

        self.send_button = IconButton(
            SEND_PATH,
            "➤",
            size_hint_x=0.18
        )

        self.send_button.bind(
            on_release=self.send_message
        )

        self.input_layout.add_widget(
            self.message_input
        )

        self.input_layout.add_widget(
            self.send_button
        )

        self.chat_wrap.add_widget(
            self.input_layout
        )

        self.root_layout.add_widget(
            self.chat_wrap
        )

        # ----------------------------------------------------
        # WELCOME
        # ----------------------------------------------------

        Clock.schedule_once(
            lambda dt: self.add_message(
                "Yo 👋 Welcome to Vibes Only.\n"
                "V1 engine is ready.",
                "ai"
            ),
            0.3
        )

        return self.root_layout

    # ========================================================
    # SEND
    # ========================================================

    def send_message(self, instance=None):

        if self.is_waiting:
            return

        message = (
            self.message_input.text.strip()
        )

        if not message:
            return

        self.message_input.text = ""

        self.add_message(
            message,
            "user"
        )

        self.history.append({
            "role": "user",
            "content": message
        })

        self.is_waiting = True

        self.send_button.disabled = True

        self.add_message(
            "V1 is thinking...",
            "ai"
        )

        threading.Thread(
            target=self._call_v1,
            args=(message,),
            daemon=True
        ).start()

    # ========================================================
    # CALL V1 IN BACKGROUND THREAD
    # ========================================================

    def _call_v1(self, message):

        try:

            response = self.v1.ask(
                message,
                self.history
            )

            success = True

        except Exception as error:

            response = (
                "V1 connection error:\n\n"
                f"{error}"
            )

            success = False

        Clock.schedule_once(
            lambda dt:
            self._finish_v1_response(
                response,
                success
            ),
            0
        )

    # ========================================================
    # FINISH V1 RESPONSE
    # ========================================================

    def _finish_v1_response(
        self,
        response,
        success
    ):

        # Remove "V1 is thinking..."
        if self.chat_messages.children:

            thinking = (
                self.chat_messages.children[0]
            )

            try:

                if (
                    isinstance(
                        thinking,
                        ChatMessage
                    )
                    and len(
                        thinking.children
                    ) >= 2
                ):

                    label = thinking.children[1]

                    if (
                        hasattr(
                            label,
                            "text"
                        )
                        and label.text
                        == "V1 is thinking..."
                    ):

                        self.chat_messages.remove_widget(
                            thinking
                        )

            except Exception:
                pass

        self.add_message(
            response,
            "ai"
        )

        self.history.append({
            "role": "assistant",
            "content": response
        })

        self.is_waiting = False

        self.send_button.disabled = False

        self.message_input.focus = True

    # ========================================================
    # ADD MESSAGE
    # ========================================================

    def add_message(
        self,
        message,
        sender="ai"
    ):

        bubble = ChatMessage(
            message,
            sender
        )

        self.chat_messages.add_widget(
            bubble
        )

        Clock.schedule_once(
            self.scroll_to_bottom,
            0.08
        )

    # ========================================================
    # SCROLL
    # ========================================================

    def scroll_to_bottom(self, dt=None):

        self.chat_scroll.scroll_y = 0

    # ========================================================
    # NEW CHAT
    # ========================================================

    def new_chat(self):

        self.chat_messages.clear_widgets()

        self.history.clear()

        self.add_message(
            "New conversation started.\n"
            "V1 is ready.",
            "ai"
        )

    # ========================================================
    # MENU
    # ========================================================

    def open_menu(self, instance):

        self.add_message(
            "☰ Vibes Only Menu\n\n"
            "• New conversation\n"
            "• V1 engine status\n"
            "• App information",
            "ai"
        )

    # ========================================================
    # OVERVIEW
    # ========================================================

    def open_overview(self, instance):

        self.v1.reload()

        endpoint = self.v1.config.get(
            "endpoint",
            "Not configured"
        )

        self.add_message(
            f"Vibes Only v{APP_VERSION}\n\n"
            "Engine: V1\n"
            f"Endpoint: {endpoint}\n"
            f"Messages: {len(self.history)}",
            "ai"
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    VibesApp().run()