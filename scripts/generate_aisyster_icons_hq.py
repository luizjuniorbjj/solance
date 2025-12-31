"""
AiSYSTER - High Quality Icon Generator
Gera icones PWA de alta qualidade com "AiS" estilizado
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Configuracoes
BACKGROUND_COLOR = (255, 255, 255, 255)  # Branco
CORNER_RADIUS_PERCENT = 18  # Bordas arredondadas

# Cores do logo AiSYSTER
AISYSTER_BLUE_LIGHT = (100, 149, 237)  # Azul claro do "Ai"
AISYSTER_BLUE_DARK = (65, 105, 225)    # Azul escuro do "S"

# Tamanhos necessarios para PWA/App Store
SIZES = [16, 32, 48, 72, 96, 120, 128, 144, 152, 180, 192, 256, 384, 512, 1024]

# Caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "logo", "aisyster", "pwa_icons_hq")

# Usar o logo original em alta resolucao
SOURCE_LOGO = os.path.join(PROJECT_ROOT, "logo", "aisyster", "logo_original.png")


def create_rounded_mask(size, radius):
    """Cria mascara com bordas arredondadas"""
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size-1, size-1)], radius=radius, fill=255)
    return mask


def extract_ais_from_logo(source_path):
    """Extrai apenas a parte 'AiS' do logo completo"""
    img = Image.open(source_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # O logo tem 2000x800
    # "AiS" ocupa aproximadamente os primeiros 45% da largura
    # Vamos pegar uma area quadrada focada no "AiS"

    width, height = img.size

    # Encontrar bounding box do conteudo
    bbox = img.getbbox()
    if bbox:
        left, top, right, bottom = bbox
        content_width = right - left
        content_height = bottom - top

        # Pegar apenas a parte "AiS" (aproximadamente 63% do lado esquerdo - S completo sem Y)
        ais_right = left + int(content_width * 0.63)

        # Recortar "AiS"
        ais_crop = img.crop((left, top, ais_right, bottom))

        return ais_crop

    return img


def generate_hq_icon(content_img, size, output_path, apply_rounded=True):
    """Gera um icone de alta qualidade"""

    # Criar imagem base com fundo branco em alta resolucao
    # Trabalhar em 4x o tamanho e depois reduzir para antialiasing
    work_size = size * 4 if size < 512 else size * 2

    icon = Image.new('RGBA', (work_size, work_size), BACKGROUND_COLOR)

    # Redimensionar conteudo para ocupar ~70% do icone
    target_size = int(work_size * 0.70)

    content_copy = content_img.copy()

    # Manter proporcao
    aspect = content_copy.width / content_copy.height
    if aspect > 1:
        # Mais largo que alto
        new_width = target_size
        new_height = int(target_size / aspect)
    else:
        new_height = target_size
        new_width = int(target_size * aspect)

    # Redimensionar com alta qualidade
    content_resized = content_copy.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Centralizar
    x = (work_size - new_width) // 2
    y = (work_size - new_height) // 2

    # Colar com transparencia
    if content_resized.mode == 'RGBA':
        icon.paste(content_resized, (x, y), content_resized)
    else:
        icon.paste(content_resized, (x, y))

    # Reduzir para o tamanho final com alta qualidade
    if work_size != size:
        icon = icon.resize((size, size), Image.Resampling.LANCZOS)

    if apply_rounded:
        # Aplicar bordas arredondadas
        radius = int(size * CORNER_RADIUS_PERCENT / 100)
        mask = create_rounded_mask(size, radius)

        # Criar imagem final com bordas arredondadas
        final = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        final.paste(icon, mask=mask)
    else:
        final = icon

    # Salvar com alta qualidade
    final.save(output_path, 'PNG', optimize=False)
    print(f"  Gerado: {os.path.basename(output_path)} ({size}x{size})")
    return final


def main():
    print("=" * 50)
    print("AiSYSTER HQ PWA Icon Generator")
    print("=" * 50)

    # Criar diretorio de saida
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Extrair "AiS" do logo
    if not os.path.exists(SOURCE_LOGO):
        print(f"ERRO: Arquivo fonte nao encontrado: {SOURCE_LOGO}")
        return

    print(f"\nExtraindo 'AiS' do logo: {SOURCE_LOGO}")
    ais_content = extract_ais_from_logo(SOURCE_LOGO)
    print(f"Tamanho do recorte: {ais_content.size}")

    # Salvar o recorte para verificacao
    ais_path = os.path.join(OUTPUT_DIR, "ais_extracted.png")
    ais_content.save(ais_path, 'PNG')
    print(f"Recorte salvo em: {ais_path}")

    print(f"\nGerando icones em: {OUTPUT_DIR}\n")

    # Gerar cada tamanho
    for size in SIZES:
        output_path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}.png")
        generate_hq_icon(ais_content, size, output_path)

    # Gerar versao maskable (com mais padding para Android)
    print("\nGerando icones maskable (Android)...")
    for size in [192, 512]:
        # Maskable precisa de ~10% de safe zone em cada lado
        work_size = size * 4 if size < 512 else size * 2

        icon = Image.new('RGBA', (work_size, work_size), BACKGROUND_COLOR)

        # Para maskable, conteudo ocupa 55% (mais margem para safe zone)
        target_size = int(work_size * 0.55)

        content_copy = ais_content.copy()
        aspect = content_copy.width / content_copy.height
        if aspect > 1:
            new_width = target_size
            new_height = int(target_size / aspect)
        else:
            new_height = target_size
            new_width = int(target_size * aspect)

        content_resized = content_copy.resize((new_width, new_height), Image.Resampling.LANCZOS)

        x = (work_size - new_width) // 2
        y = (work_size - new_height) // 2

        if content_resized.mode == 'RGBA':
            icon.paste(content_resized, (x, y), content_resized)
        else:
            icon.paste(content_resized, (x, y))

        # Reduzir para tamanho final
        if work_size != size:
            icon = icon.resize((size, size), Image.Resampling.LANCZOS)

        output_path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}-maskable.png")
        icon.save(output_path, 'PNG', optimize=False)
        print(f"  Gerado: icon-{size}x{size}-maskable.png")

    print("\n" + "=" * 50)
    print("Icones HQ gerados com sucesso!")
    print("=" * 50)

    # Copiar os principais
    print("\nCopiando icones principais...")
    import shutil

    main_icons = [
        (os.path.join(OUTPUT_DIR, "icon-512x512.png"), os.path.join(PROJECT_ROOT, "logo", "aisyster", "pwa_icon_512_hq.png")),
        (os.path.join(OUTPUT_DIR, "icon-192x192.png"), os.path.join(PROJECT_ROOT, "logo", "aisyster", "pwa_icon_192_hq.png")),
    ]

    for src, dst in main_icons:
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"  Copiado: {os.path.basename(dst)}")


if __name__ == "__main__":
    main()
