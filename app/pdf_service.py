"""
AiSyster - Serviço de PDF
Converte PDFs em imagens para análise pelo Claude
"""

import io
import base64
from typing import List, Tuple

import pypdfium2 as pdfium


# Configurações
MAX_PDF_PAGES = 5  # Máximo de páginas por PDF
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB
DPI = 150  # Resolução das imagens (150 é bom equilíbrio qualidade/tamanho)


def pdf_to_images(pdf_bytes: bytes) -> List[Tuple[str, str]]:
    """
    Converte PDF em lista de imagens base64.

    Args:
        pdf_bytes: Bytes do arquivo PDF

    Returns:
        Lista de tuplas (base64_data, media_type)

    Raises:
        ValueError: Se PDF inválido ou muito grande
    """
    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise ValueError(f"PDF muito grande. Máximo {MAX_PDF_SIZE // (1024*1024)}MB.")

    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
    except Exception as e:
        raise ValueError(f"PDF inválido ou corrompido: {str(e)}")

    n_pages = len(pdf)
    if n_pages == 0:
        raise ValueError("PDF está vazio.")

    # Limitar número de páginas
    pages_to_process = min(n_pages, MAX_PDF_PAGES)

    images = []
    for i in range(pages_to_process):
        page = pdf[i]

        # Renderizar página como imagem
        # scale = DPI / 72 (72 é o DPI padrão do PDF)
        scale = DPI / 72
        bitmap = page.render(scale=scale)

        # Converter para PIL Image
        pil_image = bitmap.to_pil()

        # Converter para JPEG (menor tamanho que PNG)
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='JPEG', quality=85, optimize=True)
        img_bytes = img_buffer.getvalue()

        # Converter para base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        images.append((img_base64, 'image/jpeg'))

        # Limpar memória
        bitmap.close()

    pdf.close()

    return images


def get_pdf_info(pdf_bytes: bytes) -> dict:
    """
    Retorna informações sobre o PDF.

    Returns:
        {
            "pages": int,
            "pages_to_process": int,
            "size_mb": float
        }
    """
    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
        n_pages = len(pdf)
        pdf.close()

        return {
            "pages": n_pages,
            "pages_to_process": min(n_pages, MAX_PDF_PAGES),
            "size_mb": round(len(pdf_bytes) / (1024 * 1024), 2)
        }
    except Exception:
        return {
            "pages": 0,
            "pages_to_process": 0,
            "size_mb": round(len(pdf_bytes) / (1024 * 1024), 2)
        }
