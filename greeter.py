#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


import os
import sys
import subprocess
import json
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
from gi.repository import Gdk, Pango


class GreeterApp:
    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        try:
            self.config = json.load(open(os.path.join(dir_path, "config.json")))
        except Exception as e:
            print(f"Failed to read config.json: {e}")
            sys.exit(1)

        Gtk.init()
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(dir_path, "greeter.glade"))
        self.main_window = self.builder.get_object("main_window")
        self.help_window = self.builder.get_object("help_window")
        self.pincode_entry = self.builder.get_object("pincode_entry")
        self.pincode_table = self.builder.get_object("pincode_table")
        self.control_panel = self.builder.get_object("control_panel")
        self.pincode_entry.override_font(Pango.FontDescription("Sans Bold 36"))
        self.process = None
        self.timeout_id = GLib.timeout_add_seconds(1, self.timeout, None)
        self.screen = Gdk.Screen.get_default()
        self.display = Gdk.Display.get_default()
        if self.main_window:
            self.control_panel.set_visible(False)
            self.main_window.set_size_request(
                self.screen.get_width(), self.screen.get_height()
            )
            self.screen.get_root_window().set_cursor(
                Gdk.Cursor.new_from_name(
                    self.display, self.config.get("cursor", "default")
                )
            )
        if self.help_window:
            if self.config.get("help_text"):
                self.help_text = self.builder.get_object("help_text")
                self.help_text.set_label(self.config.get("help_text"))
        self.builder.connect_signals(self)

    def Run(self):
        settings = Gtk.Settings.get_default()
        settings.props.gtk_button_images = True
        self.main_window.show()
        Gtk.main()

    def terminate_session(self, widget):
        self.control_panel.set_visible(False)
        self.pincode_table.set_visible(True)
        self.main_window.move(0, 0)
        self.main_window.set_size_request(
            self.screen.get_width(), self.screen.get_height()
        )
        if self.process:
            self.process.terminate()
            self.process = None

    def timeout(self, _):
        if self.main_window:
            if not self.help_window.is_visible():
                self.toggle_window(self.main_window, True)
            return True
        return False

    def check_pincode(self, widget, *args):
        rdp_servers = self.config.get("rdp_servers")
        for rdp_server in rdp_servers:
            if self.pincode_entry.get_text() == rdp_server.get("pincode"):
                self.pincode_entry.set_text("")
                self.pincode_table.set_visible(False)
                self.control_panel.set_visible(True)
                self.main_window.set_size_request(50, 50)
                self.main_window.move(0, self.screen.get_height() - 50)
                self.process = subprocess.Popen(
                    [
                        "xfreerdp",
                        "/f",
                        "/cert-ignore",
                        "+auto-reconnect",
                        "/auto-reconnect-max-retries:20",
                        "+bitmap-cache",
                        "/gdi:hw",
                        "/v:" + rdp_server.get("server"),
                        "/u:" + rdp_server.get("user"),
                        "/p:" + rdp_server.get("password"),
                        *rdp_server.get("additional_parameters", []),
                    ]
                )

    def clear_pass(self, widget, *args):
        self.pincode_entry.set_text("")

    def num_press(self, widget, *args):
        number = widget.get_child().get_text()
        self.pincode_entry.set_text(self.pincode_entry.get_text() + number)

    def sys_poweroff(self, widget, *args):
        os.system("systemctl poweroff")

    def sys_reboot(self, widget, *args):
        os.system("systemctl reboot")

    def on_help_clicked(self, widget, *args):
        self.toggle_window(self.help_window, True)

    def on_help_close_clicked(self, widget, *args):
        self.toggle_window(self.help_window, False)

    def toggle_window(self, window, visibility):
        window.set_visible(visibility)
        window.set_keep_above(visibility)
        window.set_modal(visibility)

    def on_destroy(self, widget, *args):
        GLib.source_remove(self.timeout_id)
        Gtk.main_quit()
        sys.exit(0)


if __name__ == "__main__":
    app = GreeterApp()
    app.Run()
