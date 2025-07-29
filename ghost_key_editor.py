import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Menu
import os
import threading
from text_tracker import TextTracker
from metadata_manager import MetadataManager
from file_manager import FileManager
from ui_components import StatusBar, HoverManager
import time

class Application:
    """Main application class for GhostKey text editor."""
    
    def __init__(self, root):
        self.root = root
        self.current_file = None
        self.is_modified = False
        
        # Initialize components
        self.text_tracker = TextTracker()
        self.metadata_manager = MetadataManager()
        self.file_manager = FileManager()
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        self.setup_bindings()
        
        # Initialize hover manager after text widget is created
        self.hover_manager = HoverManager(self.text_widget, self.text_tracker)
        
    def setup_ui(self):
        """Setup the main user interface."""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create text widget with scrollbars
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text widget
        self.text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            undo=True,
            font=("Consolas", 11),
            bg="#ffffff",
            fg="#000000",
            insertbackground="#000000",
            selectbackground="#b3d9ff"
        )
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.text_widget.xview)
        
        self.text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack text widget and scrollbars
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Toolbar
        self.setup_toolbar(main_frame)
        
        # Status bar
        self.status_bar = StatusBar(main_frame)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        # Initialize text tracker with text widget
        self.text_tracker.set_text_widget(self.text_widget)
    
    def setup_toolbar(self, parent):
        """Setup the toolbar with quick access buttons."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        # File operations
        ttk.Button(toolbar, text="New", command=self.new_file, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Open", command=self.open_file, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_file, width=8).pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Statistics
        ttk.Button(toolbar, text="Statistics", command=self.show_statistics, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Metadata", command=self.show_metadata_info, width=10).pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Export options
        ttk.Button(toolbar, text="Export Report", command=self.export_analysis_report, width=12).pack(side=tk.LEFT, padx=2)
        
    def setup_menu(self):
        """Setup the application menu."""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_application)
        
        # Edit menu
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        
        # View menu
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Statistics", command=self.show_statistics)
        view_menu.add_command(label="Show Metadata Info", command=self.show_metadata_info)
        
        # Tools menu
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Export Analysis Report", command=self.export_analysis_report)
        
    def setup_bindings(self):
        """Setup keyboard and mouse bindings."""
        # File operations
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-S>', lambda e: self.save_as_file())
        
        # Edit operations
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.text_widget.bind('<Control-x>', lambda e: self.cut())
        self.text_widget.bind('<Control-c>', lambda e: self.copy())
        self.text_widget.bind('<Control-v>', self.on_paste)
        self.root.bind('<Control-a>', lambda e: self.select_all())
        
        # Text modification tracking
        self.text_widget.bind('<KeyPress>', self.on_key_press)
        self.text_widget.bind('<Button-1>', self.on_mouse_click)
        self.text_widget.bind('<Button-3>', self.on_right_click)
        
        # Window closing
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)
        
        # Text modification events
        self.text_widget.bind('<<Modified>>', self.on_text_modified)
        
    def on_key_press(self, event):
        """Handle key press events for tracking manual typing."""
        # Check if this is a paste operation (Ctrl+V)
        if event.state & 0x4 and event.keysym.lower() == 'v':  # Ctrl+V
            # This will be handled by on_paste method
            return
        
        # Track manual typing
        if event.char and event.char.isprintable():
            def track_typing():
                try:
                    # Get current cursor position
                    cursor_pos = self.text_widget.index(f"{tk.INSERT} -1c")
                    # Schedule tracking after the character is inserted
                    self.root.after(1, lambda: self.text_tracker.track_manual_input(cursor_pos, event.char))
                except tk.TclError:
                    pass  # Widget might be destroyed
            
            threading.Thread(target=track_typing, daemon=True).start()
        
    def on_mouse_click(self, event):
        """Handle mouse click events."""
        self.text_tracker.update_cursor_position()
        
    def on_right_click(self, event):
        """Handle right-click context menu."""
        context_menu = None
        try:
            # Create context menu
            context_menu = Menu(self.root, tearoff=0)
            context_menu.add_command(label="Cut", command=self.cut)
            context_menu.add_command(label="Copy", command=self.copy)
            context_menu.add_command(label="Paste", command=self.paste)
            context_menu.add_separator()
            context_menu.add_command(label="Select All", command=self.select_all)
            
            # Show context menu
            context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"Context menu error: {e}")
        finally:
            if context_menu:
                try:
                    context_menu.destroy()
                except:
                    pass
    
    def on_text_modified(self, event):
        """Handle text modification events."""
        if self.text_widget.edit_modified():
            self.is_modified = True
            self.update_title()
            self.text_widget.edit_modified(False)
    
    def on_paste(self, event):
        """Handle paste operations with tracking."""
        try:
            # Get clipboard content
            clipboard_content = self.root.clipboard_get()
            if clipboard_content:
                # Get current selection or cursor position
                try:
                    sel_start = self.text_widget.index(tk.SEL_FIRST)
                    sel_end = self.text_widget.index(tk.SEL_LAST)
                    # Delete selected text first
                    self.text_widget.delete(sel_start, sel_end)
                    insert_pos = sel_start
                except tk.TclError:
                    # No selection, use cursor position
                    insert_pos = self.text_widget.index(tk.INSERT)
                
                # Insert the pasted content
                self.text_widget.insert(insert_pos, clipboard_content)
                
                # Track the pasted content
                self.text_tracker.track_paste_input(insert_pos, clipboard_content)
                
                # Update status
                self.status_bar.set_message(f"Pasted {len(clipboard_content)} characters")
                
        except tk.TclError:
            # No clipboard content or other error
            self.status_bar.set_message("Nothing to paste")
        
        # IMPORTANT: Return 'break' to prevent the default paste behavior
        return 'break'
    
    def paste(self, event=None):
        """Menu/programmatic paste - calls the event handler."""
        return self.on_paste(event)
    
    def cut(self):
        """Cut selected text."""
        try:
            self.text_widget.event_generate("<<Cut>>")
            self.status_bar.set_message("Text cut to clipboard")
        except:
            pass
    
    def copy(self):
        """Copy selected text."""
        try:
            self.text_widget.event_generate("<<Copy>>")
            self.status_bar.set_message("Text copied to clipboard")
        except:
            pass
    
    def undo(self):
        """Undo last action and refresh text tracker metadata."""
        try:
            self.last_saved_metadata = self.text_tracker.get_metadata()
            self.text_widget.edit_undo()
            self.status_bar.set_message("Undo")

            # ✅ Refresh text tracker after undo
            if hasattr(self, "text_tracker") and self.text_tracker:
                self.text_tracker.refresh_after_undo()
        except:
            pass

    def redo(self):
        try:
            self.text_widget.edit_redo()

            # Ask the tracker to restore metadata based on current text
            if hasattr(self, "text_tracker"):
                self.text_tracker.restore_from_current_text()

            # Retag the whole text using restored metadata
            self.retag_all_text()

            self.status_bar.set_message("Redo")
        except Exception as e:
            print(f"[Redo Error] {e}")


        
    def retag_all_text(self):
        self.text_widget.tag_remove("typed", "1.0", "end")
        self.text_widget.tag_remove("pasted", "1.0", "end")

        for rng in self.text_tracker.input_ranges:
            tag = "typed" if rng['source'] == 'manual' else 'pasted'
            start = f"1.0 + {rng['start']}c"
            end = f"1.0 + {rng['end']}c"
            self.text_widget.tag_add(tag, start, end)




    
    def select_all(self):
        """Select all text."""
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.mark_set(tk.INSERT, "1.0")
        self.text_widget.see(tk.INSERT)
        return 'break'
    
    def new_file(self):
        """Create a new file."""
        if self.is_modified and not self.confirm_unsaved_changes():
            return
        
        self.text_widget.delete("1.0", tk.END)
        self.text_tracker.clear()
        self.current_file = None
        self.is_modified = False
        self.update_title()
        self.status_bar.set_message("New file created")
    
    def open_file(self):
        """Open an existing file."""
        if self.is_modified and not self.confirm_unsaved_changes():
            return
        
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("All Lakra files", "*.lakra"),
                ("Lakra Text files", "*.txt.lakra"),
                ("Lakra Markdown files", "*.md.lakra"),
                ("Lakra Python files", "*.py.lakra"),
                ("Lakra JavaScript files", "*.js.lakra"),
                ("Regular Text files", "*.txt"),
                ("Regular Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                content, metadata = self.file_manager.load_file(file_path)
                
                # Clear current content
                self.text_widget.delete("1.0", tk.END)
                self.text_tracker.clear()
                
                # Insert content
                self.text_widget.insert("1.0", content)
                
                # Restore metadata
                if metadata:
                    self.text_tracker.load_metadata(metadata)
                
                self.current_file = file_path
                self.is_modified = False
                self.update_title()
                self.status_bar.set_message(f"Opened: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")
    
    def save_file(self):
        """Save the current file."""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()
    
    def save_as_file(self):
        """Save the file with a new name."""
        file_path = filedialog.asksaveasfilename(
            title="Save File As",
            defaultextension=".txt.lakra",
            filetypes=[
                ("Lakra Text files", "*.txt.lakra"),
                ("Lakra Markdown files", "*.md.lakra"),
                ("Lakra Python files", "*.py.lakra"),
                ("Lakra JavaScript files", "*.js.lakra"),
                ("Lakra HTML files", "*.html.lakra"),
                ("Lakra CSS files", "*.css.lakra"),
                ("Lakra JSON files", "*.json.lakra"),
                ("All Lakra files", "*.lakra"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.save_to_file(file_path)
    
    def save_to_file(self, file_path):
        """Save content and metadata to the specified file."""
        try:
            content = self.text_widget.get("1.0", tk.END + "-1c")
            metadata = self.text_tracker.get_metadata()
            
            self.file_manager.save_file(file_path, content, metadata)
            
            self.current_file = file_path
            self.is_modified = False
            self.update_title()
            self.status_bar.set_message(f"Saved: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
    
    def show_metadata_info(self):
        """Show metadata information dialog."""
        metadata = self.text_tracker.get_metadata()
        
        info_window = tk.Toplevel(self.root)
        info_window.title("Metadata Information")
        info_window.geometry("500x400")
        
        # Create text widget to display metadata
        text_area = tk.Text(info_window, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(info_window, orient=tk.VERTICAL, command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        # Display metadata information
        if metadata and 'ranges' in metadata:
            text_area.insert(tk.END, "Text Input Source Tracking:\n\n")
            
            total_chars = len(self.text_widget.get("1.0", tk.END + "-1c"))
            typed_chars = 0
            pasted_chars = 0
            
            for range_info in metadata['ranges']:
                source = range_info.get('source', 'unknown')
                start = range_info.get('start', 0)
                end = range_info.get('end', 0)
                length = end - start
                
                if source == 'manual':
                    typed_chars += length
                elif source == 'pasted':
                    pasted_chars += length
                
                text_area.insert(tk.END, f"Position {start}-{end}: {source} ({length} chars)\n")
            
            text_area.insert(tk.END, f"\nSummary:\n")
            text_area.insert(tk.END, f"Total characters: {total_chars}\n")
            text_area.insert(tk.END, f"Manually typed: {typed_chars}\n")
            text_area.insert(tk.END, f"Pasted content: {pasted_chars}\n")
            
            if total_chars > 0:
                typed_percent = (typed_chars / total_chars) * 100
                pasted_percent = (pasted_chars / total_chars) * 100
                text_area.insert(tk.END, f"Typed percentage: {typed_percent:.1f}%\n")
                text_area.insert(tk.END, f"Pasted percentage: {pasted_percent:.1f}%\n")
        else:
            text_area.insert(tk.END, "No metadata available for this document.")
        
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Make text area read-only
        text_area.configure(state=tk.DISABLED)
    
    def show_statistics(self):
        """Show detailed statistics about text composition."""
        metadata = self.text_tracker.get_metadata()
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Text Composition Statistics")
        stats_window.geometry("600x500")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Overview tab
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="Overview")
        
        total_chars = len(self.text_widget.get("1.0", tk.END + "-1c"))
        typed_chars = 0
        pasted_chars = 0
        typing_sessions = 0
        paste_operations = 0
        
        if metadata and 'ranges' in metadata:
            for range_info in metadata['ranges']:
                source = range_info.get('source', 'unknown')
                start = range_info.get('start', 0)
                end = range_info.get('end', 0)
                length = end - start
                
                if source == 'manual':
                    typed_chars += length
                    typing_sessions += 1
                elif source == 'pasted':
                    pasted_chars += length
                    paste_operations += 1
        
        # Overview statistics
        overview_text = tk.Text(overview_frame, wrap=tk.WORD, font=("Arial", 12))
        overview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        overview_text.insert(tk.END, "DOCUMENT COMPOSITION ANALYSIS\n")
        overview_text.insert(tk.END, "=" * 40 + "\n\n")
        
        overview_text.insert(tk.END, f"Total Characters: {total_chars:,}\n")
        overview_text.insert(tk.END, f"Manually Typed: {typed_chars:,} characters\n")
        overview_text.insert(tk.END, f"Pasted Content: {pasted_chars:,} characters\n\n")
        
        if total_chars > 0:
            typed_percent = (typed_chars / total_chars) * 100
            pasted_percent = (pasted_chars / total_chars) * 100
            
            overview_text.insert(tk.END, f"Composition Breakdown:\n")
            overview_text.insert(tk.END, f"  • Typed: {typed_percent:.1f}%\n")
            overview_text.insert(tk.END, f"  • Pasted: {pasted_percent:.1f}%\n\n")
            
            # Authenticity assessment
            if pasted_percent > 70:
                authenticity = "Low - Heavily dependent on external content"
            elif pasted_percent > 40:
                authenticity = "Medium - Significant external content mixed with original"
            elif pasted_percent > 15:
                authenticity = "High - Mostly original with some external references"
            else:
                authenticity = "Very High - Predominantly original content"
            
            overview_text.insert(tk.END, f"Content Authenticity: {authenticity}\n\n")
        
        overview_text.insert(tk.END, f"Input Operations:\n")
        overview_text.insert(tk.END, f"  • Typing Sessions: {typing_sessions}\n")
        overview_text.insert(tk.END, f"  • Paste Operations: {paste_operations}\n")
        
        overview_text.configure(state=tk.DISABLED)
        
        # Detailed breakdown tab
        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text="Detailed Breakdown")
        
        details_text = tk.Text(details_frame, wrap=tk.WORD, font=("Consolas", 10))
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=details_text.yview)
        details_text.configure(yscrollcommand=details_scrollbar.set)
        
        if metadata and 'ranges' in metadata:
            details_text.insert(tk.END, "DETAILED INPUT ANALYSIS\n")
            details_text.insert(tk.END, "=" * 50 + "\n\n")
            
            for i, range_info in enumerate(metadata['ranges'], 1):
                source = range_info.get('source', 'unknown')
                start = range_info.get('start', 0)
                end = range_info.get('end', 0)
                length = end - start
                timestamp = range_info.get('timestamp', 'Unknown')
                
                details_text.insert(tk.END, f"Operation #{i}:\n")
                details_text.insert(tk.END, f"  Type: {source.upper()}\n")
                details_text.insert(tk.END, f"  Position: {start:,} - {end:,}\n")
                details_text.insert(tk.END, f"  Length: {length:,} characters\n")
                details_text.insert(tk.END, f"  Time: {timestamp}\n")
                
                # Show preview of content
                content = self.text_widget.get(f"1.0+{start}c", f"1.0+{end}c")
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace('\n', '\\n').replace('\t', '\\t')
                details_text.insert(tk.END, f"  Preview: \"{preview}\"\n")
                details_text.insert(tk.END, "-" * 40 + "\n")
        else:
            details_text.insert(tk.END, "No detailed tracking data available.")
        
        details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        details_text.configure(state=tk.DISABLED)
    
    def export_analysis_report(self):
        """Export a comprehensive analysis report."""
        report_path = filedialog.asksaveasfilename(
            title="Export Analysis Report",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("HTML files", "*.html"),
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )
        
        if not report_path:
            return
        
        try:
            metadata = self.text_tracker.get_metadata()
            total_chars = len(self.text_widget.get("1.0", tk.END + "-1c"))
            typed_chars = 0
            pasted_chars = 0
            
            if metadata and 'ranges' in metadata:
                for range_info in metadata['ranges']:
                    source = range_info.get('source', 'unknown')
                    start = range_info.get('start', 0)
                    end = range_info.get('end', 0)
                    length = end - start
                    
                    if source == 'manual':
                        typed_chars += length
                    elif source == 'pasted':
                        pasted_chars += length
            
            # Generate report content
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            report_content = f"""GHOSTKEY TEXT ANALYSIS REPORT
Generated: {current_time}
File: {self.current_file or 'Untitled'}

