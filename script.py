from PIL import Image
import pillow_heif
import os
import argparse
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None


def calculate_new_size(width, height, target_width=1920, target_height=1080):
    """
    Calcula as novas dimensões mantendo a proporção da imagem.
    """
    aspect_ratio = width / height
    target_ratio = target_width / target_height

    if aspect_ratio > target_ratio:
        # Imagem é mais larga que 16:9
        new_width = target_width
        new_height = int(new_width / aspect_ratio)
    else:
        # Imagem é mais alta que 16:9
        new_height = target_height
        new_width = int(new_height * aspect_ratio)

    return (new_width, new_height)


def optimize_png(image):
    """
    Otimiza uma imagem PNG usando diferentes métodos de otimização.
    """
    if image.mode in ('RGBA', 'RGB'):
        try:
            quantized = image.quantize(colors=256, method=2, kmeans=1)
            if quantized.mode == 'P':
                return quantized
        except Exception:
            pass
    return image


def convert_heic(input_path, output_format='PNG', compression_level='medium'):
    """
    Converte uma imagem HEIC para PNG ou JPEG com redimensionamento para Full HD.

    Args:
        input_path (str): Caminho do arquivo HEIC
        output_format (str): Formato de saída desejado ('PNG' ou 'JPEG')
        compression_level (str): Nível de compressão ('low', 'medium', 'high')
    """
    pillow_heif.register_heif_opener()

    try:
        filename = os.path.splitext(input_path)[0]
        original_size = os.path.getsize(input_path)
        heic_image = Image.open(input_path)

        # Mantém as dimensões originais para referência
        original_dimensions = heic_image.size

        # Calcula e aplica o novo tamanho
        if original_dimensions[0] > 1920 or original_dimensions[1] > 1080:
            new_dimensions = calculate_new_size(
                original_dimensions[0], original_dimensions[1])
            heic_image = heic_image.resize(
                new_dimensions, Image.Resampling.LANCZOS)

        # Define parâmetros de compressão baseado no nível escolhido
        if compression_level == 'low':
            jpeg_quality = 95
            png_optimize = False
        elif compression_level == 'medium':
            jpeg_quality = 85
            png_optimize = True
        else:  # high
            jpeg_quality = 75
            png_optimize = True

        output_format = output_format.upper()
        if output_format not in ['PNG', 'JPEG']:
            raise ValueError("Formato de saída deve ser 'PNG' ou 'JPEG'")

        output_path = f"{filename}.{output_format.lower()}"

        if output_format == 'PNG':
            # Otimiza PNG
            if heic_image.mode in ('RGBA', 'LA'):
                # Mantém transparência
                optimized_image = optimize_png(heic_image)
                optimized_image.save(
                    output_path,
                    format='PNG',
                    optimize=png_optimize,
                    compress_level=9
                )
            else:
                # Converte para RGB e otimiza
                rgb_image = heic_image.convert('RGB')
                optimized_image = optimize_png(rgb_image)
                optimized_image.save(
                    output_path,
                    format='PNG',
                    optimize=png_optimize,
                    compress_level=9
                )
        else:  # JPEG
            if heic_image.mode in ('RGBA', 'LA'):
                heic_image = heic_image.convert('RGB')

            heic_image.save(
                output_path,
                format='JPEG',
                quality=jpeg_quality,
                optimize=True,
                progressive=True
            )

        # Calcula e mostra estatísticas
        final_size = os.path.getsize(output_path)
        compression_ratio = (1 - (final_size / original_size)) * 100

        print(f"\nConversão concluída com sucesso:")
        print(f"Arquivo original: {input_path}")
        print(f"Arquivo convertido: {output_path}")
        print(f"Dimensões originais: {original_dimensions}")
        print(f"Dimensões finais: {heic_image.size}")
        print(f"Tamanho original: {original_size/1024/1024:.2f} MB")
        print(f"Tamanho final: {final_size/1024/1024:.2f} MB")
        print(f"Taxa de compressão: {compression_ratio:.1f}%")

    except Exception as e:
        print(f"Erro ao converter a imagem: {str(e)}")


def convert_directory(directory_path, output_format='PNG', compression_level='medium'):
    """
    Converte todas as imagens HEIC em um diretório.
    """
    for filename in os.listdir(directory_path):
        if filename.lower().endswith('.heic'):
            input_path = os.path.join(directory_path, filename)
            convert_heic(input_path, output_format, compression_level)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Conversor de HEIC para PNG/JPEG com redimensionamento Full HD')
    parser.add_argument('path', help='Caminho do arquivo ou diretório')
    parser.add_argument('--format', choices=['png', 'jpeg'], default='jpeg',
                        help='Formato de saída (png ou jpeg)')
    parser.add_argument('--compression', choices=['low', 'medium', 'high'],
                        default='medium', help='Nível de compressão')

    args = parser.parse_args()

    if os.path.isfile(args.path):
        convert_heic(args.path, args.format.upper(), args.compression)
    elif os.path.isdir(args.path):
        convert_directory(args.path, args.format.upper(), args.compression)
    else:
        print("Caminho inválido")
