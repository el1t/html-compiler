# HTML "Compiler"
---
Creates standalone HTML files, consolidating referenced files. Encodes all files in base64, except CSS and JS (no need, saves space). Searches for referenced files in CSS within url() fields. Does not search javascript files. Eventually will minify CSS, JS, and HTML.

Usage:
```
python3 html-compiler.py <input-file>
```
Currently outputs to the same directory as `output.html`.