SUMMARY
=======
Total Characters: {total_chars:,}
Manually Typed: {typed_chars:,} characters ({(typed_chars/total_chars*100):.1f}% if total_chars else 0)
Pasted Content: {pasted_chars:,} characters ({(pasted_chars/total_chars*100):.1f}% if total_chars else 0)

AUTHENTICITY ASSESSMENT
======================
"""
            
            if total_chars > 0:
                pasted_percent = (pasted_chars / total_chars) * 100
                if pasted_percent > 70:
                    assessment = "LOW AUTHENTICITY - Document is heavily dependent on external content"
                elif pasted_percent > 40:
                    assessment = "MEDIUM AUTHENTICITY - Significant mix of original and external content"
                elif pasted_percent > 15:
                    assessment = "HIGH AUTHENTICITY - Mostly original with some external references"
                else:
                    assessment = "VERY HIGH AUTHENTICITY - Predominantly original content"
                
                report_content += f"{assessment}\n\n"
            
            if metadata and 'ranges' in metadata:
                report_content += "DETAILED BREAKDOWN\n"
                report_content += "==================\n"
                
                for i, range_info in enumerate(metadata['ranges'], 1):
                    source = range_info.get('source', 'unknown')
                    start = range_info.get('start', 0)
                    end = range_info.get('end', 0)
                    length = end - start
                    timestamp = range_info.get('timestamp', 'Unknown')
                    
                    report_content += f"\nOperation #{i}:\n"
                    report_content += f"  Type: {source.upper()}\n"
                    report_content += f"  Position: {start:,} - {end:,}\n"
                    report_content += f"  Length: {length:,} characters\n"
                    report_content += f"  Timestamp: {timestamp}\n"
            
            # Save the report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.status_bar.set_message(f"Analysis report exported: {os.path.basename(report_path)}")
            messagebox.showinfo("Export Complete", f"Analysis report saved to:\n{report_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")
    
    def confirm_unsaved_changes(self):
        """Ask user to confirm losing unsaved changes."""
        result = messagebox.askyesnocancel(
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save them?"
        )
        
        if result is True:  # Yes - save
            self.save_file()
            return True
        elif result is False:  # No - don't save
            return True
        else:  # Cancel
            return False
    
    def update_title(self):
        """Update the window title."""
        title = "GhostKey - Text Editor"
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        if self.is_modified:
            title += " *"
        self.root.title(title)
    
    def exit_application(self):
        """Exit the application."""
        if self.is_modified and not self.confirm_unsaved_changes():
            return
        
        self.root.quit()


"""
GhostKey Text Editor - Main Application Class
Handles the primary GUI and coordinates all components.

Fixed Issues:
1. Corrected paste binding syntax in setup_bindings()
2. Added 'return 'break'' to on_paste() to prevent double paste
3. Fixed key press detection for Ctrl+V
4. Fixed cut/copy bindings that were calling functions instead of binding them
5. Updated paste method to accept event parameter
6. Added proper event handling to prevent default behaviors

Key Changes Made:
- Fixed binding syntax: self.text_widget.bind('<Control-v>', self.on_paste)
- Added return 'break' in on_paste() to prevent Tkinter's default paste
- Fixed cut/copy bindings from self.copy() to lambda e: self.copy()
- Improved paste detection in on_key_press()
- Updated context menu paste call

This should resolve the double paste issue completely.
"""

