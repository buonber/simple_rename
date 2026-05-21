# Simple Rename v1.6 <img src="https://img.shields.io/badge/status-Latest-success" alt="Latest Release">

A free, portable batch file renaming tool featuring a neon-inspired dark UI.

> [!NOTE]
> This is a **portable application**—no installation required. Simply run the executable to start renaming your files immediately.

---

## Changelog v1.6
*feat: center window, smooth fade-in, fix uppercase ext, and add trim options*

* **Add window centering logic** and a seamless 1s opacity fade-in animation on launch.
* **Maintain lowercase/original file extensions** when applying UPPERCASE transformation.
* **Implement "Del L" and "Del R" spinboxes** to trim $N$ characters from filenames.
* **Adjust Custom Name positioning** and include dash (`-`) as a valid separator option.

---

## Changelog v1.5

### 🚀 New Features
* **Dynamic Timestamp:** Auto-append file modification dates (e.g., `YYMMDD`) to prefixes or suffixes.
* **Custom Separators:** Added flexible options (underscore, dot, or none) for filename formatting.

### 🎨 UI Optimizations
* **Refined Layout:** Optimized element padding, spacing, and component sizing for a more compact and organized interface.
* **Icon-based UI:** Replaced text labels with intuitive, professional icons for a cleaner look.
* **Drag & Drop:** Streamlined file import process.

### 🐛 Bug Fixes & Stability
* **State Management:** Fixed `reset_fields` to ensure all UI states clear correctly.
* **UI Clean-up:** Resolved Combobox focus issues (removed unwanted text highlighting artifacts).
* **Stability:** Optimized internal event handling for smoother performance.

---

## Features

* **Batch Renaming** (Find & Replace)
* **Sequential Numbering** (Start, Padding, Positioning)
* **Case Transformation** (UPPERCASE/lowercase)
* **Real-time Preview** before renaming
