"""
ZABACODE UI — Main Kivy Application & Root Widget
The heart of the v1.0.0 Kivy native edition.
"""

import threading
import time

from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.codeinput import CodeInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.stacklayout import StackLayout
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

from pygments.lexers import PythonLexer

from zabacode import __version__
from zabacode.core.paths import APP_DIR, FILES_DIR
from zabacode.core.security import AUTH_TOKEN, load_keys, save_key
from zabacode.core.executor import execute_code_isolated, normalize_code
from zabacode.core.checker import check_code
from zabacode.core.file_manager import list_files, read_file, save_file, delete_file, secure_filename
from zabacode.lib_manager import get_all_libraries, install_library, KNOWN_LIBRARIES
from zabacode.themes.definitions import THEMES, DEFAULT_THEME, get_theme, list_themes
from zabacode.i18n.translations import i18n, LANGUAGES, TRANSLATIONS
from zabacode.plugins.registry import (
    get_all_plugins, toggle_plugin, is_plugin_active, get_snippets, SNIPPET_TEMPLATES
)
from zabacode.core.ai_provider import PROVIDER_HANDLERS, PROVIDER_INFO, ALLOWED_PROVIDERS


# ---------------------------------------------------------------------------
# Helper: hex to Kivy RGBA
# ---------------------------------------------------------------------------

def hex_to_rgba(hex_color: str) -> tuple:
    """Convert hex color string to Kivy RGBA tuple (0.0-1.0)."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    a = int(hex_color[6:8], 16) / 255.0 if len(hex_color) >= 8 else 1.0
    return (r, g, b, a)


def rgba_to_hex(rgba: tuple) -> str:
    """Convert Kivy RGBA tuple to hex color string."""
    r, g, b, a = rgba
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


# ---------------------------------------------------------------------------
# Line Numbers Widget
# ---------------------------------------------------------------------------

class LineNumbersWidget(Label):
    """Displays line numbers alongside the code editor."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = sp(11)
        self.size_hint_x = None
        self.width = dp(40)
        self.halign = 'right'
        self.valign = 'top'
        self.padding = (dp(4), dp(10), dp(4), dp(0))
    
    def update_line_numbers(self, text: str):
        """Update line numbers based on editor content."""
        count = text.count('\n') + 1 if text else 1
        self.text = '\n'.join(str(i) for i in range(1, count + 1))


# ---------------------------------------------------------------------------
# Tab Data & Management
# ---------------------------------------------------------------------------

class TabData:
    """Represents a single editor tab."""
    _counter = 0
    
    def __init__(self, name: str = None, content: str = "", filepath: str = None):
        TabData._counter += 1
        self.id = TabData._counter
        self.name = name or f"untitled_{self.id}.py"
        self.content = content
        self.filepath = filepath
        self.modified = False


# ---------------------------------------------------------------------------
# Custom Widgets
# ---------------------------------------------------------------------------

class ThemedButton(Button):
    """A button that responds to theme changes."""
    
    def __init__(self, text="", bg_color=(0.18, 0.55, 0.31, 1), text_color=(0.22, 1.0, 0.078, 1),
                 font_size=sp(12), **kwargs):
        super().__init__(text=text, font_size=font_size, **kwargs)
        self.bg_color = bg_color
        self.color = text_color
        self.background_normal = ''
        self.background_color = bg_color
        self.border = (0, 0, 0, 0)
        self.size_hint_y = None
        self.height = dp(36)
    
    def apply_theme(self, theme: dict):
        self.background_color = theme.get('border_bright', self.bg_color)
        self.color = (0, 0, 0, 1) if sum(theme.get('border_bright', (0.5, 0.5, 0.5, 1))[:3]) > 1.5 else (1, 1, 1, 1)


class SymbolBarButton(Button):
    """Quick symbol insertion button for mobile typing."""
    
    def __init__(self, symbol: str, on_insert=None, **kwargs):
        super().__init__(text=symbol, font_size=sp(13), **kwargs)
        self.background_normal = ''
        self.background_color = (0.06, 0.09, 0.07, 1)
        self.color = (0.22, 1.0, 0.078, 1)
        self.size_hint_x = None
        self.width = dp(36)
        self.height = dp(32)
        self.border = (0, 0, 0, 0)
        self._on_insert = on_insert
        self.bind(on_release=self._on_release)
    
    def _on_release(self, instance):
        if self._on_insert:
            self._on_insert(self.text)


# ---------------------------------------------------------------------------
# Sidebar Panel
# ---------------------------------------------------------------------------

