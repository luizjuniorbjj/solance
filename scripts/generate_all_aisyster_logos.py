"""
AiSYSTER - Complete Logo Generator
Gera todos os logos necessarios a partir do logo_original.png
"""

from PIL import Image, ImageDraw
import os
import shutil

# Configuracoes
BACKGROUND_COLOR = (255, 255, 255, 255)  # Branco
CORNER_RADIUS_PERCENT = 18  # Bordas arredondadas para PWA icons

# Tamanhos necessarios para PWA/App Store
PWA_SIZES = [16, 32, 48, 72, 96, 120, 128, 144, 152, 180, 192, 256, 384, 512, 1024]

# Caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SOURCE_LOGO = os.path.join(PROJECT_ROOT, "logo", "aisyster", "logo_original.png")
SOURCE_AIS = os.path.join(PROJECT_ROOT, "logo", "aisyster", "logo_original_ais.png")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "logo", "aisyster")


def create_rounded_mask(size, radius):
    """Cria mascara com bordas arredondadas"""
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size-1, size-1)], radius=radius, fill=255)
    return mask


def extract_ais_from_logo(img):
    """Extrai apenas a parte 'AiS' do logo completo"""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Encontrar bounding box do conteudo
    bbox = img.getbbox()
    if bbox:
        left, top, right, bottom = bbox
        content_width = right - left

        # Pegar apenas a parte "AiS" (51.5% - melhor compromisso entre S completo e sem Y)
        ais_right = left + int(content_width * 0.515)

        # Recortar "AiS"
        ais_crop = img.crop((left, top, ais_right, bottom))
        return ais_crop

    return img


def generate_pwa_icon(content_img, size, output_path, apply_rounded=True):
    """Gera um icone PWA de alta qualidade"""
    # Trabalhar em 4x o tamanho para antialiasing
    work_size = size * 4 if size < 512 else size * 2

    icon = Image.new('RGBA', (work_size, work_size), BACKGROUND_COLOR)

    # Conteudo ocupa ~70% do icone
    target_size = int(work_size * 0.70)

    content_copy = content_img.copy()

    # Manter proporcao
    aspect = content_copy.width / content_copy.height
    if aspect > 1:
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

    # Reduzir para o tamanho final
    if work_size != size:
        icon = icon.resize((size, size), Image.Resampling.LANCZOS)

    if apply_rounded:
        radius = int(size * CORNER_RADIUS_PERCENT / 100)
        mask = create_rounded_mask(size, radius)
        final = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        final.paste(icon, mask=mask)
    else:
        final = icon

    final.save(output_path, 'PNG', optimize=False)
    return final


def generate_header_logo(source_img, output_path, height=50):
    """Gera logo para header do site"""
    if source_img.mode != 'RGBA':
        source_img = source_img.convert('RGBA')

    bbox = source_img.getbbox()
    if bbox:
        content = source_img.crop(bbox)
    else:
        content = source_img

    # Calcular largura proporcional
    aspect = content.width / content.height
    new_width = int(height * aspect)

    # Redimensionar
    resized = content.resize((new_width, height), Image.Resampling.LANCZOS)
    resized.save(output_path, 'PNG')
    return resized


def generate_email_logo(source_img, output_path, width=600, height=200):
    """Gera logo para emails"""
    if source_img.mode != 'RGBA':
        source_img = source_img.convert('RGBA')

    # Criar imagem com fundo branco
    email_img = Image.new('RGBA', (width, height), BACKGROUND_COLOR)

    bbox = source_img.getbbox()
    if bbox:
        content = source_img.crop(bbox)
    else:
        content = source_img

    # Conteudo ocupa 80% da altura
    target_height = int(height * 0.80)
    aspect = content.width / content.height
    target_width = int(target_height * aspect)

    if target_width > width * 0.90:
        target_width = int(width * 0.90)
        target_height = int(target_width / aspect)

    resized = content.resize((target_width, target_height), Image.Resampling.LANCZOS)

    # Centralizar
    x = (width - target_width) // 2
    y = (height - target_height) // 2

    if resized.mode == 'RGBA':
        email_img.paste(resized, (x, y), resized)
    else:
        email_img.paste(resized, (x, y))

    email_img.save(output_path, 'PNG')
    return email_img


