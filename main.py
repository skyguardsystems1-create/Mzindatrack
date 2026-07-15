"""
MzindaTrack Mobile App - GPS Tracking Client
GPS yathu, Chitetezo chathu
"""

import os
import re
import json
import requests
import webbrowser
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform
from kivy.network.urlrequest import UrlRequest
from kivy.storage.jsonstore import JsonStore
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty, NumericProperty

# For Android permissions
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.INTERNET,
        Permission.ACCESS_FINE_LOCATION,
        Permission.ACCESS_COARSE_LOCATION
    ])

# ==================== CONFIGURATION ====================
DEFAULT_SERVER_URLS = [
    "https://culminate-retype-cresting.ngrok-free.dev",
    "https://unowing-earnest-gapless.ngrok-free.dev"
]

APP_NAME = "MzindaTrack"
APP_VERSION = "1.0"

# ==================== STORE SETTINGS ====================
class SettingsStore:
    """Handle persistent settings storage"""
    
    def __init__(self):
        self.store = None
        try:
            self.store = JsonStore('mzindatrack_settings.json')
        except:
            pass
    
    def get(self, key, default=None):
        try:
            if self.store and self.store.exists(key):
                return self.store.get(key)
            return default
        except:
            return default
    
    def put(self, key, value):
        try:
            if self.store:
                self.store.put(key, **value)
            return True
        except:
            return False

# ==================== CUSTOM WIDGETS ====================
class StatusBar(BoxLayout):
    """Custom status bar"""
    status_text = StringProperty("Ready")
    status_color = StringProperty("#8892b0")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(30)
        self.padding = [dp(10), dp(5)]
        self.orientation = 'horizontal'


class Header(BoxLayout):
    """Custom header with hamburger menu"""
    title = StringProperty("MzindaTrack")
    page_name = StringProperty("Connect")
    status_indicator = StringProperty("⚪")
    status_tooltip = StringProperty("Disconnected")
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = [dp(10), dp(3)]
        self.spacing = dp(8)
        
        # Auto-connect indicator (will be added by app)


