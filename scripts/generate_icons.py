"""
SoulHaven - Icon Generator
Gera icones com fundo colorido e bordas arredondadas
"""

from PIL import Image, ImageDraw
import os

# Configuracoes
BACKGROUND_COLOR = (30, 58, 95)  # #1e3a5f - Azul escuro do logo
CORNER_RADIUS_PERCENT = 20  # 20% do tamanho = bordas bem arredondadas

# Tamanhos necessarios para PWA/App Store
SIZES = [16, 32, 48, 72, 96, 128, 144, 152, 192, 256, 384, 512]

# Caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LOGO_PATH = os.path.join(PROJECT_ROOT, "logo", "icone.png")  # Novo icone limpo
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "frontend", "static", "icons")


def create_rounded_mask(size, radius):
    """Cria mascara com bordas arredondadas"""
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size-1, size-1)], radius=radius, fill=255)
    return mask


def generate_icon(logo_img, size, output_path):
    """Gera um icone mantendo o formato original, apenas redimensionando"""

    # Criar imagem base com fundo branco
    icon = Image.new('RGBA', (size, size), (255, 255, 255, 255))

    # Redimensionar logo mantendo proporcao
    logo_resized = logo_img.copy()
    logo_resized.thumbnail((size, size), Image.Resampling.LANCZOS)

    # Centralizar logo
    x = (size - logo_resized.width) // 2
    y = (size - logo_resized.height) // 2

    # Colar logo com transparencia
    if logo_resized.mode == 'RGBA':
        icon.paste(logo_resized, (x, y), logo_resized)
    else:
        icon.paste(logo_resized, (x, y))

    # Aplicar bordas arredondadas
    radius = int(size * CORNER_RADIUS_PERCENT / 100)
    mask = create_rounded_mask(size, radius)

    # Criar imagem final com bordas arredondadas
    final = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    final.paste(icon, mask=mask)

    # Salvar
    final.save(output_path, 'PNG')
    print(f"  Gerado: {os.path.basename(output_path)} ({size}x{size})")


def main():
    print("=" * 50)
    print("SoulHaven Icon Generator")
    print("=" * 50)
    print(f"\nFundo: RGB{BACKGROUND_COLOR}")
    print(f"Bordas arredondadas: {CORNER_RADIUS_PERCENT}%")
    print(f"\nCarregando logo de: {LOGO_PATH}")

    # Carregar logo original
    if not os.path.exists(LOGO_PATH):
        print(f"ERRO: Logo nao encontrado em {LOGO_PATH}")
        return

    logo = Image.open(LOGO_PATH)

    # Converter para RGBA se necessario
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')

    print(f"Logo carregado: {logo.size[0]}x{logo.size[1]}")
    print(f"\nGerando icones em: {OUTPUT_DIR}\n")

    # Criar diretorio se nao existir
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Gerar cada tamanho
    for size in SIZES:
        output_path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}-rounded.png")
        generate_icon(logo, size, output_path)

    print("\n" + "=" * 50)
    print("Icones gerados com sucesso!")
    print("=" * 50)

    # Instrucoes
    print("\nProximos passos:")
    print("1. Verifique os icones gerados na pasta frontend/static/icons/")
    print("2. Se estiverem bons, renomeie-os removendo '-rounded' do nome")
    print("3. Atualize o manifest.json se necessario")
    print("4. Incremente a versao do cache no sw.js")


if __name__ == "__main__":
    main()
