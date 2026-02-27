import fitz  # PyMuPDF, install with pip install pymupdf
import re, sys
import argparse


def extract_sections(pdf_path: str) -> list:
    """
    Extract sections from a single PDF using the TOC on pages 2-6 (0-based).
    Returns a list of dictionaries with section_number, title, page, and text.
    """
    empty_section_number_count = 1
    doc = fitz.open(pdf_path)
    # Parse TOC from pages 2-6 (0-based, range(2,7))
    toc_text = ""
    for page_num in range(2, 7):
        toc_text += doc[page_num].get_text() + "\n"

    # Parse TOC lines
    toc = []
    last_line = None
    for line in toc_text.split('\n'):
        line = line.strip()
        if not line or "Table of Contents" in line:
            continue
        # Match lines with optional leading spaces
        match = re.match(r'^\s*(?:(?:(\d+(?:\.\d+)*\.?)\s+)?(.+?)\s*\.+\s*(\d+)$)', line)
        empty_section_number = False
        if match:
            if match.group(1) is not None:
                section_number = match.group(1)
            else:
                section_number = "0." + str(empty_section_number_count)
                empty_section_number = True
            title = match.group(2).strip()
            page = int(match.group(3))
            if page >= 13 and section_number.startswith("0"):
                section_number = last_line
            toc.append((section_number, title, page))
            if empty_section_number:
                empty_section_number_count += 1
        last_line = line
    if not toc:
        print(f"No sections found in {pdf_path}.")
        doc.close()
        return []

    # Extract text for each section
    sections = []
    for i in range(len(toc)):
        section_number, title, page = toc[i]
        if page == 0:
            # section_number: 0.1, title: Version 3
            continue

        next_section_number = toc[i + 1][0] if i + 1 < len(toc) else None
        next_title = toc[i + 1][1] if i + 1 < len(toc) else None
        next_page = toc[i + 1][2] if i + 1 < len(toc) else len(doc) + 1

        # if section_number == '4.4.3.':
        #     print(f"next_title: {next_title}, next_page: {next_page}")

        # Collect full text with formatting from start page to next page
        full_text = []
        for p in range(page - 1, next_page):
            if p >= doc.page_count:
                continue
            page_obj = doc[p]
            text_dict = page_obj.get_text("dict")
            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:  # Skip non-text blocks
                    continue
                for line in block.get("lines", []):
                    line_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                    if not line_text:
                        continue
                    # Get font size from first span
                    font_size = line.get("spans", [{}])[0].get("size", 0.0)
                    full_text.append((line_text, font_size))

        # Find start index after title with font size >= 13
        start_idx = -1
        for j in range(len(full_text)):
            line_text, font_size = full_text[j]
            if font_size >= 13 and (title in line_text or (not section_number.startswith("0") and section_number in line_text)):
                start_idx = j + 1
                break
        if start_idx == -1:
            print(f"Title '{title}' or section number '{section_number}' not found on page {page} with font size >= 13.")
            continue

        # Find end index before next title with font size >= 13
        end_idx = len(full_text)
        if next_title:
            for j in range(start_idx, len(full_text)):
                line_text, font_size = full_text[j]
                if font_size >= 13 and (next_title in line_text or (next_section_number and not next_section_number.startswith("0") and next_section_number in line_text)):
                    end_idx = j
                    break

        # Collect text, removing empty lines
        text = '\n'.join([line_text for line_text, _ in full_text[start_idx:end_idx] if line_text.strip()]).strip()

        sections.append({
            "section_number": section_number,
            "title": title,
            "page": page,
            "text": text
        })

    doc.close()
    return sections


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PDF sections using TOC.")
    parser.add_argument("--pdf_path", type=str, default="data/2024_Joint_Application_Information_Requirements.pdf")
    args = parser.parse_args()

    sections = extract_sections(args.pdf_path)
    for section in sections:
        print(f"\n{'=' * 80}")
        print(f"Section number: {section['section_number']} Section title: {section['title']} (Page: {section['page']})")
        # preview_start = section['text'][:50]
        # preview_last = section['text'][-50:]
        #
        # print(f"Preview_start: {preview_start}")
        # print(f"Preview_last: {preview_last}")
        # print(f"Length: {len(section['text'])} characters")
    print(f"length of sections: {len(sections)}")