class CustomPopup(Popup):
    """Custom styled popup"""
    def __init__(self, title, content, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.content = content
        self.size_hint = (0.9, None)
        self.height = dp(300)
        self.auto_dismiss = True
        self.separator_height = dp(1)

# ==================== WEB VIEW - PLACEHOLDER ====================
class MobileWebView(BoxLayout):
    """Web view for mobile (simplified - uses WebView on Android)"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.spacing = 0
        
        # Toolbar
        self.toolbar = BoxLayout(
            size_hint_y=None,
            height=dp(36),
            padding=[dp(4), dp(2)],
            spacing=dp(2)
        )
        
        # Navigation buttons
        self.back_btn = Button(
            text="◀",
            size_hint=(None, None),
            size=(dp(32), dp(28)),
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.back_btn.bind(on_press=self.go_back)
        
        self.forward_btn = Button(
            text="▶",
            size_hint=(None, None),
            size=(dp(32), dp(28)),
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.forward_btn.bind(on_press=self.go_forward)
        
        self.refresh_btn = Button(
            text="⟳",
            size_hint=(None, None),
            size=(dp(32), dp(28)),
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.refresh_btn.bind(on_press=self.refresh)
        
        # URL bar
        self.url_bar = TextInput(
            multiline=False,
            hint_text="Enter URL",
            size_hint=(1, None),
            height=dp(28),
            background_color=(0.1, 0.1, 0.15, 1),
            foreground_color=(0.88, 0.9, 0.93, 1)
        )
        
        # Home button
        self.home_btn = Button(
            text="🏠",
            size_hint=(None, None),
            size=(dp(32), dp(28)),
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.home_btn.bind(on_press=self.go_home)
        
        # Open in browser
        self.open_btn = Button(
            text="↗",
            size_hint=(None, None),
            size=(dp(32), dp(28)),
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.open_btn.bind(on_press=self.open_in_browser)
        
        # Add to toolbar
        self.toolbar.add_widget(self.back_btn)
        self.toolbar.add_widget(self.forward_btn)
        self.toolbar.add_widget(self.refresh_btn)
        self.toolbar.add_widget(self.url_bar)
        self.toolbar.add_widget(self.home_btn)
        self.toolbar.add_widget(self.open_btn)
        
        self.add_widget(self.toolbar)
        
        # Web view container
        self.web_container = BoxLayout()
        
        # Show placeholder
        self.placeholder = Label(
            text="🌐 Web View\n\nEnter a URL to browse",
            halign='center',
            valign='middle',
            color=(0.4, 0.45, 0.5, 1)
        )
        self.web_container.add_widget(self.placeholder)
        
        # WebView will be added when on Android
        if platform == 'android':
            try:
                from kivy.uix.webview import WebView
                self.webview = WebView()
                self.webview.size_hint = (1, 1)
                # We'll replace placeholder with webview when needed
            except ImportError:
                pass
        
        self.add_widget(self.web_container)
        self.current_url = ""
        self.home_url = ""
    
    def load_url(self, url):
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url
        self.current_url = url
        self.url_bar.text = url
        
        if platform == 'android':
            try:
                from kivy.uix.webview import WebView
                if hasattr(self, 'webview'):
                    self.web_container.clear_widgets()
                    self.web_container.add_widget(self.webview)
                    self.webview.load(url)
                    return
            except:
                pass
        
        # Fallback: open in browser
        webbrowser.open(url)
    
    def set_home_url(self, url):
        self.home_url = url
    
    def go_home(self, instance=None):
        if self.home_url:
            self.load_url(self.home_url)
    
    def go_back(self, instance=None):
        if platform == 'android' and hasattr(self, 'webview'):
            try:
                self.webview.go_back()
                return
            except:
                pass
    
    def go_forward(self, instance=None):
        if platform == 'android' and hasattr(self, 'webview'):
            try:
                self.webview.go_forward()
                return
            except:
                pass
    
    def refresh(self, instance=None):
        if platform == 'android' and hasattr(self, 'webview'):
            try:
                self.webview.reload()
                return
            except:
                pass
        # Reload in browser fallback
        if self.current_url:
            webbrowser.open(self.current_url)
    
    def open_in_browser(self, instance=None):
        if self.current_url:
            webbrowser.open(self.current_url)

# ==================== API CLIENT ====================
class MzindaTrackAPI:
    """API client for MzindaTrack server"""
    
    def __init__(self, base_url=None):
        self.base_url = base_url.rstrip('/') if base_url else None
    
    def set_base_url(self, url):
        self.base_url = url.rstrip('/') if url else None
    
    def verify_token(self, token, callback):
        if not self.base_url:
            callback({'valid': False, 'error': 'No server URL set'})
            return
        
        url = f"{self.base_url}/api/user_info/{token}"
        req = UrlRequest(
            url,
            on_success=lambda req, result: self._on_verify_success(result, callback, token),
            on_failure=lambda req, result: self._on_verify_failure(result, callback),
            on_error=lambda req, error: self._on_verify_error(error, callback),
            timeout=10,
            method='GET'
        )
    
    def _on_verify_success(self, result, callback, token):
        if result:
            callback({
                'valid': True,
                'user_info': result,
                'token': token
            })
        else:
            callback({'valid': False, 'error': 'Invalid response from server'})
    
    def _on_verify_failure(self, result, callback):
        if result and result.status_code == 403:
            callback({'valid': False, 'error': 'Token is invalid or expired'})
        else:
            callback({'valid': False, 'error': f'Server error: {result.status_code if result else "unknown"}'})
    
    def _on_verify_error(self, error, callback):
        callback({'valid': False, 'error': f'Connection error: {str(error)}'})
    
    def register_user(self, full_name, email, organisation, callback):
        if not self.base_url:
            callback({'success': False, 'error': 'No server URL set'})
            return
        
        url = f"{self.base_url}/api/register"
        req = UrlRequest(
            url,
            on_success=lambda req, result: callback(result),
            on_failure=lambda req, result: callback({'success': False, 'error': f'Server error: {result.status_code if result else "unknown"}'}),
            on_error=lambda req, error: callback({'success': False, 'error': f'Connection error: {str(error)}'}),
            timeout=15,
            method='POST',
            req_body=json.dumps({
                'full_name': full_name,
                'email': email,
                'organisation': organisation
            }),
            req_headers={'Content-Type': 'application/json'}
        )
    
    def get_health(self, callback):
        if not self.base_url:
            callback({'status': 'unknown'})
            return
        
        url = f"{self.base_url}/health"
        req = UrlRequest(
            url,
            on_success=lambda req, result: callback(result),
            on_failure=lambda req, result: callback({'status': 'unhealthy'}),
            on_error=lambda req, error: callback({'status': 'unreachable'}),
            timeout=5,
            method='GET'
        )

# ==================== MAIN SCREENS ====================
class ConnectScreen(Screen):
    """Connection/Verification screen"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        
        # Scroll view for content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Title
        title_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        title = Label(
            text="🔑 Connect to MzindaTrack",
            font_size=dp(20),
            bold=True,
            color=(0.39, 0.49, 0.92, 1),  # #667eea
            size_hint=(1, None),
            height=dp(40),
            halign='center'
        )
        title_container.add_widget(title)
        content.add_widget(title_container)
        
        # Subtitle
        subtitle = Label(
            text="Enter your MzindaTrack token or the public URL you received via email.",
            font_size=dp(13),
            color=(0.6, 0.65, 0.7, 1),
            size_hint=(1, None),
            height=dp(60),
            halign='center',
            valign='middle',
            text_size=(Window.width - dp(32), None)
        )
        content.add_widget(subtitle)
        
        # Server URL group
        server_group = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, height=dp(160))
        server_label = Label(
            text="Server URL",
            font_size=dp(14),
            bold=True,
            size_hint=(1, None),
            height=dp(25),
            halign='left'
        )
        server_group.add_widget(server_label)
        
        server_input_layout = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(45))
        self.server_input = TextInput(
            multiline=False,
            hint_text="Enter server URL",
            size_hint=(0.6, 1),
            background_color=(0.08, 0.08, 0.12, 1),
            foreground_color=(0.88, 0.9, 0.93, 1)
        )
        server_input_layout.add_widget(self.server_input)
        
        # Spinner for default servers
        self.server_spinner = Spinner(
            text='Select default...',
            values=['Select default...'] + DEFAULT_SERVER_URLS,
            size_hint=(0.3, 1),
            background_color=(0.08, 0.08, 0.12, 1),
            color=(0.88, 0.9, 0.93, 1)
        )
        self.server_spinner.bind(text=self.on_server_selected)
        server_input_layout.add_widget(self.server_spinner)
        
        # Test button
        self.test_btn = Button(
            text="Test",
            size_hint=(0.2, 1),
            background_color=(0.3, 0.3, 0.35, 1),
            color=(1, 1, 1, 1)
        )
        self.test_btn.bind(on_press=self.test_server)
        server_input_layout.add_widget(self.test_btn)
        
        server_group.add_widget(server_input_layout)
        content.add_widget(server_group)
        
        # Token group
        token_group = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, height=dp(110))
        token_label = Label(
            text="Token or Access URL",
            font_size=dp(14),
            bold=True,
            size_hint=(1, None),
            height=dp(25),
            halign='left'
        )
        token_group.add_widget(token_label)
        
        token_input_layout = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(45))
        self.token_input = TextInput(
            multiline=False,
            hint_text="Paste your token or URL here",
            size_hint=(0.85, 1),
            background_color=(0.08, 0.08, 0.12, 1),
            foreground_color=(0.88, 0.9, 0.93, 1)
        )
        token_input_layout.add_widget(self.token_input)
        
        self.paste_btn = Button(
            text="📋",
            size_hint=(0.15, 1),
            background_color=(0.2, 0.2, 0.25, 1),
            color=(1, 1, 1, 1)
        )
        self.paste_btn.bind(on_press=self.paste_token)
        token_input_layout.add_widget(self.paste_btn)
        
        token_group.add_widget(token_input_layout)
        content.add_widget(token_group)
        
        # Auto-connect toggle
        auto_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.auto_connect_check = ToggleButton(
            text="🔄 Auto-connect on startup",
            state='down',
            size_hint=(1, None),
            height=dp(36),
            background_color=(0.15, 0.15, 0.2, 1)
        )
        self.auto_connect_check.bind(state=self.toggle_auto_connect)
        auto_layout.add_widget(self.auto_connect_check)
        content.add_widget(auto_layout)
        
        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(50))
        self.verify_btn = Button(
            text="🔐 Verify Token",
            size_hint=(0.6, 1),
            background_color=(0.4, 0.49, 0.92, 1),  # #667eea
            color=(1, 1, 1, 1)
        )
        self.verify_btn.bind(on_press=self.verify_token)
        btn_layout.add_widget(self.verify_btn)
        
        self.register_btn = Button(
            text="📝 Register",
            size_hint=(0.4, 1),
            background_color=(0.3, 0.3, 0.35, 1),
            color=(1, 1, 1, 1)
        )
        self.register_btn.bind(on_press=self.open_registration)
        btn_layout.add_widget(self.register_btn)
        content.add_widget(btn_layout)
        
        # Progress
        self.progress = ProgressBar(
            value=0,
            size_hint=(1, None),
            height=dp(6)
        )
        self.progress.opacity = 0
        content.add_widget(self.progress)
        
        # Status message
        self.status_label = Label(
            text="",
            font_size=dp(13),
            color=(0.6, 0.65, 0.7, 1),
            size_hint=(1, None),
            height=dp(30),
            halign='center',
            valign='middle'
        )
        content.add_widget(self.status_label)
        
        # Recent tokens
        recent_group = BoxLayout(orientation='vertical', spacing=dp(4), size_hint_y=None, height=dp(80))
        recent_label = Label(
            text="Recent Connections",
            font_size=dp(14),
            bold=True,
            size_hint=(1, None),
            height=dp(25),
            halign='left'
        )
        recent_group.add_widget(recent_label)
        self.recent_list = Label(
            text="No recent connections",
            font_size=dp(12),
            color=(0.4, 0.45, 0.5, 1),
            size_hint=(1, None),
            height=dp(50),
            halign='center',
            valign='middle'
        )
        recent_group.add_widget(self.recent_list)
        content.add_widget(recent_group)
        
        # Info footer
        footer = Label(
            text="🔐 MzindaTrack - GPS yathu, Chitetezo chathu\nSecure GPS tracking with 2-meter precision",
            font_size=dp(10),
            color=(0.4, 0.45, 0.5, 1),
            size_hint=(1, None),
            height=dp(50),
            halign='center',
            valign='middle'
        )
        content.add_widget(footer)
        
        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)
    
    def on_server_selected(self, spinner, text):
        if text and text != 'Select default...':
            self.server_input.text = text
            self.app.api.set_base_url(text)
    
    def test_server(self, instance):
        url = self.server_input.text.strip()
        if not url:
            self.show_message("Warning", "Please enter a server URL", "warning")
            return
        
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url
            self.server_input.text = url
        
        self.app.api.set_base_url(url)
        self.test_btn.text = "Testing..."
        self.test_btn.disabled = True
        
        def on_result(result):
            self.test_btn.text = "Test"
            self.test_btn.disabled = False
            if result.get('status') == 'healthy':
                self.app.status_bar.status_text = "✅ Connected to server"
                self.app.status_bar.status_color = "#4CAF50"
                self.app.header.status_indicator = "✅"
                self.app.header.status_tooltip = "Connected to server"
                self.show_message("Connection Test", "✅ Successfully connected to MzindaTrack server!", "success")
            else:
                self.app.status_bar.status_text = "❌ Could not connect to server"
                self.app.status_bar.status_color = "#f44336"
                self.app.header.status_indicator = "⚪"
                self.app.header.status_tooltip = "Disconnected"
                self.show_message("Connection Failed", "❌ Could not connect to the server. Please check the URL.", "error")
        
        self.app.api.get_health(on_result)
    
    def paste_token(self, instance):
        # On mobile, we'll use clipboard
        # Kivy doesn't have direct clipboard access on all platforms
        # We'll use the text input's paste functionality
        self.token_input.paste()
    
    def verify_token(self, instance):
        token = self.token_input.text.strip()
        if not token:
            self.show_message("Warning", "Please enter your token", "warning")
            return
        
        server_url = self.server_input.text.strip()
        if not server_url:
            self.show_message("Warning", "Please enter the server URL", "warning")
            return
        
        if not server_url.startswith('http://') and not server_url.startswith('https://'):
            server_url = 'http://' + server_url
            self.server_input.text = server_url
        
        self.app.api.set_base_url(server_url)
        
        self.verify_btn.disabled = True
        self.register_btn.disabled = True
        self.progress.opacity = 1
        self.progress.value = 0
        self.status_label.text = "Verifying token..."
        self.status_label.color = (0.39, 0.49, 0.92, 1)
        
        Clock.schedule_interval(lambda dt: self.progress.value < 90 and setattr(self.progress, 'value', self.progress.value + 10), 0.2)
        
        def on_verify(result):
            Clock.unschedule(lambda dt: None)
            self.progress.value = 100
            self.verify_btn.disabled = False
            self.register_btn.disabled = False
            self.progress.opacity = 0
            
            if result.get('valid'):
                self.app.on_verification_success(result)
            else:
                self.app.on_verification_failure(result)
        
        self.app.api.verify_token(token, on_verify)
    
    def open_registration(self, instance):
        self.app.show_registration_dialog()
    
    def toggle_auto_connect(self, instance, state):
        enabled = state == 'down'
        self.app.auto_connect_enabled = enabled
        if enabled:
            if not self.app.verified:
                self.app.start_auto_connect()
        else:
            self.app.stop_auto_connect()
        self.app.save_settings()
    
    def show_message(self, title, message, msg_type="info"):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        msg_label = Label(
            text=message,
            font_size=dp(14),
            halign='center',
            valign='middle',
            size_hint=(1, None),
            height=dp(100),
            text_size=(Window.width - dp(80), None)
        )
        content.add_widget(msg_label)
        
        close_btn = Button(
            text="OK",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.4, 0.49, 0.92, 1),
            color=(1, 1, 1, 1)
        )
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.85, None),
            height=dp(200),
            auto_dismiss=True
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()


