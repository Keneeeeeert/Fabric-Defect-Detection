import fitz  # PyMuPDF
import sys

def pdf_to_png(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            # Increase resolution
            zoom_x = 2.0
            zoom_y = 2.0
            mat = fitz.Matrix(zoom_x, zoom_y)
            pix = page.get_pixmap(matrix=mat)
            out_name = f"page_{i+1}.png"
            pix.save(out_name)
            print(f"Saved {out_name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    pdf_to_png("实验报告.pdf")
