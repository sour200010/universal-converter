import os
import io
import shutil
import subprocess
import warnings
from PIL import Image
import pymupdf
from pypdf import PdfWriter
from pdf2docx import Converter
import pdfplumber
import pandas as pd
from pptx import Presentation

# Suppress fitz deprecation notices
warnings.filterwarnings("ignore", category=UserWarning, module="fitz")
warnings.filterwarnings("ignore", message=".*The `fitz` API is deprecated.*")

# --- Image Operations ---
def resize_and_compress_image(
    input_path: str,
    output_path: str,
    width: float = None,
    height: float = None,
    unit: str = "Pixels (px)",
    target_dpi: int = 72,
    export_format: str = "JPEG",
    target_kb: int = 0,
    quality: int = 80
) -> str:
    unit_to_inch = {
        "Pixels (px)": 1.0,
        "Inches (in)": 1.0,
        "Centimeters (cm)": 1 / 2.54,
        "Millimeters (mm)": 1 / 25.4
    }

    raw = Image.open(input_path)
    orig_w, orig_h = raw.size

    if unit == "Pixels (px)":
        final_w = int(round(width)) if width else orig_w
        final_h = int(round(height)) if height else orig_h
    else:
        mult = unit_to_inch.get(unit, 1.0)
        final_w = int(round(width * mult * target_dpi)) if width else orig_w
        final_h = int(round(height * mult * target_dpi)) if height else orig_h

    processed = raw.copy()
    if (final_w, final_h) != (orig_w, orig_h):
        processed = processed.resize((final_w, final_h), Image.Resampling.LANCZOS)

    if export_format in ["JPEG", "JPG"] and processed.mode in ("RGBA", "P"):
        processed = processed.convert("RGB")

    if target_kb > 0 and export_format in ["JPEG", "WEBP"]:
        low, high = 5, 95
        matched_buffer = None
        for _ in range(8):
            mid = (low + high) // 2
            buf = io.BytesIO()
            processed.save(buf, format=export_format, quality=mid, optimize=True, dpi=(target_dpi, target_dpi))
            if (buf.tell() / 1024) <= target_kb:
                matched_buffer = buf.getvalue()
                low = mid + 1
            else:
                high = mid - 1

        if matched_buffer:
            with open(output_path, "wb") as f:
                f.write(matched_buffer)
        else:
            processed.save(output_path, format=export_format, quality=5, optimize=True, dpi=(target_dpi, target_dpi))
    else:
        save_opts = {"format": export_format, "dpi": (target_dpi, target_dpi), "optimize": True}
        if export_format in ["JPEG", "WEBP"]:
            save_opts["quality"] = quality
        elif export_format == "PNG":
            save_opts["compress_level"] = 9
        processed.save(output_path, **save_opts)

    return output_path

def image_to_pdf(input_path: str, output_path: str) -> str:
    im = Image.open(input_path)
    if im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    im.save(output_path, "PDF", resolution=100.0)
    return output_path

# --- PDF Tools ---
def merge_pdfs(pdf_paths: list[str], output_path: str) -> str:
    writer = PdfWriter()
    for p in pdf_paths:
        writer.append(p)
    with open(output_path, "wb") as f:
        writer.write(f)
    writer.close()
    return output_path

def compress_pdf(input_path: str, output_path: str, level: str = "recommended") -> str:
    """
    Compresses PDF using PyMuPDF.
    - extreme: Aggressive downsampling (DPI 72, quality ~40), maximum deflation.
    - recommended: Balanced reduction (DPI 150, quality ~75), clean fonts.
    - low: Minimal image tampering (quality ~90), font/stream deflating only.
    """
    doc = pymupdf.open(input_path)
    level = level.lower()

    if level == "extreme":
        img_quality = 40
        max_dim = 1000
    elif level == "low":
        img_quality = 90
        max_dim = 2400
    else:  # recommended
        img_quality = 70
        max_dim = 1600

    # Optimize and re-compress embedded raster images
    for page in doc:
        for img_info in page.get_images():
            xref = img_info[0]
            try:
                base_img = doc.extract_image(xref)
                if not base_img:
                    continue
                
                raw_bytes = base_img["image"]
                pil_img = Image.open(io.BytesIO(raw_bytes))

                # Resize oversized images down
                w, h = pil_img.size
                if max(w, h) > max_dim:
                    scale = max_dim / max(w, h)
                    pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

                if pil_img.mode in ("RGBA", "P"):
                    pil_img = pil_img.convert("RGB")

                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=img_quality, optimize=True)
                doc.update_stream(xref, buf.getvalue())
            except Exception:
                continue

    # Clean unused objects, deflate font streams and structural trees
    doc.save(
        output_path,
        garbage=4,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True
    )
    doc.close()
    return output_path

