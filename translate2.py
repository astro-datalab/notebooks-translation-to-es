import argparse
import nbformat
import time
import re
from googletrans import Translator

# --- Define word placeholders ---
#PLACEHOLDER_MAP = {
#    "notebook": "__NOTEBOOK__",
#    "by default": "__BYDEFAULT__",
#    "**": "PHBOLD",
#    "_": "PHITALIC",
#    "`": "PHCODE",
#    "__": "PHUNDER",
#}
#
## Reverse mapping for restoration
#REVERSE_MAP = {v: k for k, v in PLACEHOLDER_MAP.items()}
#
#def mask_text(text):
#    """Replace words with placeholders before translation."""
#    for word, placeholder in PLACEHOLDER_MAP.items():
#        # Use regex to match whole words, case-insensitive
#        #text = text.replace(placeholder, "por omisión")
#        #text = re.sub(rf'\b{re.escape(word)}\b', placeholder, text, flags=re.IGNORECASE)
#        text = text.replace(word, placeholder)
#    return text

#def unmask_text(text):
#    """Replace placeholders back with the original words (or desired translation)."""
#    for placeholder, word in REVERSE_MAP.items():
#        # For 'by default', translate to 'por omisión' instead of literal English
#        if word == "by default":
#            text = text.replace(placeholder, "por omisión")
#        else:
#        text = text.replace(placeholder, word)
#    return text

def translate_text(translator, text, src="en", dest="es"):
    #"""Helper function: mask, translate, then unmask."""
    """Helper function with retry logic."""
    try:
        time.sleep(0.1)  # avoid rate limiting
        return translator.translate(text, src=src, dest=dest).text
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
        return text  # fallback to original

def process_code_cell(source, translator, keep_both=False):
    """
    Process code cell line by line, translating:
    1. Comments (# ...)
    2. Plot labels (xlabel, ylabel, title, set(...label=...))
    3. Print statements
    4. Docstrings (triple-quoted)
    """
    new_lines = []
    in_docstring = False
    docstring_delim = None
    docstring_buffer = []

    for line in source.splitlines():
        stripped = line.strip()

        # --- Handle docstrings ---
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_docstring = True
            docstring_delim = stripped[:3]
            docstring_buffer = [line]
            continue
        elif in_docstring:
            docstring_buffer.append(line)
            if stripped.endswith(docstring_delim):
                # End of docstring
                doc_text = "\n".join(docstring_buffer)
                translated = translate_text(translator, doc_text)
                if keep_both:
                    merged = (
                        f"{doc_text}\n\n# --- Translation ---\n{translated}"
                    )
                    new_lines.append(merged)
                else:
                    new_lines.append(translated)
                in_docstring = False
                docstring_delim = None
                docstring_buffer = []
            continue

        # --- Translate comments ---
        if "#" in line:
            parts = line.split("#", 1)
            code_part = parts[0]
            comment = parts[1].strip()
            if comment:
                translated = translate_text(translator, comment)
                if keep_both:
                    new_lines.append(f"{code_part}# {comment}  # [ES] {translated}")
                else:
                    new_lines.append(f"{code_part}# {translated}")
            else:
                new_lines.append(line)
            continue

        # --- Translate print statements ---
        if re.search(r"print\s*\(", line):
            matches = re.findall(r"['\"](.*?)['\"]", line)
            new_line = line
            for m in matches:
                translated = translate_text(translator, m)
                if keep_both:
                    replacement = f"{m} / [ES] {translated}"
                else:
                    replacement = translated
                new_line = new_line.replace(m, replacement, 1)
            new_lines.append(new_line)
            continue

        # --- Translate plot labels ---
        if any(lbl in line for lbl in ["xlabel", "ylabel", "title"]):
            matches = re.findall(r"['\"](.*?)['\"]", line)
            new_line = line
            for m in matches:
                translated = translate_text(translator, m)
                if keep_both:
                    replacement = f"{m} / [ES] {translated}"
                else:
                    replacement = translated
                new_line = new_line.replace(m, replacement, 1)
            new_lines.append(new_line)
            continue

        # --- Default: keep line ---
        new_lines.append(line)

    return "\n".join(new_lines)

def main():
    parser = argparse.ArgumentParser(
        description="Translate Jupyter notebook: markdown fully, code comments/labels/prints/docstrings selectively."
    )
    parser.add_argument("notebook", help="Path to the .ipynb notebook file")
    parser.add_argument("-o", "--output", help="Output notebook file", default="translated_notebook.ipynb")
    parser.add_argument("--keep-both", action="store_true", help="Keep both English and Spanish in cells")
    args = parser.parse_args()

    with open(args.notebook, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    with open("../disclaimer_esen.md", "r", encoding="utf-8") as f:
        DISCLAIMER_TEXT = f.read()

    translator = Translator()

    for idx, cell in enumerate(nb.cells, start=1):
        if cell["cell_type"] == "markdown":
            lines = cell["source"].splitlines()
            if any(line.strip() == "# Disclaimer & attribution" for line in lines):
                cell["source"] = DISCLAIMER_TEXT
                print(f"🔄 Replaced disclaimer cell {idx}")
            else:
                text = cell["source"]
                translated = translate_text(translator, text)
                if args.keep_both:
                    cell["source"] = (
                        "## 🇬🇧 English\n\n"
                        + text
                        + "\n\n---\n\n"
                        + "## 🇪🇸 Español\n\n"
                        + translated
                    )
                else:
                    cell["source"] = translated
                print(f"✅ Translated markdown cell {idx}")

        elif cell["cell_type"] == "code":
            cell["source"] = process_code_cell(cell["source"], translator, keep_both=args.keep_both)
            print(f"✅ Processed code cell {idx}")

    with open(args.output, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    print(f"\n✨ Translated notebook written to {args.output}")

if __name__ == "__main__":
    main()

