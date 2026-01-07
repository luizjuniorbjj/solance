"""
Script para gerar ícones PWA a partir do logo do AiSyster
Extrai apenas o símbolo (sem texto) para ícones do app
"""
from PIL import Image
import os

# Diretório de saída
OUTPUT_DIR = "frontend/static/icons"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Carregar logo original (símbolo isolado, sem texto)
LOGO_PATH = "logo/logo-header.png"

# Tamanhos necessários para PWA
SIZES = [16, 32, 72, 96, 128, 144, 152, 167, 180, 192, 384, 512]

def extract_icon_from_logo(logo_path):
    """
    Usa o logo do símbolo e recorta para remover espaço vazio
    """
    img = Image.open(logo_path)
    width, height = img.size

    # O logo tem espaço vazio ao redor - recortar apenas o símbolo
    # Baseado nas dimensões 1536x1024
    crop_left = int(width * 0.22)
    crop_right = int(width * 0.78)
    crop_top = int(height * 0.15)
    crop_bottom = int(height * 0.85)

    # Recortar símbolo
    symbol = img.crop((crop_left, crop_top, crop_right, crop_bottom))

    # Converter para RGBA
    if symbol.mode != 'RGBA':
        symbol = symbol.convert('RGBA')

    # Criar imagem quadrada com fundo branco
    symbol_size = max(symbol.width, symbol.height)
    padding = int(symbol_size * 0.08)  # 8% de margem
    final_size = symbol_size + (padding * 2)

    final_icon = Image.new('RGBA', (final_size, final_size), (255, 255, 255, 255))

    # Centralizar símbolo
    x_offset = (final_size - symbol.width) // 2
    y_offset = (final_size - symbol.height) // 2

    final_icon.paste(symbol, (x_offset, y_offset), symbol)

    return final_icon

def create_icon(icon_img, size):
    """
    Redimensiona o ícone para o tamanho especificado
    """
    # Redimensionar mantendo qualidade
    resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)

    # Converter para RGBA se necessário
    if resized.mode != 'RGBA':
        resized = resized.convert('RGBA')

    return resized

def main():
    print("Gerando ícones PWA do AiSyster a partir do logo...")

    # Extrair ícone do logo
    print("  Extraindo ícone do logo...")
    icon_base = extract_icon_from_logo(LOGO_PATH)

    # Salvar ícone base para referência
    icon_base.save(os.path.join(OUTPUT_DIR, "icon-base.png"), "PNG")
    print("  Salvo: icon-base.png")

    # Gerar cada tamanho
    for size in SIZES:
        icon = create_icon(icon_base, size)
        filename = f"icon-{size}x{size}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        icon.save(filepath, "PNG")
        print(f"  Criado: {filename}")

    # Criar favicon.ico
    icon16 = create_icon(icon_base, 16)
    icon32 = create_icon(icon_base, 32)
    icon48 = create_icon(icon_base, 48)
    ico_path = os.path.join(OUTPUT_DIR, "favicon.ico")
    icon32.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print("  Criado: favicon.ico")

    # Também salvar o logo completo em tamanhos úteis
    full_logo = Image.open(LOGO_PATH)

    # Logo para header (altura ~40px)
    logo_height = 60
    ratio = logo_height / full_logo.height
    logo_width = int(full_logo.width * ratio)
    logo_header = full_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    logo_header.save(os.path.join(OUTPUT_DIR, "logo-header.png"), "PNG")
    print("  Criado: logo-header.png")

    # Logo médio para welcome screen
    logo_height = 120
    ratio = logo_height / full_logo.height
    logo_width = int(full_logo.width * ratio)
    logo_medium = full_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    logo_medium.save(os.path.join(OUTPUT_DIR, "logo-medium.png"), "PNG")
    print("  Criado: logo-medium.png")

    # Logo grande para landing
    logo_height = 200
    ratio = logo_height / full_logo.height
    logo_width = int(full_logo.width * ratio)
    logo_large = full_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    logo_large.save(os.path.join(OUTPUT_DIR, "logo-large.png"), "PNG")
    print("  Criado: logo-large.png")

    print("\nTodos os ícones foram gerados com sucesso!")

if __name__ == "__main__":
    main()