# --- PDF to Office ---
def pdf_to_word(input_path: str, output_path: str) -> str:
    cv = Converter(input_path)
    cv.convert(output_path)
    cv.close()
    return output_path

def pdf_to_excel(input_path: str, output_path: str) -> str:
    tables_found = []
    with pdfplumber.open(input_path) as pdf:
        for idx, page in enumerate(pdf.pages):
            extracted = page.extract_tables()
            for t_idx, table in enumerate(extracted):
                if table and len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    tables_found.append((f"Page_{idx+1}_T{t_idx+1}", df))

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        if tables_found:
            for sheet_name, df in tables_found:
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        else:
            pd.DataFrame({"Notice": ["No structured tables detected"]}).to_excel(writer, sheet_name="Result", index=False)
    return output_path

def pdf_to_powerpoint(input_path: str, output_path: str) -> str:
    prs = Presentation()
    blank_slide_layout = prs.slide_layouts[6]
    doc = pymupdf.open(input_path)
    temp_dir = os.path.dirname(output_path)

    for i, page in enumerate(doc):
        slide = prs.slides.add_slide(blank_slide_layout)
        pix = page.get_pixmap(dpi=150)
        temp_img = os.path.join(temp_dir, f"_slide_render_{i}.png")
        pix.save(temp_img)
        slide.shapes.add_picture(temp_img, 0, 0, width=prs.slide_width, height=prs.slide_height)
        if os.path.exists(temp_img):
            os.remove(temp_img)

    doc.close()
    prs.save(output_path)
    return output_path

# --- Office to PDF (Windows COM with Headless Fallback) ---
def convert_office_document(input_path: str, output_path: str, doc_type: str) -> str:
    # Attempt Windows COM automation first
    try:
        import win32com.client
        import pythoncom
        pythoncom.CoInitialize()

        abs_in = os.path.abspath(input_path)
        abs_out = os.path.abspath(output_path)

        if doc_type == "docx":
            app = win32com.client.Dispatch("Word.Application")
            app.Visible = False
            try:
                doc = app.Documents.Open(abs_in)
                doc.SaveAs(abs_out, FileFormat=17)
                doc.Close()
            finally:
                app.Quit()
        elif doc_type == "pptx":
            app = win32com.client.Dispatch("Powerpoint.Application")
            try:
                deck = app.Presentations.Open(abs_in, WithWindow=False)
                deck.SaveAs(abs_out, 32)
                deck.Close()
            finally:
                app.Quit()
        elif doc_type == "xlsx":
            app = win32com.client.Dispatch("Excel.Application")
            app.Visible = False
            try:
                wb = app.Workbooks.Open(abs_in)
                wb.ExportAsFixedFormat(0, abs_out)
                wb.Close(False)
            finally:
                app.Quit()
        return output_path
    except Exception:
        # Cross-platform fallback: LibreOffice CLI
        out_dir = os.path.dirname(os.path.abspath(output_path))
        bin_path = shutil.which("soffice") or shutil.which("libreoffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
        cmd = [bin_path, "--headless", "--convert-to", "pdf", "--outdir", out_dir, os.path.abspath(input_path)]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        auto_name = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(input_path))[0]}.pdf")
        if os.path.abspath(auto_name) != os.path.abspath(output_path):
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(auto_name, output_path)
        return output_path