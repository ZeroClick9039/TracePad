"""
UI Components - Additional UI components for the GhostKey editor.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time

class StatusBar:
    """Status bar component for displaying application status."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        self.label = ttk.Label(
            self.frame,
            textvariable=self.status_var,
            anchor=tk.W,
            padding=(5, 2)
        )
        self.label.pack(fill=tk.X)
        
        # Timer for clearing temporary messages
        self.clear_timer = None
    
    def pack(self, **kwargs):
        """Pack the status bar frame."""
        self.frame.pack(**kwargs)
    
    def set_message(self, message, timeout=3000):
        """Set a status message with optional timeout."""
        self.status_var.set(message)
        
        # Clear any existing timer
        if self.clear_timer:
            self.frame.after_cancel(self.clear_timer)
        
        # Set new timer to clear message
        if timeout > 0:
            self.clear_timer = self.frame.after(timeout, lambda: self.status_var.set("Ready"))
    
    def set_permanent_message(self, message):
        """Set a permanent status message."""
        if self.clear_timer:
            self.frame.after_cancel(self.clear_timer)
            self.clear_timer = None
        self.status_var.set(message)


class HoverManager:
    """Manages hover effects for text input source visualization."""
    
    def __init__(self, text_widget, text_tracker):
        self.text_widget = text_widget
        self.text_tracker = text_tracker
        self.current_hover_tag = None
        self.hover_active = False
        
        # Configure highlight tags
        self.text_widget.tag_configure("hover_typed", background="#90EE90", foreground="#000000")  # Light green
        self.text_widget.tag_configure("hover_pasted", background="#FFB6C1", foreground="#000000")  # Light red
        
        # Bind hover events
        self.setup_hover_bindings()
    
    def setup_hover_bindings(self):
        """Setup mouse hover event bindings."""
        self.text_widget.bind("<Motion>", self.on_mouse_motion)
        self.text_widget.bind("<Leave>", self.on_mouse_leave)
        self.text_widget.bind("<Button-1>", self.on_mouse_click)
    
    def on_mouse_motion(self, event):
        """Handle mouse motion over text."""
        try:
            # Get mouse position in text widget
            x, y = event.x, event.y
            index_str = self.text_widget.index(f"@{x},{y}")
            
            # Get input source at this position
            source = self.text_tracker.get_source_at_position(index_str)
            
            if source:
                self.show_hover_highlight(index_str, source)
            else:
                self.clear_hover_highlight()
                
        except tk.TclError:
            # Mouse is outside text area
            self.clear_hover_highlight()
        except Exception as e:
            print(f"Error in mouse motion handler: {e}")
    
    def on_mouse_leave(self, event):
        """Handle mouse leaving text widget."""
        self.clear_hover_highlight()
    
    def on_mouse_click(self, event):
        """Handle mouse click to clear hover effects."""
        self.clear_hover_highlight()
    
    def show_hover_highlight(self, position, source):
        """Show hover highlight for a specific position and source."""
        try:
            # Clear previous highlight
            self.clear_hover_highlight()
            
            # Find the range that contains this position
            hover_range = self.find_hover_range(position, source)
            
            if hover_range:
                start_pos = self.text_tracker._index_to_pos(hover_range['start'])
                end_pos = self.text_tracker._index_to_pos(hover_range['end'])
                
                # Apply appropriate tag
                if source == 'manual':
                    tag_name = "hover_typed"
                    self.current_hover_tag = tag_name
                elif source == 'pasted':
                    tag_name = "hover_pasted"
                    self.current_hover_tag = tag_name
                else:
                    return
                
                # Apply the highlight
                self.text_widget.tag_add(tag_name, start_pos, end_pos)
                self.hover_active = True
                
        except Exception as e:
            print(f"Error showing hover highlight: {e}")
    
    def find_hover_range(self, position, source):
        """Find the complete range around the position with the same source."""
        try:
            pos_index = self.text_tracker._pos_to_index(position)
            
            # Find the range that contains this position
            with self.text_tracker.lock:
                for range_info in self.text_tracker.input_ranges:
                    if (range_info['start'] <= pos_index < range_info['end'] and 
                        range_info['source'] == source):
                        return range_info
            
            return None
        except Exception as e:
            print(f"Error finding hover range: {e}")
            return None
    
    def clear_hover_highlight(self):
        """Clear all hover highlights."""
        try:
            if self.current_hover_tag and self.hover_active:
                self.text_widget.tag_remove(self.current_hover_tag, "1.0", tk.END)
                self.current_hover_tag = None
                self.hover_active = False
        except Exception as e:
            print(f"Error clearing hover highlight: {e}")


class TooltipManager:
    """Manages tooltips for enhanced user feedback."""
    
    def __init__(self, widget):
        self.widget = widget
        self.tooltip_window = None
        self.tooltip_text = ""
        
    def show_tooltip(self, text, x=None, y=None):
        """Show a tooltip with the given text."""
        if self.tooltip_window or not text:
            return
        
        # Get coordinates
        if x is None or y is None:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + 20
        
        # Create tooltip window
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip label
        label = tk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
            padx=4,
            pady=2
        )
        label.pack()
    
    def hide_tooltip(self):
        """Hide the current tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class ProgressDialog:
    """Simple progress dialog for long operations."""
    
    def __init__(self, parent, title="Processing..."):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x100")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.dialog,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(pady=20, padx=20, fill=tk.X)
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_var.set("Please wait...")
        self.status_label = ttk.Label(self.dialog, textvariable=self.status_var)
        self.status_label.pack()
    
    def update_progress(self, value, status=None):
        """Update progress value and status."""
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        self.dialog.update()
    
    def close(self):
        """Close the progress dialog."""
        if self.dialog:
            self.dialog.destroy()


class FindReplaceDialog:
    """Find and replace dialog for text operations."""
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text_widget = text_widget
        self.dialog = None
        self.last_search_index = "1.0"
    
    def show_find_dialog(self):
        """Show the find dialog."""
        if self.dialog:
            self.dialog.lift()
            return
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Find")
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        
        # Find entry
        ttk.Label(self.dialog, text="Find:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.find_entry = ttk.Entry(self.dialog, width=30)
        self.find_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Buttons
        ttk.Button(self.dialog, text="Find Next", command=self.find_next).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.dialog, text="Close", command=self.close_dialog).grid(row=1, column=2, padx=5, pady=5)
        
        # Configure grid
        self.dialog.columnconfigure(1, weight=1)
        
        # Bind events
        self.find_entry.bind('<Return>', lambda e: self.find_next())
        self.dialog.protocol("WM_DELETE_WINDOW", self.close_dialog)
        
        # Focus on entry
        self.find_entry.focus()
    
    def find_next(self):
        """Find the next occurrence of the search text."""
        search_text = self.find_entry.get()
        if not search_text:
            return
        
        # Search from current position
        start_pos = self.text_widget.index(tk.INSERT)
        found_pos = self.text_widget.search(search_text, start_pos, tk.END)
        
        if not found_pos:
            # Search from beginning
            found_pos = self.text_widget.search(search_text, "1.0", start_pos)
        
        if found_pos:
            # Select found text
            end_pos = f"{found_pos}+{len(search_text)}c"
            self.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
            self.text_widget.tag_add(tk.SEL, found_pos, end_pos)
            self.text_widget.mark_set(tk.INSERT, end_pos)
            self.text_widget.see(found_pos)
        else:
            tk.messagebox.showinfo("Not Found", f"'{search_text}' not found.")
    
    def close_dialog(self):
        """Close the find dialog."""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