class SidebarPanel(BoxLayout):
    """Navigation sidebar with menu items."""
    
    def __init__(self, app_ref, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.app_ref = app_ref
        self.size_hint_x = None
        self.width = dp(250)
        self.pos_hint = {'top': 1}
        self.opacity = 0
        self.x = -self.width
        
        # Header
        header = Label(
            text=f"/// ZABACODE v{__version__}",
            font_size=sp(13),
            size_hint_y=None,
            height=dp(44),
            halign='left',
            valign='middle',
        )
        self.add_widget(header)
        
        # Menu buttons
        menu_items = [
            ("files", "📁"),
            ("save", "💾"),
            ("libraries", "📦"),
            ("ai_keys", "🔑"),
            ("themes", "🎨"),
            ("plugins", "🧩"),
            ("language", "🌐"),
            ("about", "ℹ️"),
        ]
        
        self.menu_buttons = {}
        for action, icon in menu_items:
            btn = Button(
                text=f"  {icon}  {action}",
                font_size=sp(13),
                size_hint_y=None,
                height=dp(40),
                halign='left',
                valign='middle',
                background_normal='',
                background_color=(0.04, 0.06, 0.05, 1),
                color=(0.72, 0.96, 0.77, 1),
                border=(0, 0, 0, 0),
            )
            btn.bind(on_release=lambda inst, a=action: self._on_menu(a))
            self.add_widget(btn)
            self.menu_buttons[action] = btn
    
    def _on_menu(self, action: str):
        self.app_ref.close_sidebar()
        Clock.schedule_once(lambda dt: self.app_ref.handle_sidebar_action(action), 0.15)
    
    def apply_theme(self, theme: dict):
        self.canvas.before.clear()
        # Update colors
        bg = theme.get('bg_panel', (0.04, 0.06, 0.05, 1))
        border = theme.get('border', (0.1, 0.3, 0.18, 1))
        text_c = theme.get('text', (0.72, 0.96, 0.77, 1))
        bright = theme.get('text_bright', (0.22, 1.0, 0.078, 1))
        btn_bg = theme.get('bg_panel_2', bg)
        
        for child in self.children:
            if isinstance(child, Label):
                child.color = bright
            elif isinstance(child, Button):
                child.background_color = btn_bg
                child.color = text_c


# ---------------------------------------------------------------------------
# AI Chat Panel
# ---------------------------------------------------------------------------

class AIChatPanel(BoxLayout):
    """AI assistant chat panel."""
    
    def __init__(self, app_ref, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.app_ref = app_ref
        self.size_hint_x = None
        self.width = dp(280)
        self.pos_hint = {'top': 1, 'right': 1}
        self.opacity = 0
        self.x = Window.width
        
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(40), orientation='horizontal')
        self.title_label = Label(text="🤖 Zaba AI", font_size=sp(14), size_hint_x=0.7)
        close_btn = Button(text="✕", font_size=sp(14), size_hint_x=0.15,
                          background_normal='', background_color=(0.5, 0.1, 0.1, 1),
                          color=(1, 1, 1, 1))
        close_btn.bind(on_release=lambda x: self.app_ref.close_ai_panel())
        header.add_widget(self.title_label)
        header.add_widget(close_btn)
        self.add_widget(header)
        
        # Provider selector
        provider_layout = BoxLayout(size_hint_y=None, height=dp(36), orientation='horizontal')
        self.provider_spinner = Spinner(
            text="OpenRouter",
            values=list(PROVIDER_INFO.keys()),
            size_hint_x=0.7,
            font_size=sp(11),
        )
        self.provider_spinner.text = "openrouter"
        provider_layout.add_widget(Label(text="Provider:", font_size=sp(10), size_hint_x=0.3))
        provider_layout.add_widget(self.provider_spinner)
        self.add_widget(provider_layout)
        
        # Chat messages area
        self.chat_scroll = ScrollView(size_hint_y=0.8)
        self.chat_layout = StackLayout(size_hint_y=None, spacing=dp(4), padding=dp(4))
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.chat_scroll.add_widget(self.chat_layout)
        self.add_widget(self.chat_scroll)
        
        # Input area
        input_layout = BoxLayout(size_hint_y=None, height=dp(44), orientation='horizontal', spacing=dp(4))
        self.chat_input = TextInput(
            hint_text="Ask something...",
            multiline=False,
            font_size=sp(12),
            size_hint_x=0.8,
        )
        self.chat_input.bind(on_text_validate=lambda x: self._send_message())
        send_btn = Button(text="➤", font_size=sp(16), size_hint_x=0.2,
                         background_normal='', background_color=(0.18, 0.55, 0.31, 1))
        send_btn.bind(on_release=lambda x: self._send_message())
        input_layout.add_widget(self.chat_input)
        input_layout.add_widget(send_btn)
        self.add_widget(input_layout)
    
    def _send_message(self):
        message = self.chat_input.text.strip()
        if not message:
            return
        self.chat_input.text = ""
        self.app_ref.send_ai_message(message, self.provider_spinner.text)
    
    def add_message(self, text: str, sender: str = "user"):
        """Add a message to the chat."""
        bg_color = (0.06, 0.09, 0.07, 1) if sender == "user" else (0.09, 0.06, 0.02, 1)
        text_color = (0.72, 0.96, 0.77, 1) if sender == "user" else (1.0, 0.69, 0.0, 1)
        
        msg_label = Label(
            text=text[:2000],
            font_size=sp(11),
            size_hint_y=None,
            height=max(dp(30), len(text) * dp(0.15)),
            color=text_color,
            halign='left',
            valign='top',
            text_size=(dp(240), None),
        )
        # Tricky: compute height after text_size
        msg_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(8)))
        self.chat_layout.add_widget(msg_label)
        
        # Auto scroll
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, 'scroll_y', 0), 0.05)
    
    def apply_theme(self, theme: dict):
        bg = theme.get('bg_panel', (0.04, 0.06, 0.05, 1))
        text_c = theme.get('text', (0.72, 0.96, 0.77, 1))
        bright = theme.get('text_bright', (0.22, 1.0, 0.078, 1))
        ai_c = theme.get('ai', (1.0, 0.69, 0.0, 1))
        
        self.title_label.color = bright


# ---------------------------------------------------------------------------
# Output Panel
# ---------------------------------------------------------------------------

