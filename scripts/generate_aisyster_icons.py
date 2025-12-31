"""
AiSYSTER - Icon Generator
Gera icones PWA com apenas "AiS" centralizado
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Configuracoes
BACKGROUND_COLOR = (255, 255, 255, 255)  # Branco
CORNER_RADIUS_PERCENT = 18  # Bordas arredondadas

# Cor do logo AiSYSTER (azul)
AISYSTER_BLUE = (66, 133, 244)  # #4285F4

# Tamanhos necessarios para PWA/App Store
SIZES = [16, 32, 48, 72, 96, 120, 128, 144, 152, 180, 192, 256, 384, 512]

# Caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "logo", "aisyster", "pwa_icons")

# Usar o logo da homepage que tem o texto completo "AiSYSTER"
SOURCE_ICON = os.path.join(PROJECT_ROOT, "logo", "aisyster", "homepage_logo_2000x800.png")


def create_rounded_mask(size, radius):
    """Cria mascara com bordas arredondadas"""
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size-1, size-1)], radius=radius, fill=255)
    return mask


def generate_icon_from_source(source_img, size, output_path, apply_rounded=True):
    """Gera um icone a partir da imagem fonte, centralizando o conteudo"""

    # Criar imagem base com fundo branco
    icon = Image.new('RGBA', (size, size), BACKGROUND_COLOR)

    # A imagem fonte tem o logo cortado, precisamos usar a parte util
    # Vamos pegar a bbox do conteudo (area nao transparente)
    if source_img.mode == 'RGBA':
        # Encontrar a bounding box do conteudo
        bbox = source_img.getbbox()
        if bbox:
            # Recortar apenas o conteudo
            content = source_img.crop(bbox)
        else:
            content = source_img
    else:
        content = source_img

    # Calcular tamanho para o conteudo ocupar ~75% do icone
    target_size = int(size * 0.75)

    # Redimensionar mantendo proporcao
    content_copy = content.copy()
    content_copy.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

    # Centralizar
    x = (size - content_copy.width) // 2
    y = (size - content_copy.height) // 2

    # Colar com transparencia
    if content_copy.mode == 'RGBA':
        icon.paste(content_copy, (x, y), content_copy)
    else:
        icon.paste(content_copy, (x, y))

    if apply_rounded:
        # Aplicar bordas arredondadas
        radius = int(size * CORNER_RADIUS_PERCENT / 100)
        mask = create_rounded_mask(size, radius)

        # Criar imagem final com bordas arredondadas
        final = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        final.paste(icon, mask=mask)
    else:
        final = icon

    # Salvar
    final.save(output_path, 'PNG')
    print(f"  Gerado: {os.path.basename(output_path)} ({size}x{size})")
    return final


def main():
    print("=" * 50)
    print("AiSYSTER PWA Icon Generator")
    print("=" * 50)

    # Criar diretorio de saida
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Carregar imagem fonte
    if not os.path.exists(SOURCE_ICON):
        print(f"ERRO: Arquivo fonte nao encontrado: {SOURCE_ICON}")
        return

    source = Image.open(SOURCE_ICON)
    if source.mode != 'RGBA':
        source = source.convert('RGBA')

    print(f"\nFonte: {SOURCE_ICON}")
    print(f"Tamanho original: {source.size}")
    print(f"\nGerando icones em: {OUTPUT_DIR}\n")

    # Gerar cada tamanho
    for size in SIZES:
        output_path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}.png")
        generate_icon_from_source(source, size, output_path)

    # Gerar versao maskable (com mais padding para Android)
    print("\nGerando icones maskable (Android)...")
    for size in [192, 512]:
        # Maskable precisa de ~10% de safe zone em cada lado
        # Entao o conteudo ocupa ~80% do centro
        icon = Image.new('RGBA', (size, size), BACKGROUND_COLOR)

        # Bbox do conteudo
        bbox = source.getbbox()
        if bbox:
            content = source.crop(bbox)
        else:
            content = source

        # Para maskable, conteudo ocupa 60% (mais margem)
        target_size = int(size * 0.60)
        content_copy = content.copy()
        content_copy.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

        x = (size - content_copy.width) // 2
        y = (size - content_copy.height) // 2

        if content_copy.mode == 'RGBA':
            icon.paste(content_copy, (x, y), content_copy)
        else:
            icon.paste(content_copy, (x, y))

        output_path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}-maskable.png")
        icon.save(output_path, 'PNG')
        print(f"  Gerado: icon-{size}x{size}-maskable.png")

    print("\n" + "=" * 50)
    print("Icones gerados com sucesso!")
    print("=" * 50)

    # Copiar os principais para a pasta raiz do aisyster
    print("\nCopiando icones principais...")
    import shutil

    main_icons = [
        (os.path.join(OUTPUT_DIR, "icon-512x512.png"), os.path.join(PROJECT_ROOT, "logo", "aisyster", "pwa_icon_512_fixed.png")),
        (os.path.join(OUTPUT_DIR, "icon-192x192.png"), os.path.join(PROJECT_ROOT, "logo", "aisyster", "pwa_icon_192_fixed.png")),
    ]

    for src, dst in main_icons:
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"  Copiado: {os.path.basename(dst)}")


if __name__ == "__main__":
    main()
