#!/usr/bin/env python3
"""
GhostKey Text Editor - Main Entry Point
A text editor that tracks manual typing vs pasted content with visual feedback.
"""

import tkinter as tk
from ghost_key_editor import Application

def main():
    """Main entry point for the GhostKey application."""
    root = tk.Tk()
    app = Application(root)
    
    # Configure the root window
    root.title("GhostKey - Text Editor")
    root.geometry("800x600")
    root.minsize(600, 400)
    
    # Start the application
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")

if __name__ == "__main__":
    main()