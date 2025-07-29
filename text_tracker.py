"""
Text Tracker - Manages tracking of text input sources and metadata.
"""

import tkinter as tk
import threading
import time

class TextTracker:
    """Tracks text input sources and maintains metadata."""

    def __init__(self):
        self.text_widget = None
        self.input_ranges = []  # List of {start, end, source, timestamp}
        self.lock = threading.Lock()
        self.last_cursor_pos = "1.0"

    def set_text_widget(self, text_widget):
        """Set the text widget to track."""
        self.text_widget = text_widget

        # Tag configurations
        self.text_widget.tag_configure("manual_green", foreground="green")
        self.text_widget.tag_configure("pasted_red", foreground="red")
        self.text_widget.tag_configure("selection_blue", background="lightblue")

        # Ensure selection is always on top
        self.text_widget.tag_raise("selection_blue")

        # Bind events
        self.text_widget.bind("<Motion>", self.on_hover)
        self.text_widget.bind("<<Selection>>", self.on_selection_changed)
        self.text_widget.bind("<ButtonRelease-1>", self.on_selection_changed)
        self.text_widget.bind("<KeyRelease>", self.on_selection_changed)

    def clear(self):
        """Clear all tracking data."""
        with self.lock:
            self.input_ranges.clear()
            self.last_cursor_pos = "1.0"

    def track_manual_input(self, position, character):
        """Track manually typed input."""
        if not self.text_widget:
            return
        try:
            with self.lock:
                start_idx = self._pos_to_index(position)
                end_idx = start_idx + len(character)
                self._update_ranges(start_idx, end_idx, 'manual')
        except Exception as e:
            print(f"Error tracking manual input: {e}")

    
    def track_paste_input(self, position, content):
        """Track pasted input."""
        if not self.text_widget or not content:
            return
        try:
            with self.lock:
                start_idx = self._pos_to_index(position)
                end_idx = start_idx + len(content)
                self._update_ranges(start_idx, end_idx, 'pasted')
        except Exception as e:
            print(f"Error tracking paste input: {e}")

    def _pos_to_index(self, position):
        """Convert Tkinter text position to character index."""
        try:
            if isinstance(position, str):
                line, col = position.split('.')
                line = int(line) - 1
                col = int(col)
                text_content = self.text_widget.get("1.0", tk.END + "-1c")
                lines = text_content.split('\n')
                index = 0
                for i in range(line):
                    if i < len(lines):
                        index += len(lines[i]) + 1
                index += min(col, len(lines[line]) if line < len(lines) else 0)
                return index
            else:
                return int(position)
        except Exception as e:
            print(f"Error converting position to index: {e}")
            return 0

    def _index_to_pos(self, index):
        """Convert character index to Tkinter text position."""
        try:
            text_content = self.text_widget.get("1.0", tk.END + "-1c")
            if index >= len(text_content):
                return f"{len(text_content.split(chr(10)))}.{len(text_content.split(chr(10))[-1])}"
            lines = text_content[:index].split('\n')
            return f"{len(lines)}.{len(lines[-1])}"
        except Exception as e:
            print(f"Error converting index to position: {e}")
            return "1.0"

    def _handle_deletions(self):
        """Adjust metadata when text is deleted."""
        current_length = len(self.text_widget.get("1.0", tk.END + "-1c"))
        new_ranges = []
        for r in self.input_ranges:
            if r['start'] >= current_length:
                continue  # Entirely deleted
            r['end'] = min(r['end'], current_length)
            if r['end'] > r['start']:
                new_ranges.append(r)
        self.input_ranges = new_ranges

    def _update_ranges(self, start_idx, end_idx, source):
        """Update ranges for new input & handle deletions automatically."""
        self._handle_deletions()  # Check for deleted characters first

        insertion_length = end_idx - start_idx
        new_ranges = []
        for r in self.input_ranges:
            r_start, r_end = r['start'], r['end']

            if r_end <= start_idx:
                new_ranges.append(r.copy())
            elif r_start >= start_idx:
                new_ranges.append({
                    'start': r_start + insertion_length,
                    'end': r_end + insertion_length,
                    'source': r['source'],
                    'timestamp': r['timestamp']
                })
            else:
                if r_start < start_idx:
                    new_ranges.append({
                        'start': r_start,
                        'end': start_idx,
                        'source': r['source'],
                        'timestamp': r['timestamp']
                    })
                if r_end > start_idx:
                    new_ranges.append({
                        'start': end_idx,
                        'end': r_end + insertion_length,
                        'source': r['source'],
                        'timestamp': r['timestamp']
                    })

        new_ranges.append({
            'start': start_idx,
            'end': end_idx,
            'source': source,
            'timestamp': time.time()
        })

        new_ranges.sort(key=lambda x: x['start'])
        merged = []
        for r in new_ranges:
            if merged and merged[-1]['source'] == r['source'] and merged[-1]['end'] == r['start']:
                merged[-1]['end'] = r['end']
            else:
                merged.append(r)
        self.input_ranges = merged

    def get_source_at_position(self, position):
        """Get the input source at a specific position."""
        try:
            with self.lock:
                index = self._pos_to_index(position)
                for range_info in self.input_ranges:
                    if range_info['start'] <= index < range_info['end']:
                        return range_info['source']
                return None
        except Exception as e:
            print(f"Error getting source at position: {e}")
            return None

    def get_metadata(self):
        """Get all metadata as a dictionary."""
        with self.lock:
            return {
                'version': '1.1',
                'ranges': [
                    {
                        'start': r['start'],
                        'end': r['end'],
                        'source': r['source'],
                        'timestamp': r['timestamp']
                    }
                    for r in self.input_ranges
                ]
            }

    def load_metadata(self, metadata):
        """Load metadata from a dictionary."""
        if not metadata or 'ranges' not in metadata:
            return
        with self.lock:
            self.input_ranges = []
            for range_data in metadata['ranges']:
                self.input_ranges.append({
                    'start': range_data.get('start', 0),
                    'end': range_data.get('end', 0),
                    'source': range_data.get('source', 'unknown'),
                    'timestamp': range_data.get('timestamp', time.time())
                })
            self.input_ranges.sort(key=lambda x: x['start'])

    def update_cursor_position(self):
        """Update the last known cursor position."""
        if self.text_widget:
            try:
                self.last_cursor_pos = self.text_widget.index(tk.INSERT)
            except:
                pass

    def get_ranges_in_area(self, start_pos, end_pos):
        """Get all ranges that intersect with the given area."""
        try:
            with self.lock:
                start_idx = self._pos_to_index(start_pos)
                end_idx = self._pos_to_index(end_pos)
                return [r for r in self.input_ranges if r['start'] < end_idx and r['end'] > start_idx]
        except Exception as e:
            print(f"Error getting ranges in area: {e}")
            return []

    # ✅ NEW FUNCTIONS FOR HOVER & SELECTION FIX

    def on_hover(self, event=None):
        """Change color on hover (manual = green, pasted = red) but don't override selection."""
        if not self.text_widget:
            return
        index = self.text_widget.index(f"@{event.x},{event.y}")
        source = self.get_source_at_position(index)

        # Remove old hover tags
        self.text_widget.tag_remove("manual_green", "1.0", tk.END)
        self.text_widget.tag_remove("pasted_red", "1.0", tk.END)

        if source:
            idx = self._pos_to_index(index)
            for r in self.input_ranges:
                if r['start'] <= idx < r['end']:
                    start_pos = self._index_to_pos(r['start'])
                    end_pos = self._index_to_pos(r['end'])
                    if source == "manual":
                        self.text_widget.tag_add("manual_green", start_pos, end_pos)
                    elif source == "pasted":
                        self.text_widget.tag_add("pasted_red", start_pos, end_pos)

        # Ensure selection stays visible
        self.text_widget.tag_raise("selection_blue")

    def on_selection_changed(self, event=None):
        """Always show blue selection over hover colors."""
        if not self.text_widget:
            return
        try:
            sel_start = self.text_widget.index(tk.SEL_FIRST)
            sel_end = self.text_widget.index(tk.SEL_LAST)

            # Remove previous blue selection
            self.text_widget.tag_remove("selection_blue", "1.0", tk.END)

            # Apply new selection
            self.text_widget.tag_add("selection_blue", sel_start, sel_end)

            # Ensure selection stays visible
            self.text_widget.tag_raise("selection_blue")
        except tk.TclError:
            self.text_widget.tag_remove("selection_blue", "1.0", tk.END)
    

    def refresh_after_undo(self):
        """Recalculate metadata after undo - treating restored text as manual."""
        if not self.text_widget:
            return

        current_text = self.text_widget.get("1.0", tk.END + "-1c")
        with self.lock:
            self.input_ranges.clear()
            if current_text:  # Mark all restored text as manual
                self.input_ranges.append({
                    'start': 0,
                    'end': len(current_text),
                    'source': 'manual',
                    'timestamp': time.time()
                })

    def restore_from_current_text(self):
        """Rebuild metadata from current text (used in redo)."""
        if not self.text_widget:
            return

        current_text = self.text_widget.get("1.0", "end-1c")
        self.input_ranges.clear()

        if current_text:
            self.input_ranges.append({
                "start": 0,
                "end": len(current_text),
                "source": "pasted",  # assume redo inserts pasted text
                "timestamp": time.time()
            })