class ViewScreen(Screen):
    """Web view screen"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical')
        self.web_view = MobileWebView(self.app)
        layout.add_widget(self.web_view)
        self.add_widget(layout)


class AccountScreen(Screen):
    """Account information screen"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        
        # Card background
        card = BoxLayout(
            orientation='vertical',
            padding=dp(16),
            spacing=dp(8),
            size_hint=(1, None),
            height=dp(250)
        )
        card.canvas.before.clear()
        from kivy.graphics import Color, RoundedRectangle
        with card.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=self._update_rect, size=self._update_rect)
        
        self.name_label = Label(
            text="Not logged in",
            font_size=dp(18),
            bold=True,
            color=(0.88, 0.9, 0.93, 1),
            size_hint=(1, None),
            height=dp(35),
            halign='center'
        )
        card.add_widget(self.name_label)
        
        self.email_label = Label(
            text="",
            font_size=dp(14),
            color=(0.6, 0.65, 0.7, 1),
            size_hint=(1, None),
            height=dp(30),
            halign='center'
        )
        card.add_widget(self.email_label)
        
        self.org_label = Label(
            text="",
            font_size=dp(14),
            color=(0.6, 0.65, 0.7, 1),
            size_hint=(1, None),
            height=dp(30),
            halign='center'
        )
        card.add_widget(self.org_label)
        
        self.status_label = Label(
            text="Status: Disconnected",
            font_size=dp(14),
            color=(1, 0.6, 0, 1),
            size_hint=(1, None),
            height=dp(30),
            halign='center'
        )
        card.add_widget(self.status_label)
        
        # Disconnect button
        self.disconnect_btn = Button(
            text="🚪 Disconnect",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            disabled=True
        )
        self.disconnect_btn.bind(on_press=self.app.disconnect)
        card.add_widget(self.disconnect_btn)
        
        layout.add_widget(card)
        
        # Info footer
        footer = Label(
            text="⛶ Full screen available in web view",
            font_size=dp(11),
            color=(0.4, 0.45, 0.5, 1),
            size_hint=(1, None),
            height=dp(30),
            halign='center'
        )
        layout.add_widget(footer)
        
        self.add_widget(layout)
        self.card = card
    
    def _update_rect(self, instance, value):
        instance.canvas.before.clear()
        from kivy.graphics import Color, RoundedRectangle
        with instance.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[dp(12)])


