import os
import sys
import cv2
import torch
import logging
from bot.config import GFPGAN_MODEL_PATH

# Добавляем путь к GFPGAN в PYTHONPATH
gfpgan_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'GFPGAN')
sys.path.append(gfpgan_path)

# Импортируем GFPGAN
try:
    from gfpgan import GFPGANer
except ImportError as e:
    logging.error(f"Ошибка импорта GFPGAN: {e}")
    raise

logger = logging.getLogger(__name__)

def process_image(input_path, output_path):
    """
    Обработка изображения с помощью GFPGAN.
    
    Args:
        input_path (str): Путь к входному изображению
        output_path (str): Путь для сохранения обработанного изображения
    """
    try:
        logger.info(f"Начало обработки изображения: {input_path}")
        
        # Проверяем наличие входного файла
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Входной файл не найден: {input_path}")
            
        # Проверяем наличие модели
        if not os.path.exists(GFPGAN_MODEL_PATH):
            raise FileNotFoundError(f"Файл модели не найден: {GFPGAN_MODEL_PATH}")
        
        # Инициализация модели
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Используется устройство: {device}")
        
        model = GFPGANer(
            model_path=GFPGAN_MODEL_PATH,
            upscale=2,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=None,
            device=device
        )
        
        # Загрузка изображения
        img = cv2.imread(input_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Не удалось загрузить изображение")
            
        # Обработка изображения
        _, _, output = model.enhance(
            img,
            has_aligned=False,
            only_center_face=False,
            paste_back=True
        )
        
        # Сохранение результата
        cv2.imwrite(output_path, output)
        
        logger.info(f"Изображение успешно обработано и сохранено: {output_path}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}")
        raise