class OutputPanel(BoxLayout):
    """Displays code execution output (stdout/stderr/images)."""
    
    def __init__(self, app_ref, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.app_ref = app_ref
        self.size_hint_y = None
        self.height = 0
        self.min_height = dp(120)
        self.max_height_ratio = 0.6
        
        # Header with close button
        header = BoxLayout(size_hint_y=None, height=dp(32), orientation='horizontal')
        self.output_label = Label(
            text="📤 Output",
            font_size=sp(11),
            size_hint_x=0.85,
            halign='left',
            valign='middle',
        )
        close_btn = Button(text="✕", font_size=sp(12), size_hint_x=0.15,
                          background_normal='', background_color=(0.3, 0.1, 0.1, 1),
                          color=(1, 0.3, 0.3, 1))
        close_btn.bind(on_release=lambda x: self.hide())
        header.add_widget(self.output_label)
        header.add_widget(close_btn)
        self.add_widget(header)
        
        # Output text
        self.output_scroll = ScrollView()
        self.output_text = Label(
            text="",
            font_size=sp(11),
            font_name='RobotoMono',
            halign='left',
            valign='top',
            text_size=(None, None),
            size_hint_y=None,
        )
        self.output_text.bind(width=lambda *x: self.output_text.setter('text_size')(self.output_text, (self.output_text.width, None)))
        self.output_text.bind(texture_size=lambda *x: setattr(self.output_text, 'height', self.output_text.texture_size[1]))
        self.output_scroll.add_widget(self.output_text)
        self.add_widget(self.output_scroll)
    
    def show_output(self, stdout: str = "", stderr: str = "", images: list = None):
        """Display output content."""
        text = ""
        if stdout:
            text += stdout
        if stderr:
            if text:
                text += "\n\n--- Error ---\n"
            text += stderr
        self.output_text.text = text or "(no output)"
        
        # Compute height
        target_h = min(
            max(self.min_height, dp(30) + len(text) * dp(0.15)),
            Window.height * self.max_height_ratio
        )
        anim = Animation(height=target_h, duration=0.25)
        anim.start(self)
    
    def hide(self):
        anim = Animation(height=0, duration=0.2)
        anim.start(self)
    
    def apply_theme(self, theme: dict):
        bg = theme.get('bg_panel', (0.04, 0.06, 0.05, 1))
        text_c = theme.get('text', (0.72, 0.96, 0.77, 1))
        err_c = theme.get('err', (1.0, 0.29, 0.29, 1))
        bright = theme.get('text_bright', (0.22, 1.0, 0.078, 1))
        
        self.output_label.color = bright
        self.output_text.color = text_c


# ---------------------------------------------------------------------------
# Tab Bar
# ---------------------------------------------------------------------------

class TabBar(ScrollView):
    """Horizontal tab bar for multi-tab editor."""
    
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.size_hint_y = None
        self.height = dp(32)
        self.do_scroll_x = True
        self.do_scroll_y = False
        
        self.tab_layout = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            size_hint_y=None,
            height=dp(32),
            spacing=dp(1),
        )
        self.tab_layout.bind(minimum_width=self.tab_layout.setter('width'))
        self.add_widget(self.tab_layout)
        
        self.tab_buttons = {}
    
    def update_tabs(self, tabs: list, active_tab_id: int):
        """Rebuild tab bar from tab list."""
        self.tab_layout.clear_widgets()
        self.tab_buttons.clear()
        
        for tab in tabs:
            btn = ToggleButton(
                text=tab.name[:20],
                font_size=sp(10),
                size_hint_x=None,
                width=dp(100),
                group='editor_tabs',
                background_normal='',
                background_color=(0.06, 0.09, 0.07, 1),
                color=(0.3, 0.47, 0.35, 1),
                border=(0, 0, 0, 0),
            )
            if tab.id == active_tab_id:
                btn.state = 'down'
            
            btn.bind(on_release=lambda inst, t=tab: self.app_ref.switch_tab(t.id))
            self.tab_layout.add_widget(btn)
            self.tab_buttons[tab.id] = btn
        
        # Add new tab button
        add_btn = Button(
            text="+",
            font_size=sp(14),
            size_hint_x=None,
            width=dp(36),
            background_normal='',
            background_color=(0.04, 0.06, 0.05, 1),
            color=(0.22, 1.0, 0.078, 1),
            border=(0, 0, 0, 0),
        )
        add_btn.bind(on_release=lambda x: self.app_ref.add_new_tab())
        self.tab_layout.add_widget(add_btn)
    
    def apply_theme(self, theme: dict):
        bg = theme.get('bg_panel_2', (0.06, 0.09, 0.07, 1))
        active_bg = theme.get('bg', (0.02, 0.03, 0.02, 1))
        text_c = theme.get('text_dim', (0.3, 0.47, 0.35, 1))
        bright = theme.get('text_bright', (0.22, 1.0, 0.078, 1))
        border = theme.get('border', (0.1, 0.3, 0.18, 1))
        
        for tid, btn in self.tab_buttons.items():
            if btn.state == 'down':
                btn.background_color = active_bg
                btn.color = bright
            else:
                btn.background_color = bg
                btn.color = text_c


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class ZabacodeApp(App):
    """ZABACODE v1.0.0 — Kivy Native Edition"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "ZABACODE"
        self.icon = "assets/logo.png"
        
        # State
        self.current_theme_name = DEFAULT_THEME
        self.current_theme = THEMES[DEFAULT_THEME]
        self.tabs = []
        self.active_tab_id = None
        self.sidebar_open = False
        self.ai_panel_open = False
        self.is_running = False
        
    def build(self):
        """Build the root widget tree."""
        # Initialize first tab
        self._add_tab("main.py", "# ZABACODE v1.0.0 — Kivy Edition\n# Happy coding!\n\nprint('Hello, ZABACODE!')\n")
        
        # Root layout (FloatLayout for overlays)
        self.root = FloatLayout()
        
        # Apply initial background
        self._apply_root_bg()
        
        # ---- Main content area ----
        self.main_layout = BoxLayout(orientation='vertical')
        
        # Top bar
        self.topbar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(44),
            spacing=dp(8),
            padding=(dp(8), dp(4), dp(8), dp(4)),
        )
        
        self.menu_btn = Button(
            text="≡",
            font_size=sp(20),
            size_hint_x=None,
            width=dp(40),
            background_normal='',
            color=(0.22, 1.0, 0.078, 1),
        )
        self.menu_btn.bind(on_release=lambda x: self.toggle_sidebar())
        
        self.title_label = Label(
            text="> ZABACODE",
            font_size=sp(14),
            bold=True,
            size_hint_x=0.5,
            halign='left',
            valign='middle',
        )
        
        self.status_dot = Label(text="●", font_size=sp(10), size_hint_x=None, width=dp(20))
        self.line_col_label = Label(text="Ln 1, Col 1", font_size=sp(10), size_hint_x=0.25, halign='right')
        
        self.topbar.add_widget(self.menu_btn)
        self.topbar.add_widget(self.title_label)
        self.topbar.add_widget(self.status_dot)
        self.topbar.add_widget(self.line_col_label)
        self.main_layout.add_widget(self.topbar)
        
        # Tab bar
        self.tab_bar = TabBar(self)
        self.main_layout.add_widget(self.tab_bar)
        
        # Editor area (with line numbers)
        editor_layout = BoxLayout(orientation='horizontal')
        
        self.line_numbers = LineNumbersWidget()
        editor_layout.add_widget(self.line_numbers)
        
        # Code editor using CodeInput with Python syntax highlighting
        self.editor = CodeInput(
            lexer=PythonLexer(),
            font_size=sp(13),
            font_name='RobotoMono',
            size_hint_x=0.92,
        )
        self.editor.bind(text=self._on_editor_text)
        self.editor.bind(cursor=self._on_cursor_change)
        
        # Set initial content
        if self.tabs:
            self.editor.text = self.tabs[0].content
        
        editor_layout.add_widget(self.editor)
        self.main_layout.add_widget(editor_layout)
        
        # Symbol bar (optional, shown if plugin active)
        self.symbol_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(32),
            spacing=dp(2),
            padding=(dp(4), dp(2)),
        )
        symbols = [":", "(", ")", "[", "]", "{", "}", "=", ".", ",", '"', "'", "#", "->", "==", "!=", "<=", ">="]
        for sym in symbols:
            btn = SymbolBarButton(sym, on_insert=self._insert_symbol)
            self.symbol_bar.add_widget(btn)
        self.main_layout.add_widget(self.symbol_bar)
        
        # Output panel
        self.output_panel = OutputPanel(self)
        self.main_layout.add_widget(self.output_panel)
        
        # Action bar
        self.action_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
            padding=(dp(8), dp(4)),
        )
        
        self.run_btn = Button(
            text="▶ JALANKAN",
            font_size=sp(14),
            font_name='Roboto',
            bold=True,
            background_normal='',
            background_color=(0.22, 1.0, 0.078, 1),
            color=(0.0, 0.1, 0.04, 1),
        )
        self.run_btn.bind(on_release=lambda x: self.run_code())
        
        self.check_btn = Button(
            text="CEK",
            font_size=sp(11),
            size_hint_x=None,
            width=dp(60),
            background_normal='',
            background_color=(0.1, 0.3, 0.18, 1),
            color=(0.72, 0.96, 0.77, 1),
        )
        self.check_btn.bind(on_release=lambda x: self.check_current_code())
        
        self.clear_btn = Button(
            text="BERSIHKAN",
            font_size=sp(11),
            size_hint_x=None,
            width=dp(80),
            background_normal='',
            background_color=(0.2, 0.1, 0.1, 1),
            color=(1, 0.5, 0.5, 1),
        )
        self.clear_btn.bind(on_release=lambda x: self.clear_output())
        
        self.ai_btn = Button(
            text="🤖",
            font_size=sp(16),
            size_hint_x=None,
            width=dp(44),
            background_normal='',
            background_color=(0.3, 0.2, 0.0, 1),
            color=(1.0, 0.69, 0.0, 1),
        )
        self.ai_btn.bind(on_release=lambda x: self.toggle_ai_panel())
        
        self.action_bar.add_widget(self.run_btn)
        self.action_bar.add_widget(self.check_btn)
        self.action_bar.add_widget(self.clear_btn)
        self.action_bar.add_widget(Widget())  # spacer
        self.action_bar.add_widget(self.ai_btn)
        self.main_layout.add_widget(self.action_bar)
        
        self.root.add_widget(self.main_layout)
        
        # ---- Overlay: Sidebar ----
        self.sidebar = SidebarPanel(self)
        self.root.add_widget(self.sidebar)
        
        # Sidebar backdrop
        self.sidebar_backdrop = Widget(
            size_hint=(None, None),
            size=Window.size,
            opacity=0,
        )
        self.root.add_widget(self.sidebar_backdrop)
        
        # ---- Overlay: AI Panel ----
        self.ai_panel = AIChatPanel(self)
        self.root.add_widget(self.ai_panel)
        
        # Apply theme
        self._apply_theme_full()
        
        # Update tab bar
        self._refresh_tab_bar()
        
        # Welcome message in AI
        self.ai_panel.add_message("Selamat datang di ZABACODE v1.0.0! Saya Zaba AI, asisten coding tsundere kamu. Ada yang bisa dibantu? 😏", "ai")
        
        return self.root
    
    def _apply_root_bg(self):
        """Apply root background color."""
        bg = self.current_theme.get('bg', (0.02, 0.03, 0.02, 1))
        with self.root.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*bg)
            self._bg_rect = Rectangle(pos=self.root.pos, size=self.root.size)
        self.root.bind(pos=self._update_bg_rect, size=self._update_bg_rect)
    
    def _update_bg_rect(self, instance, value):
        if hasattr(self, '_bg_rect'):
            self._bg_rect.pos = instance.pos
            self._bg_rect.size = instance.size
    
    # -----------------------------------------------------------------------
    # Tab Management
    # -----------------------------------------------------------------------
    
    def _add_tab(self, name: str = None, content: str = "", filepath: str = None):
        tab = TabData(name=name, content=content, filepath=filepath)
        self.tabs.append(tab)
        self.active_tab_id = tab.id
    
    def add_new_tab(self):
        self._add_tab()
        self._switch_to_active_tab()
        self._refresh_tab_bar()
    
    def switch_tab(self, tab_id: int):
        # Save current tab content
        self._save_current_tab_content()
        # Switch
        self.active_tab_id = tab_id
        self._switch_to_active_tab()
        self._refresh_tab_bar()
    
    def _switch_to_active_tab(self):
        tab = self._get_active_tab()
        if tab:
            self.editor.text = tab.content
            self._update_line_numbers()
    
    def _save_current_tab_content(self):
        tab = self._get_active_tab()
        if tab:
            tab.content = self.editor.text
    
    def _get_active_tab(self) -> TabData | None:
        for tab in self.tabs:
            if tab.id == self.active_tab_id:
                return tab
        return None
    
    def _refresh_tab_bar(self):
        self.tab_bar.update_tabs(self.tabs, self.active_tab_id)
        self.tab_bar.apply_theme(self.current_theme)
    
    # -----------------------------------------------------------------------
    # Editor Callbacks
    # -----------------------------------------------------------------------
    
    def _on_editor_text(self, instance, value):
        self._update_line_numbers()
        tab = self._get_active_tab()
        if tab:
            tab.content = value
            tab.modified = True
    
    def _on_cursor_change(self, instance, value):
        row, col = value
        self.line_col_label.text = f"Ln {row+1}, Col {col+1}"
    
    def _update_line_numbers(self):
        self.line_numbers.update_line_numbers(self.editor.text or "")
    
    def _insert_symbol(self, symbol: str):
        """Insert a symbol at the current cursor position."""
        if self.editor:
            cur = self.editor.cursor
            text = self.editor.text
            lines = text.split('\n')
            if cur and cur[0] < len(lines):
                line = lines[cur[0]]
                col = min(cur[1], len(line))
                lines[cur[0]] = line[:col] + symbol + line[col:]
                self.editor.text = '\n'.join(lines)
    
    # -----------------------------------------------------------------------
    # Code Execution
    # -----------------------------------------------------------------------
    
    def run_code(self):
        """Run the current code in an isolated subprocess."""
        if self.is_running:
            return
        
        code = self.editor.text
        if not code.strip():
            self.output_panel.show_output(stderr="No code to execute.")
            return
        
        self.is_running = True
        self.run_btn.disabled = True
        self.run_btn.text = "⏳ RUNNING..."
        self.status_dot.color = (1.0, 0.69, 0.0, 1)  # yellow
        
        # Run in background thread
        def _run():
            result = execute_code_isolated(code, timeout=30)
            Clock.schedule_once(lambda dt: self._on_run_complete(result))
        
        threading.Thread(target=_run, daemon=True).start()
    
    def _on_run_complete(self, result: dict):
        self.is_running = False
        self.run_btn.disabled = False
        
        if result.get("timeout"):
            self.run_btn.text = "▶ JALANKAN"
            self.status_dot.color = (1.0, 0.29, 0.29, 1)  # red
            self.output_panel.show_output(
                stderr=result.get("stderr", "") + "\n[Process timed out]"
            )
        elif result.get("ok"):
            self.run_btn.text = "▶ JALANKAN"
            self.status_dot.color = (0.22, 1.0, 0.078, 1)  # green
            self.output_panel.show_output(stdout=result.get("stdout", ""))
        else:
            self.run_btn.text = "▶ JALANKAN"
            self.status_dot.color = (1.0, 0.29, 0.29, 1)  # red
            self.output_panel.show_output(
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", "")
            )
    
    def check_current_code(self):
        """Check current code for syntax issues."""
        code = self.editor.text
        result = check_code(code)
        if result.get("valid"):
            self.output_panel.show_output(stdout="✅ Code is valid! Ready to run.")
        else:
            issues_text = "\n".join(f"  • {i}" for i in result.get("issues", []))
            self.output_panel.show_output(stderr=f"⚠️ Issues found:\n{issues_text}")
    
    def clear_output(self):
        self.output_panel.hide()
    
    # -----------------------------------------------------------------------
    # Sidebar
    # -----------------------------------------------------------------------
    
    def toggle_sidebar(self):
        if self.sidebar_open:
            self.close_sidebar()
        else:
            self.open_sidebar()
    
    def open_sidebar(self):
        self.sidebar_open = True
        anim = Animation(x=0, opacity=1, duration=0.2)
        anim.start(self.sidebar)
        self.sidebar_backdrop.opacity = 0.6
        self.sidebar_backdrop.size = Window.size
    
    def close_sidebar(self):
        self.sidebar_open = False
        anim = Animation(x=-self.sidebar.width, opacity=0, duration=0.2)
        anim.start(self.sidebar)
        self.sidebar_backdrop.opacity = 0
    
    # -----------------------------------------------------------------------
    # AI Panel
    # -----------------------------------------------------------------------
    
    def toggle_ai_panel(self):
        if self.ai_panel_open:
            self.close_ai_panel()
        else:
            self.open_ai_panel()
    
    def open_ai_panel(self):
        self.ai_panel_open = True
        target_x = Window.width - self.ai_panel.width
        anim = Animation(x=target_x, opacity=1, duration=0.2)
        anim.start(self.ai_panel)
    
    def close_ai_panel(self):
        self.ai_panel_open = False
        anim = Animation(x=Window.width, opacity=0, duration=0.2)
        anim.start(self.ai_panel)
    
    def send_ai_message(self, message: str, provider: str = "openrouter"):
        """Send a message to the AI provider."""
        self.ai_panel.add_message(message, "user")
        code = self.editor.text
        
        def _send():
            keys = load_keys()
            api_key = keys.get(provider)
            
            if not api_key:
                Clock.schedule_once(lambda dt: self.ai_panel.add_message(
                    f"⚠️ API Key for {provider} not set. Please enter it in AI Keys menu.", "system"
                ))
                return
            
            handler = PROVIDER_HANDLERS.get(provider)
            if not handler:
                Clock.schedule_once(lambda dt: self.ai_panel.add_message(
                    f"❌ Provider '{provider}' not implemented.", "system"
                ))
                return
            
            result = handler(api_key, message, code)
            Clock.schedule_once(lambda dt: self.ai_panel.add_message(
                result.get("reply", result.get("message", "Unknown error")), "ai"
            ))
        
        threading.Thread(target=_send, daemon=True).start()
    
    # -----------------------------------------------------------------------
    # Sidebar Action Handler
    # -----------------------------------------------------------------------
    
    def handle_sidebar_action(self, action: str):
        """Handle sidebar menu actions."""
        if action == "files":
            self._show_file_manager()
        elif action == "save":
            self._show_save_dialog()
        elif action == "libraries":
            self._show_library_manager()
        elif action == "ai_keys":
            self._show_ai_keys_dialog()
        elif action == "themes":
            self._show_theme_selector()
        elif action == "plugins":
            self._show_plugin_marketplace()
        elif action == "language":
            self._show_language_selector()
        elif action == "about":
            self._show_about_dialog()
    
    # -----------------------------------------------------------------------
    # Dialogs
    # -----------------------------------------------------------------------
    
    def _show_file_manager(self):
        """Show file manager dialog."""
        modal = ModalView(size_hint=(0.9, 0.8), auto_dismiss=True)
        layout = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(8))
        
        header = Label(text="📁 File Manager", font_size=sp(14), size_hint_y=None, height=dp(36))
        layout.add_widget(header)
        
        # File list
        scroll = ScrollView(size_hint_y=0.7)
        file_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        file_layout.bind(minimum_height=file_layout.setter('height'))
        
        files = list_files()
        if files:
            for f in files:
                row = BoxLayout(size_hint_y=None, height=dp(36), orientation='horizontal', spacing=dp(4))
                name_label = Label(text=f['name'], font_size=sp(11), size_hint_x=0.5, halign='left')
                open_btn = Button(text="Buka", font_size=sp(10), size_hint_x=0.25,
                                 background_normal='', background_color=(0.18, 0.55, 0.31, 1))
                del_btn = Button(text="Hapus", font_size=sp(10), size_hint_x=0.25,
                                background_normal='', background_color=(0.5, 0.1, 0.1, 1))
                
                def _open_file(fname=f['name']):
                    result = read_file(fname)
                    if result.get("ok"):
                        tab = self._get_active_tab()
                        if tab:
                            tab.name = fname
                            tab.filepath = fname
                            tab.content = result['content']
                            self.editor.text = result['content']
                            self._refresh_tab_bar()
                        modal.dismiss()
                
                def _del_file(fname=f['name']):
                    delete_file(fname)
                    modal.dismiss()
                    self._show_file_manager()
                
                open_btn.bind(on_release=lambda x, fn=f['name']: _open_file(fn))
                del_btn.bind(on_release=lambda x, fn=f['name']: _del_file(fn))
                
                row.add_widget(name_label)
                row.add_widget(open_btn)
                row.add_widget(del_btn)
                file_layout.add_widget(row)
        else:
            file_layout.add_widget(Label(text="No saved files yet.", font_size=sp(11)))
        
        scroll.add_widget(file_layout)
        layout.add_widget(scroll)
        
        close_btn = Button(text="Close", font_size=sp(12), size_hint_y=None, height=dp(36),
                          background_normal='', background_color=(0.3, 0.1, 0.1, 1))
        close_btn.bind(on_release=lambda x: modal.dismiss())
        layout.add_widget(close_btn)
        
        modal.add_widget(layout)
        modal.open()
    
    def _show_save_dialog(self):
        """Show save file dialog."""
        modal = ModalView(size_hint=(0.85, 0.35), auto_dismiss=True)
        layout = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(12))
        
        header = Label(text="💾 Save File", font_size=sp(14), size_hint_y=None, height=dp(30))
        layout.add_widget(header)
        
        tab = self._get_active_tab()
        default_name = tab.name if tab else "untitled.py"
        
        name_input = TextInput(text=default_name, font_size=sp(12), size_hint_y=None, height=dp(36), multiline=False)
        layout.add_widget(name_input)
        
        btn_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        save_btn = Button(text="Save", font_size=sp(12),
                         background_normal='', background_color=(0.18, 0.55, 0.31, 1))
        cancel_btn = Button(text="Cancel", font_size=sp(12),
                           background_normal='', background_color=(0.3, 0.1, 0.1, 1))
        
        def _save():
            fname = name_input.text.strip()
            result = save_file(fname, self.editor.text)
            if result.get("ok"):
                tab = self._get_active_tab()
                if tab:
                    tab.name = result['filename']
                    tab.filepath = result['filename']
                    self._refresh_tab_bar()
            modal.dismiss()
        
        save_btn.bind(on_release=lambda x: _save())
        cancel_btn.bind(on_release=lambda x: modal.dismiss())
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        layout.add_widget(btn_row)
        
        modal.add_widget(layout)
        modal.open()
    
    def _show_library_manager(self):
        """Show library manager dialog."""
        modal = ModalView(size_hint=(0.95, 0.85), auto_dismiss=True)
        layout = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(8))
        
        header = Label(text="📦 Library Manager (zabapip)", font_size=sp(13), size_hint_y=None, height=dp(30))
        layout.add_widget(header)
        
        # Category filter
        categories = ["All", "Web & API", "Web & Scraping", "Data & Math", "Database", 
                      "AI & Automation", "Utilities", "Security", "Media & Images", 
                      "Games & Media", "Testing", "Data Format", "Networking"]
        cat_spinner = Spinner(
            text="All", values=categories,
            size_hint_y=None, height=dp(32), font_size=sp(10),
        )
        layout.add_widget(cat_spinner)
        
        # Library list
        scroll = ScrollView(size_hint_y=0.8)
        lib_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        lib_layout.bind(minimum_height=lib_layout.setter('height'))
        
        all_libs = get_all_libraries()
        mode_colors = {
            "offline": (0.22, 1.0, 0.078, 1),
            "online": (0.3, 0.6, 1.0, 1),
            "hybrid": (1.0, 0.69, 0.0, 1),
        }
        
        for name, info in sorted(all_libs.items()):
            row = BoxLayout(size_hint_y=None, height=dp(50), orientation='horizontal', spacing=dp(4))
            
            # Info column
            info_col = BoxLayout(orientation='vertical', size_hint_x=0.7)
            name_label = Label(
                text=f"{name} {'✅' if info.get('installed') else ''}",
                font_size=sp(10),
                halign='left', valign='middle',
                size_hint_y=0.5,
            )
            mode = info.get('mode', 'unknown')
            mode_color = mode_colors.get(mode, (0.5, 0.5, 0.5, 1))
            desc_label = Label(
                text=f"[{mode.upper()}] {info.get('category', '')} — {info.get('reason', '')[:50]}",
                font_size=sp(8),
                color=mode_color,
                halign='left', valign='middle',
                size_hint_y=0.5,
            )
            info_col.add_widget(name_label)
            info_col.add_widget(desc_label)
            row.add_widget(info_col)
            
            # Install button
            if info.get('installed'):
                inst_btn = Button(
                    text="✓", font_size=sp(12),
                    size_hint_x=0.3,
                    background_normal='',
                    background_color=(0.1, 0.3, 0.18, 1),
                    color=(0.22, 1.0, 0.078, 1),
                    disabled=True,
                )
            elif info.get('tier') == 'buildtime':
                inst_btn = Button(
                    text="🏗️ Rebuild", font_size=sp(9),
                    size_hint_x=0.3,
                    background_normal='',
                    background_color=(0.3, 0.2, 0.0, 1),
                    color=(1.0, 0.69, 0.0, 1),
                )
            else:
                inst_btn = Button(
                    text="Install", font_size=sp(10),
                    size_hint_x=0.3,
                    background_normal='',
                    background_color=(0.18, 0.55, 0.31, 1),
                    color=(1, 1, 1, 1),
                )
                def _install(lib_name=name):
                    inst_btn.text = "..."
                    inst_btn.disabled = True
                    threading.Thread(target=lambda: self._install_lib(lib_name, inst_btn), daemon=True).start()
                inst_btn.bind(on_release=lambda x, n=name: _install(n))
            
            row.add_widget(inst_btn)
            lib_layout.add_widget(row)
        
        scroll.add_widget(lib_layout)
        layout.add_widget(scroll)
        
        close_btn = Button(text="Close", font_size=sp(12), size_hint_y=None, height=dp(36),
                          background_normal='', background_color=(0.3, 0.1, 0.1, 1))
        close_btn.bind(on_release=lambda x: modal.dismiss())
        layout.add_widget(close_btn)
        
        modal.add_widget(layout)
        modal.open()
    
    def _install_lib(self, name: str, btn: Button):
        """Install a library (runs in background thread)."""
        result = install_library(name)
        msg = result.get("message", "")
        Clock.schedule_once(lambda dt: setattr(btn, 'text', '✓' if result.get('ok') else '✗'))
    
    def _show_ai_keys_dialog(self):
        """Show AI API keys management dialog."""
        modal = ModalView(size_hint=(0.9, 0.7), auto_dismiss=True)
        layout = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(8))
        
        header = Label(text="🔑 AI API Keys", font_size=sp(14), size_hint_y=None, height=dp(30))
        layout.add_widget(header)
        
        keys = load_keys()
        
        scroll = ScrollView(size_hint_y=0.75)
        keys_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))
        keys_layout.bind(minimum_height=keys_layout.setter('height'))
        
        for provider, info in PROVIDER_INFO.items():
            row = BoxLayout(size_hint_y=None, height=dp(60), orientation='vertical', spacing=dp(2))
            
            mode_str = info.get('mode', 'online')
            status = "✅ Active" if keys.get(provider) else "❌ Not set"
            label = Label(
                text=f"{info.get('icon', '')} {info.get('name', provider)} [{mode_str}] — {status}",
                font_size=sp(10), halign='left', valign='middle', size_hint_y=0.4
            )
            row.add_widget(label)
            
            input_row = BoxLayout(size_hint_y=0.6, spacing=dp(4))
            key_input = TextInput(
                hint_text=f"Enter {provider} API key...",
                password=True,
                font_size=sp(10),
                size_hint_x=0.7,
                multiline=False,
            )
            if keys.get(provider):
                key_input.hint_text = f"Current: {'*' * 8} (enter new to update)"
            
            save_btn = Button(
                text="Save", font_size=sp(10),
                size_hint_x=0.3,
                background_normal='', background_color=(0.18, 0.55, 0.31, 1),
            )
            
            def _save_key(p=provider, inp=key_input):
                key = inp.text.strip()
                if key:
                    save_key(p, key)
                    inp.text = ""
                    inp.hint_text = "Saved! ✓"
            
            save_btn.bind(on_release=lambda x, p=provider, inp=key_input: _save_key(p, inp))
            input_row.add_widget(key_input)
            input_row.add_widget(save_btn)
            row.add_widget(input_row)
            
            keys_layout.add_widget(row)
        
        scroll.add_widget(keys_layout)
        layout.add_widget(scroll)
        
        close_btn = Button(text="Close", font_size=sp(12), size_hint_y=None, height=dp(36),
                          background_normal='', background_color=(0.3, 0.1, 0.1, 1))
        close_btn.bind(on_release=lambda x: modal.dismiss())
        layout.add_widget(close_btn)
        
        modal.add_widget(layout)
        modal.open()
    
    def _show_theme_selector(self):
        """Show theme selection dialog."""
        modal = ModalView(size_hint=(0.85, 0.75), auto_dismiss=True)
        layout = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(8))
        
        header = Label(text="🎨 Choose Theme", font_size=sp(14), size_hint_y=None, height=dp(30))
        layout.add_widget(header)
        
        scroll = ScrollView(size_hint_y=0.85)
        theme_layout = GridLayout(cols=2, size_hint_y=None, spacing=dp(6), padding=dp(4))
        theme_layout.bind(minimum_height=theme_layout.setter('height'))
        
        for theme_key, theme_data in THEMES.items():
            btn = Button(
                text=f"{theme_data.get('icon', '🎨')} {theme_data.get('display_name', theme_key)}",
                font_size=sp(11),
                size_hint_y=None,
                height=dp(44),
                background_normal='',
                background_color=theme_data.get('border_bright', (0.18, 0.55, 0.31, 1)),
                color=theme_data.get('text_bright', (1, 1, 1, 1)),
            )
            
            def _apply(tk=theme_key):
                self._set_theme(tk)
                modal.dismiss()
            
            btn.bind(on_release=lambda x, tk=theme_key: _apply(tk))
            theme_layout.add_widget(btn)
        
        scroll.add_widget(theme_layout)
        layout.add_widget(scroll)
        
        close_btn = Button(text="Close", font_size=sp(12), size_hint_y=None, height=dp(36),
                          background_normal='', background_color=(0.3, 0.1, 0.1, 1))
        close_btn.bind(on_release=lambda x: modal.dismiss())
        layout.add_widget(close_btn)
        
        modal.add_widget(layout)
        modal.open()
    
    def _set_theme(self, theme_name: str):
        """Apply a theme by name."""
        theme = get_theme(theme_name)
        if theme:
            self.current_theme_name = theme_name
            self.current_theme = theme
            self._apply_theme_full()
    
    def _apply_theme_full(self):
        """Apply current theme to all widgets."""
        theme = self.current_theme
        
        # Root background
        if hasattr(self, '_bg_rect'):
            self._bg_rect.color = theme.get('bg', (0.02, 0.03, 0.02, 1))
        
        # Topbar
        if hasattr(self, 'topbar'):
            for child in self.topbar.children:
                if isinstance(child, Label):
                    child.color = theme.get('text_bright', (0.22, 1.0, 0.078, 1))
                elif isinstance(child, Button):
                    child.color = theme.get('text_bright', (0.22, 1.0, 0.078, 1))
                    child.background_color = theme.get('bg_panel', (0.04, 0.06, 0.05, 1))
        
        # Editor
        if hasattr(self, 'editor'):
            self.editor.background_color = theme.get('editor_bg', (0.02, 0.03, 0.02, 1))
            self.editor.foreground_color = theme.get('editor_fg', (0.72, 0.96, 0.77, 1))
        
        # Line numbers
        if hasattr(self, 'line_numbers'):
            self.line_numbers.color = theme.get('line_number_fg', (0.3, 0.47, 0.35, 1))
        
        # Tab bar
        if hasattr(self, 'tab_bar'):
            self.tab_bar.apply_theme(theme)
        
        # Symbol bar
        if hasattr(self, 'symbol_bar'):
            for btn in self.symbol_bar.children:
                if isinstance(btn, SymbolBarButton):
                    btn.background_color = theme.get('bg_panel_2', (0.06, 0.09, 0.07, 1))
                    btn.color = theme.get('text_bright', (0.22, 1.0, 0.078, 1))
        
        # Action bar
        if hasattr(self, 'action_bar'):
            for child in self.action_bar.children:
                if isinstance(child, Button):
                    if child == self.run_btn:
                        child.background_color = theme.get('text_bright', (0.22, 1.0, 0.078, 1))
                        child.color = (0, 0, 0, 1)
                    elif child == self.ai_btn:
                        child.background_color = theme.get('ai', (1.0, 0.69, 0.0, 1))
                        child.color = (0, 0, 0, 1)
        
        # Sidebar
        if hasattr(self, 'sidebar'):
            self.sidebar.apply_theme(theme)
        
        # AI Panel
        if hasattr(self, 'ai_panel'):
            self.ai_panel.apply_theme(theme)
        
        # Output
        if hasattr(self, 'output_panel'):
            self.output_panel.apply_theme(theme)
    
    def _show_plugin_marketplace(self):
        """Show plugin marketplace dialog."""
        modal = ModalView(size_hint=(0.9, 0.85), auto_dismiss=True)
        layout = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(8))
        
        header = Label(text="🧩 Plugins & Addons", font_size=sp(14), size_hint_y=None, height=dp(30))
        layout.add_widget(header)
        
        # Snippets section
        snippets_label = Label(text="📜 Quick Snippets", font_size=sp(12), size_hint_y=None, height=dp(24))
        layout.add_widget(snippets_label)
        
        snippet_grid = GridLayout(cols=2, size_hint_y=None, spacing=dp(4))
        snippet_grid.bind(minimum_height=snippet_grid.setter('height'))
        
        for sid, snippet in get_snippets().items():
            btn = Button(
                text=snippet['name'],
                font_size=sp(9),
                size_hint_y=None,
                height=dp(30),
                background_normal='',
                background_color=(0.1, 0.3, 0.18, 1),
                color=(0.72, 0.96, 0.77, 1),
            )
            
            def _insert_snippet(s=snippet):
                self.editor.text = s['code']
                modal.dismiss()
            
            btn.bind(on_release=lambda x, s=snippet: _insert_snippet(s))
            snippet_grid.add_widget(btn)
        
        scroll = ScrollView(size_hint_y=0.55)
        scroll.add_widget(snippet_grid)
        layout.add_widget(scroll)
        
        # Plugins section
        plugins_label = Label(text="🧩 Active Plugins", font_size=sp(12), size_hint_y=None, height=dp(24))
        layout.add_widget(plugins_label)
        
        plugin_scroll = ScrollView(size_hint_y=0.3)
        plugin_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        plugin_layout.bind(minimum_height=plugin_layout.setter('height'))
        
        all_plugins = get_all_plugins()
        for pid, pinfo in all_plugins.items():
            row = BoxLayout(size_hint_y=None, height=dp(36), orientation='horizontal', spacing=dp(4))
            label = Label(text=f"{pinfo['name']}", font_size=sp(9), halign='left', size_hint_x=0.7)
            toggle_btn = Button(
                text="✓ Active" if pinfo['active'] else "Enable",
                font_size=sp(9),
                size_hint_x=0.3,
                background_normal='',
                background_color=(0.1, 0.3, 0.18, 1) if pinfo['active'] else (0.3, 0.1, 0.1, 1),
            )
            
            def _toggle(p=pid, b=toggle_btn):
                result = toggle_plugin(p)
                b.text = "✓ Active" if result.get('active') else "Enable"
                b.background_color = (0.1, 0.3, 0.18, 1) if result.get('active') else (0.3, 0.1, 0.1, 1)
            
            toggle_btn.bind(on_release=lambda x, p=pid, b=toggle_btn: _toggle(p, b))
            row.add_widget(label)
            row.add_widget(toggle_btn)
            plugin_layout.add_widget(row)
        
        plugin_scroll.add_widget(plugin_layout)
        layout.add_widget(plugin_scroll)
        
        close_btn = Button(text="Close", font_size=sp(12), size_hint_y=None, height=dp(36),
                          background_normal='', background_color=(0.3, 0.1, 0.1, 1))
        close_btn.bind(on_release=lambda x: modal.dismiss())
        layout.add_widget(close_btn)
        
        modal.add_widget(layout)
        modal.open()
    
    def _show_language_selector(self):
        """Show language selection dialog."""
        modal = ModalView(size_hint=(0.75, 0.55), auto_dismiss=True)
        layout = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(8))
        
        header = Label(text="🌐 Choose Language", font_size=sp(14), size_hint_y=None, height=dp(30))
        layout.add_widget(header)
        
        for lang_code, lang_name in LANGUAGES.items():
            btn = Button(
                text=lang_name + (" ✓" if i18n.lang == lang_code else ""),
                font_size=sp(13),
                size_hint_y=None,
                height=dp(40),
                background_normal='',
                background_color=(0.18, 0.55, 0.31, 1) if i18n.lang == lang_code else (0.1, 0.15, 0.12, 1),
                color=(0.22, 1.0, 0.078, 1) if i18n.lang == lang_code else (0.72, 0.96, 0.77, 1),
            )
            
            def _set_lang(lc=lang_code):
                i18n.set_language(lc)
                self._update_ui_text()
                modal.dismiss()
            
            btn.bind(on_release=lambda x, lc=lang_code: _set_lang(lc))
            layout.add_widget(btn)
        
        modal.add_widget(layout)
        modal.open()
    
    def _show_about_dialog(self):
        """Show about dialog."""
        modal = ModalView(size_hint=(0.85, 0.55), auto_dismiss=True)
        layout = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(16))
        
        layout.add_widget(Label(
            text="⚡ ZABACODE ⚡",
            font_size=sp(20),
            bold=True,
            size_hint_y=None, height=dp(40),
        ))
        layout.add_widget(Label(
            text=f"Version {__version__} — Kivy Native Edition",
            font_size=sp(12),
            size_hint_y=None, height=dp(24),
        ))
        layout.add_widget(Label(
            text="Anti-Capitalist Mobile Python IDE\n100% Free, Open Source, Zero Telemetry\nLicense: GPLv3",
            font_size=sp(11),
            size_hint_y=None, height=dp(60),
        ))
        layout.add_widget(Label(
            text="Creator: Zaqi (muzape28-blip)\nCo-Dev: Arena.ai Agent",
            font_size=sp(10),
            size_hint_y=None, height=dp(40),
        ))
        
        close_btn = Button(
            text="Close", font_size=sp(12), size_hint_y=None, height=dp(36),
            background_normal='', background_color=(0.3, 0.1, 0.1, 1),
        )
        close_btn.bind(on_release=lambda x: modal.dismiss())
        layout.add_widget(close_btn)
        
        modal.add_widget(layout)
        modal.open()
    
    def _update_ui_text(self):
        """Update all UI text based on current language."""
        t = i18n.t
        self.run_btn.text = t("run")
        self.clear_btn.text = t("clear")
        self.check_btn.text = t("check")
        self.title_label.text = f"> {t('app_title')}"
        # Rebuild tab bar
        self._refresh_tab_bar()
    
    # -----------------------------------------------------------------------
    # Window resize handler
    # -----------------------------------------------------------------------
    
    def on_start(self):
        Window.bind(on_resize=self._on_window_resize)
    
    def _on_window_resize(self, instance, width, height):
        if self.ai_panel_open:
            self.ai_panel.x = width - self.ai_panel.width