class RegistrationPopup(Popup):
    """Registration dialog"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.title = "Register for MzindaTrack"
        self.size_hint = (0.85, None)
        self.height = dp(400)
        self.auto_dismiss = True
        
        self.build_ui()
    
    def build_ui(self):
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(12))
        
        # Header
        header = Label(
            text="🎯 Register for MzindaTrack\nGPS yathu, Chitetezo chathu",
            font_size=dp(16),
            bold=True,
            color=(0.39, 0.49, 0.92, 1),
            size_hint=(1, None),
            height=dp(60),
            halign='center'
        )
        content.add_widget(header)
        
        # Form
        form = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, height=dp(160))
        
        self.name_input = TextInput(
            multiline=False,
            hint_text="Full Name",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.08, 0.08, 0.12, 1),
            foreground_color=(0.88, 0.9, 0.93, 1)
        )
        form.add_widget(self.name_input)
        
        self.email_input = TextInput(
            multiline=False,
            hint_text="Email Address",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.08, 0.08, 0.12, 1),
            foreground_color=(0.88, 0.9, 0.93, 1)
        )
        form.add_widget(self.email_input)
        
        self.org_input = TextInput(
            multiline=False,
            hint_text="Organisation (Optional)",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.08, 0.08, 0.12, 1),
            foreground_color=(0.88, 0.9, 0.93, 1)
        )
        form.add_widget(self.org_input)
        
        content.add_widget(form)
        
        # Info
        info = Label(
            text="📌 You will receive a payment link via email.\nAfter payment, your access will be activated.",
            font_size=dp(11),
            color=(0.6, 0.65, 0.7, 1),
            size_hint=(1, None),
            height=dp(50),
            halign='center'
        )
        content.add_widget(info)
        
        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        
        self.register_btn = Button(
            text="✅ Register",
            size_hint=(0.6, 1),
            background_color=(0.3, 0.75, 0.35, 1),
            color=(1, 1, 1, 1)
        )
        self.register_btn.bind(on_press=self.register)
        
        self.cancel_btn = Button(
            text="Cancel",
            size_hint=(0.4, 1),
            background_color=(0.3, 0.3, 0.35, 1),
            color=(1, 1, 1, 1)
        )
        self.cancel_btn.bind(on_press=self.dismiss)
        
        btn_layout.add_widget(self.register_btn)
        btn_layout.add_widget(self.cancel_btn)
        content.add_widget(btn_layout)
        
        self.status_label = Label(
            text="",
            font_size=dp(12),
            color=(0.6, 0.65, 0.7, 1),
            size_hint=(1, None),
            height=dp(25),
            halign='center'
        )
        content.add_widget(self.status_label)
        
        self.content = content
    
    def register(self, instance):
        name = self.name_input.text.strip()
        email = self.email_input.text.strip()
        org = self.org_input.text.strip()
        
        if not name:
            self.status_label.text = "❌ Please enter your full name"
            self.status_label.color = (0.8, 0.2, 0.2, 1)
            return
        
        if not email or '@' not in email:
            self.status_label.text = "❌ Please enter a valid email"
            self.status_label.color = (0.8, 0.2, 0.2, 1)
            return
        
        self.register_btn.disabled = True
        self.register_btn.text = "Registering..."
        self.status_label.text = "⏳ Contacting server..."
        self.status_label.color = (0.39, 0.49, 0.92, 1)
        
        def on_result(result):
            self.register_btn.disabled = False
            self.register_btn.text = "✅ Register"
            
            if result.get('success'):
                self.status_label.text = f"✅ {result.get('message', 'Registration successful')}"
                self.status_label.color = (0.3, 0.75, 0.35, 1)
                
                # Show payment link
                if result.get('payment_url'):
                    self.app.show_message(
                        "Registration Successful",
                        f"Payment link sent to {email}\n\nTap OK to open payment page.",
                        "success"
                    )
                    # Open payment URL
                    Clock.schedule_once(lambda dt: webbrowser.open(result['payment_url']), 1)
                
                Clock.schedule_once(lambda dt: self.dismiss(), 3)
            else:
                self.status_label.text = f"❌ {result.get('error', 'Registration failed')}"
                self.status_label.color = (0.8, 0.2, 0.2, 1)
        
        self.app.api.register_user(name, email, org, on_result)

# ==================== MAIN APP ====================
class MzindaTrackApp(App):
    """Main MzindaTrack Mobile Application"""
    
    def build(self):
        self.title = APP_NAME
        self.api = MzindaTrackAPI()
        self.verified = False
        self.current_token = None
        self.user_info = None
        self.auto_connect_enabled = True
        self.auto_connect_active = False
        
        # Setup theme
        self.setup_theme()
        
        # Settings store
        self.settings = SettingsStore()
        
        # Main screen manager
        self.screen_manager = ScreenManager(transition=SlideTransition())
        
        # Create screens
        self.connect_screen = ConnectScreen(self, name='connect')
        self.view_screen = ViewScreen(self, name='view')
        self.account_screen = AccountScreen(self, name='account')
        
        self.screen_manager.add_widget(self.connect_screen)
        self.screen_manager.add_widget(self.view_screen)
        self.screen_manager.add_widget(self.account_screen)
        
        # Main layout with header, content, status bar
        main_layout = BoxLayout(orientation='vertical')
        
        # Header
        self.header = Header(self)
        self.header.title = APP_NAME
        main_layout.add_widget(self.header)
        
        # Content
        main_layout.add_widget(self.screen_manager)
        
        # Status bar
        self.status_bar = StatusBar()
        self.status_bar.status_text = "Ready"
        main_layout.add_widget(self.status_bar)
        
        # Load settings
        self.load_settings()
        
        # Start auto-connect
        if self.auto_connect_enabled:
            Clock.schedule_once(lambda dt: self.start_auto_connect(), 1.5)
        
        return main_layout
    
    def setup_theme(self):
        """Setup application theme"""
        from kivy.core.window import Window
        Window.clearcolor = (0.04, 0.06, 0.12, 1)  # #0a0f1e
        Window.size = (400, 720)  # Mobile default
    
    def load_settings(self):
        """Load settings from storage"""
        settings = self.settings.get('settings', {})
        
        if settings:
            self.auto_connect_enabled = settings.get('auto_connect_enabled', True)
            
            server_url = settings.get('server_url', '')
            if server_url:
                self.connect_screen.server_input.text = server_url
                self.api.set_base_url(server_url)
            
            recent_tokens = settings.get('recent_tokens', [])
            if recent_tokens:
                self.connect_screen.recent_list.text = "\n".join([
                    f"• {t[:20]}..." if len(t) > 20 else f"• {t}"
                    for t in recent_tokens[:5]
                ])
                self.connect_screen.recent_list.color = (0.39, 0.49, 0.92, 1)
        
        # Set first default server if none set
        if not self.api.base_url:
            self.connect_screen.server_input.text = DEFAULT_SERVER_URLS[0]
            self.api.set_base_url(DEFAULT_SERVER_URLS[0])
        
        self.connect_screen.auto_connect_check.state = 'down' if self.auto_connect_enabled else 'normal'
    
    def save_settings(self):
        """Save settings to storage"""
        settings = {
            'auto_connect_enabled': self.auto_connect_enabled,
            'server_url': self.connect_screen.server_input.text.strip(),
            'recent_tokens': getattr(self, 'recent_tokens', [])[:5]
        }
        self.settings.put('settings', settings)
    
    def start_auto_connect(self):
        """Start auto-connect process"""
        if not self.auto_connect_enabled or self.verified:
            return
        
        if self.auto_connect_active:
            return
        
        self.auto_connect_active = True
        self.header.status_indicator = "🔄"
        self.header.status_tooltip = "Auto-connecting..."
        self.status_bar.status_text = "🔄 Auto-connecting..."
        self.status_bar.status_color = "#64ffda"
        
        # Get stored token
        token = self.settings.get('token', {}).get('value', '')
        if not token:
            self.auto_connect_active = False
            self.header.status_indicator = "⚪"
            self.status_bar.status_text = "No saved token"
            return
        
        # Set token and verify
        self.connect_screen.token_input.text = token
        
        # Check if server URL is set
        server_url = self.connect_screen.server_input.text.strip()
        if server_url:
            self.api.set_base_url(server_url)
        
        # Attempt verification
        self.connect_screen.verify_btn.disabled = True
        self.status_bar.status_text = "🔄 Verifying saved token..."
        
        def on_verify(result):
            self.auto_connect_active = False
            
            if result.get('valid'):
                self.on_verification_success(result)
                self.status_bar.status_text = "✅ Auto-connected successfully"
                self.status_bar.status_color = "#4CAF50"
                self.header.status_indicator = "✅"
                self.header.status_tooltip = "Connected"
            else:
                # Retry with defaults
                for url in DEFAULT_SERVER_URLS:
                    if url != self.api.base_url:
                        self.api.set_base_url(url)
                        self.connect_screen.server_input.text = url
                        self.verify_token_with_retry(token)
                        return
                
                self.on_verification_failure(result, auto=True)
                self.status_bar.status_text = "⚠️ Auto-connect failed"
                self.status_bar.status_color = "#FF9800"
                self.header.status_indicator = "⚪"
                self.header.status_tooltip = "Disconnected"
            
            self.connect_screen.verify_btn.disabled = False
        
        self.api.verify_token(token, on_verify)
    
    def verify_token_with_retry(self, token):
        """Retry verification with different server"""
        def on_verify(result):
            if result.get('valid'):
                self.on_verification_success(result)
                self.status_bar.status_text = "✅ Auto-connected successfully"
                self.status_bar.status_color = "#4CAF50"
                self.header.status_indicator = "✅"
                self.header.status_tooltip = "Connected"
            else:
                self.on_verification_failure(result, auto=True)
                self.status_bar.status_text = "⚠️ Auto-connect failed"
                self.status_bar.status_color = "#FF9800"
                self.header.status_indicator = "⚪"
                self.header.status_tooltip = "Disconnected"
            self.auto_connect_active = False
            self.connect_screen.verify_btn.disabled = False
        
        self.api.verify_token(token, on_verify)
    
    def stop_auto_connect(self):
        """Stop auto-connect process"""
        self.auto_connect_active = False
        self.status_bar.status_text = "Auto-connect stopped"
        self.header.status_indicator = "⚪"
        self.header.status_tooltip = "Disconnected"
    
    def on_verification_success(self, result):
        """Handle successful verification"""
        self.verified = True
        self.current_token = result.get('token')
        self.user_info = result.get('user_info', {})
        
        # Save token
        self.settings.put('token', {'value': self.current_token})
        
        # Add to recent tokens
        if not hasattr(self, 'recent_tokens'):
            self.recent_tokens = []
        if self.current_token not in self.recent_tokens:
            self.recent_tokens.insert(0, self.current_token)
            self.recent_tokens = self.recent_tokens[:5]
            self.save_settings()
        
        # Update connect screen
        self.connect_screen.status_label.text = "✅ Token verified successfully!"
        self.connect_screen.status_label.color = (0.3, 0.75, 0.35, 1)
        self.connect_screen.progress.opacity = 0
        
        # Update account screen
        user = self.user_info
        self.account_screen.name_label.text = f"👤 {user.get('full_name', 'User')}"
        self.account_screen.email_label.text = f"📧 {user.get('email', '')}"
        if user.get('organisation'):
            self.account_screen.org_label.text = f"🏢 {user['organisation']}"
        self.account_screen.status_label.text = "✅ Account Active"
        self.account_screen.status_label.color = (0.3, 0.75, 0.35, 1)
        self.account_screen.disconnect_btn.disabled = False
        
        # Update header
        self.header.status_indicator = "✅"
        self.header.status_tooltip = "Connected - Access granted"
        self.header.page_name = "Connected"
        
        # Update status bar
        self.status_bar.status_text = "✅ Access granted - Welcome!"
        self.status_bar.status_color = "#4CAF50"
        
        # Enable menu actions
        self.account_screen.disconnect_btn.disabled = False
    
    def on_verification_failure(self, result, auto=False):
        """Handle verification failure"""
        self.verified = False
        
        # Update connect screen
        error_msg = result.get('error', 'Invalid token')
        self.connect_screen.status_label.text = f"❌ {error_msg}"
        self.connect_screen.status_label.color = (0.8, 0.2, 0.2, 1)
        self.connect_screen.progress.opacity = 0
        
        # Update status
        self.header.status_indicator = "⚪"
        self.header.status_tooltip = "Disconnected"
        self.status_bar.status_text = "❌ Verification failed"
        self.status_bar.status_color = "#f44336"
        
        # Show message if not auto
        if not auto:
            self.show_message(
                "Verification Failed",
                f"❌ {error_msg}\n\nPlease check your token and try again.",
                "error"
            )
    
    def show_registration_dialog(self):
        """Show registration dialog"""
        server_url = self.connect_screen.server_input.text.strip()
        if not server_url:
            self.show_message("Warning", "Please enter the server URL first", "warning")
            return
        
        if not server_url.startswith('http://') and not server_url.startswith('https://'):
            server_url = 'http://' + server_url
            self.connect_screen.server_input.text = server_url
        
        self.api.set_base_url(server_url)
        
        dialog = RegistrationPopup(self)
        dialog.open()
    
    def open_map(self):
        """Open map view"""
        if not self.verified or not self.current_token:
            self.show_message("Warning", "Please verify your token first", "warning")
            return
        
        url = f"{self.api.base_url}/map/{self.current_token}"
        self.view_screen.web_view.set_home_url(url)
        self.view_screen.web_view.load_url(url)
        self.screen_manager.current = 'view'
        self.header.page_name = "🗺️ Map"
        self.status_bar.status_text = "Loading map..."
        self.status_bar.status_color = "#8892b0"
    
    def open_phone(self):
        """Open phone tracker"""
        if not self.verified or not self.current_token:
            self.show_message("Warning", "Please verify your token first", "warning")
            return
        
        url = f"{self.api.base_url}/phone/{self.current_token}"
        self.view_screen.web_view.set_home_url(url)
        self.view_screen.web_view.load_url(url)
        self.screen_manager.current = 'view'
        self.header.page_name = "📱 Phone Tracker"
        self.status_bar.status_text = "Loading phone tracker..."
        self.status_bar.status_color = "#8892b0"
    
    def switch_page(self, page):
        """Switch to a specific page"""
        if page == 'connect':
            self.screen_manager.current = 'connect'
            self.header.page_name = "Connect"
        elif page == 'view':
            self.screen_manager.current = 'view'
            self.header.page_name = "View"
        elif page == 'account':
            self.screen_manager.current = 'account'
            self.header.page_name = "Account"
    
    def disconnect(self, instance):
        """Disconnect from server"""
        if not self.verified:
            return
        
        # Show confirmation
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        msg = Label(
            text="Are you sure you want to disconnect from MzindaTrack?",
            font_size=dp(14),
            halign='center',
            valign='middle',
            size_hint=(1, None),
            height=dp(60)
        )
        content.add_widget(msg)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        yes_btn = Button(
            text="Yes",
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        no_btn = Button(
            text="No",
            background_color=(0.3, 0.3, 0.35, 1),
            color=(1, 1, 1, 1)
        )
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title="Disconnect",
            content=content,
            size_hint=(0.8, None),
            height=dp(150),
            auto_dismiss=True
        )
        
        def on_yes(instance):
            popup.dismiss()
            self._do_disconnect()
        
        def on_no(instance):
            popup.dismiss()
        
        yes_btn.bind(on_press=on_yes)
        no_btn.bind(on_press=on_no)
        popup.open()
    
    def _do_disconnect(self):
        """Perform disconnection"""
        self.verified = False
        self.current_token = None
        self.user_info = None
        
        # Update account screen
        self.account_screen.name_label.text = "Not logged in"
        self.account_screen.email_label.text = ""
        self.account_screen.org_label.text = ""
        self.account_screen.status_label.text = "Status: Disconnected"
        self.account_screen.status_label.color = (1, 0.6, 0, 1)
        self.account_screen.disconnect_btn.disabled = True
        
        # Update header
        self.header.status_indicator = "⚪"
        self.header.status_tooltip = "Disconnected"
        self.header.page_name = "Connect"
        
        # Update status bar
        self.status_bar.status_text = "Disconnected"
        self.status_bar.status_color = "#8892b0"
        
        # Switch to connect screen
        self.screen_manager.current = 'connect'
        
        # Clear token from storage
        self.settings.put('token', {'value': ''})
        
        # Restart auto-connect if enabled
        if self.auto_connect_enabled:
            Clock.schedule_once(lambda dt: self.start_auto_connect(), 2)
    
    def show_message(self, title, message, msg_type="info"):
        """Show a message popup"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        msg_label = Label(
            text=message,
            font_size=dp(14),
            halign='center',
            valign='middle',
            size_hint=(1, None),
            height=dp(150 if len(message) > 50 else 80),
            text_size=(Window.width - dp(80), None)
        )
        content.add_widget(msg_label)
        
        close_btn = Button(
            text="OK",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.4, 0.49, 0.92, 1),
            color=(1, 1, 1, 1)
        )
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.85, None),
            height=dp(250 if len(message) > 50 else 180),
            auto_dismiss=True
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()
    
    def on_pause(self):
        """Handle app pause (Android)"""
        return True
    
    def on_resume(self):
        """Handle app resume (Android)"""
        pass

# ==================== MAIN ====================
if __name__ == "__main__":
    MzindaTrackApp().run()
