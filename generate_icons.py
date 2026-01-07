"""
Script para gerar ícones PWA do AiSyster
Gera ícones PNG em vários tamanhos com o "S" dourado
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Diretório de saída
OUTPUT_DIR = "/tmp/icons"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cores
GOLD_START = (212, 160, 86)  # #d4a056
GOLD_END = (184, 134, 11)    # #b8860b
WHITE = (255, 255, 255)

# Tamanhos necessários para PWA
SIZES = [16, 32, 72, 96, 128, 144, 152, 167, 180, 192, 384, 512]

def create_gradient(size):
    """Cria um gradiente diagonal"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for y in range(size):
        for x in range(size):
            # Calcular posição no gradiente (diagonal)
            t = (x + y) / (2 * size)
            r = int(GOLD_START[0] + (GOLD_END[0] - GOLD_START[0]) * t)
            g = int(GOLD_START[1] + (GOLD_END[1] - GOLD_START[1]) * t)
            b = int(GOLD_START[2] + (GOLD_END[2] - GOLD_START[2]) * t)
            img.putpixel((x, y), (r, g, b, 255))

    return img

def create_icon(size):
    """Cria um ícone com o S no centro"""
    # Criar imagem com gradiente
    img = create_gradient(size)
    draw = ImageDraw.Draw(img)

    # Criar máscara para bordas arredondadas
    corner_radius = size // 5
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=corner_radius,
        fill=255
    )

    # Aplicar máscara
    img.putalpha(mask)

    # Desenhar o "S"
    font_size = int(size * 0.55)
    try:
        # Tentar usar uma fonte do sistema
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # Calcular posição do texto
    text = "S"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]  # Ajuste para centralização vertical

    draw.text((x, y), text, fill=WHITE, font=font)

    return img

def main():
    print("Gerando ícones PWA do AiSyster...")

    for size in SIZES:
        icon = create_icon(size)
        filename = f"icon-{size}x{size}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        icon.save(filepath, "PNG")
        print(f"  Criado: {filename}")

    # Criar também favicon.ico (16x16 e 32x32)
    icon16 = create_icon(16)
    icon32 = create_icon(32)
    ico_path = os.path.join(OUTPUT_DIR, "favicon.ico")
    icon32.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32)])
    print(f"  Criado: favicon.ico")

    print("\nTodos os ícones foram gerados com sucesso!")

if __name__ == "__main__":
    main()