def generate_homepage_logo(source_img, output_path, width=2000, height=800):
    """Gera logo para homepage"""
    if source_img.mode != 'RGBA':
        source_img = source_img.convert('RGBA')

    # Criar imagem com fundo transparente
    homepage_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))

    bbox = source_img.getbbox()
    if bbox:
        content = source_img.crop(bbox)
    else:
        content = source_img

    # Conteudo ocupa 70% da altura
    target_height = int(height * 0.70)
    aspect = content.width / content.height
    target_width = int(target_height * aspect)

    if target_width > width * 0.90:
        target_width = int(width * 0.90)
        target_height = int(target_width / aspect)

    resized = content.resize((target_width, target_height), Image.Resampling.LANCZOS)

    # Centralizar
    x = (width - target_width) // 2
    y = (height - target_height) // 2

    if resized.mode == 'RGBA':
        homepage_img.paste(resized, (x, y), resized)
    else:
        homepage_img.paste(resized, (x, y))

    homepage_img.save(output_path, 'PNG')
    return homepage_img


def main():
    print("=" * 60)
    print("AiSYSTER Complete Logo Generator")
    print("=" * 60)

    # Verificar fonte
    if not os.path.exists(SOURCE_LOGO):
        print(f"ERRO: Logo original nao encontrado: {SOURCE_LOGO}")
        return

    # Carregar logo original
    source = Image.open(SOURCE_LOGO)
    if source.mode != 'RGBA':
        source = source.convert('RGBA')

    print(f"\nFonte: {SOURCE_LOGO}")
    print(f"Tamanho: {source.size}")

    # Criar diretorios
    pwa_dir = os.path.join(OUTPUT_DIR, "pwa_icons")
    os.makedirs(pwa_dir, exist_ok=True)

    # ===== 1. PWA ICONS (apenas "AiS") =====
    print("\n" + "=" * 40)
    print("1. Gerando PWA Icons (AiS)")
    print("=" * 40)

    # Usar arquivo AiS dedicado se existir
    if os.path.exists(SOURCE_AIS):
        ais_content = Image.open(SOURCE_AIS)
        if ais_content.mode != 'RGBA':
            ais_content = ais_content.convert('RGBA')
        print(f"Usando AiS dedicado: {SOURCE_AIS}")
        print(f"Tamanho AiS: {ais_content.size}")
    else:
        ais_content = extract_ais_from_logo(source)
        print(f"Recorte AiS: {ais_content.size}")

    # O arquivo AiS ja vem com bordas arredondadas, nao aplicar novamente
    apply_rounded = not os.path.exists(SOURCE_AIS)

    for size in PWA_SIZES:
        output_path = os.path.join(pwa_dir, f"icon-{size}x{size}.png")
        generate_pwa_icon(ais_content, size, output_path, apply_rounded=apply_rounded)
        print(f"  Gerado: icon-{size}x{size}.png")

    # Copiar principais
    shutil.copy(
        os.path.join(pwa_dir, "icon-512x512.png"),
        os.path.join(OUTPUT_DIR, "pwa_icon_512.png")
    )
    shutil.copy(
        os.path.join(pwa_dir, "icon-192x192.png"),
        os.path.join(OUTPUT_DIR, "pwa_icon_192.png")
    )
    print("  Copiado: pwa_icon_512.png")
    print("  Copiado: pwa_icon_192.png")

    # Maskable icons
    print("\nGerando icones maskable...")
    for size in [192, 512]:
        work_size = size * 4 if size < 512 else size * 2
        icon = Image.new('RGBA', (work_size, work_size), BACKGROUND_COLOR)

        # Conteudo ocupa 55% para safe zone
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

        if work_size != size:
            icon = icon.resize((size, size), Image.Resampling.LANCZOS)

        output_path = os.path.join(pwa_dir, f"icon-{size}x{size}-maskable.png")
        icon.save(output_path, 'PNG')
        print(f"  Gerado: icon-{size}x{size}-maskable.png")

    # ===== 2. HEADER LOGO =====
    print("\n" + "=" * 40)
    print("2. Gerando Header Logo")
    print("=" * 40)

    header_path = os.path.join(OUTPUT_DIR, "header_logo_h50.png")
    generate_header_logo(source, header_path, height=50)
    print(f"  Gerado: header_logo_h50.png")

    # ===== 3. EMAIL LOGO =====
    print("\n" + "=" * 40)
    print("3. Gerando Email Logo")
    print("=" * 40)

    email_path = os.path.join(OUTPUT_DIR, "email_logo_600x200.png")
    generate_email_logo(source, email_path, width=600, height=200)
    print(f"  Gerado: email_logo_600x200.png")

    # ===== 4. HOMEPAGE LOGO =====
    print("\n" + "=" * 40)
    print("4. Gerando Homepage Logo")
    print("=" * 40)

    homepage_path = os.path.join(OUTPUT_DIR, "homepage_logo_2000x800.png")
    generate_homepage_logo(source, homepage_path, width=2000, height=800)
    print(f"  Gerado: homepage_logo_2000x800.png")

    print("\n" + "=" * 60)
    print("Todos os logos gerados com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    main()
