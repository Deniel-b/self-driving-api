import cv2  # type: ignore
import numpy as np
import torch
import torch.nn.functional as F
from PySide6.QtCore import QObject, Signal, Slot
from torchvision.transforms import Compose

from depth_anything.dpt import DepthAnything
from depth_anything.util.transform import Resize, NormalizeImage, PrepareForNet


class ImageProcessor(QObject):
    processedFrame = Signal(np.ndarray)

    def __init__(self, encoder="vitl", parent=None):
        super().__init__(parent)

        # Определяем устройство (CPU / CUDA)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("Using device:", self.device)

        # Загружаем модель (можно менять "vitl" на "vitb"/"vits" в зависимости от версии)
        model_name = f"LiheYoung/depth_anything_{encoder}14"
        print("Loading DepthAnything:", model_name)
        self.depth_model = DepthAnything.from_pretrained(model_name).to(self.device).eval()

        # Собираем трансформ (см. оригинальный скрипт)
        self.transform = Compose([
            Resize(
                width=518,
                height=518,
                resize_target=False,
                keep_aspect_ratio=True,
                ensure_multiple_of=14,
                resize_method='lower_bound',
                image_interpolation_method=cv2.INTER_CUBIC,
            ),
            NormalizeImage(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            PrepareForNet(),
        ])

        # Параметры отображения depth-карты
        self.colormap = cv2.COLORMAP_INFERNO  # Или COLORMAP_JET, COLORMAP_TURBO и т. д.

    @Slot(np.ndarray)
    def processFrame(self, frame_bgr: np.ndarray):
        """
        Слот, получает BGR-кадр и возвращает раскрашенную depth-карту (RGB).
        1) BGR -> RGB и делим на 255
        2) Применяем трансформ (Resize, Normalize, PrepareForNet)
        3) Прогоняем через DepthAnything
        4) Возвращаем глубину к исходному размеру, нормируем в [0..255]
        5) Накладываем colormap (требует (H, W) одноканальное)
        6) BGR -> RGB и отправляем processedFrame сигналом
        """
        # 1) BGR -> RGB, [0..1]
        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB) / 255.0

        # 2) Трансформ (увеличение/уменьшение, нормализация)
        sample = {'image': frame_rgb}
        sample = self.transform(sample)
        inp = torch.from_numpy(sample['image']).unsqueeze(0).to(self.device)  # (1, C, H', W')

        # 3) Depth inference
        with torch.no_grad():
            depth_map = self.depth_model(inp)  # обычно (B=1, H', W')

        # 4) Интерполяция под исходное (h, w)
        # Нужен формат (N, C, H, W), где C=1 для bilinear:
        depth_map_4d = depth_map.unsqueeze(1)          # (1, 1, H', W')
        depth_resized_4d = F.interpolate(
            depth_map_4d,
            size=(h, w),
            mode="bilinear",
            align_corners=False
        )  # -> (1, 1, h, w)

        # Убираем измерение каналов => (1, h, w)
        depth_resized = depth_resized_4d.squeeze(1)

        # depth_resized.shape = (1, h, w). Для colormap нужен (h, w):
        depth_resized = depth_resized.squeeze(0)  # Теперь (h, w)

        # Нормализуем [0..1], умножаем на 255 => uint8
        # (Обратите внимание: можно ещё проверить, что depth_resized.max() не ноль)
        max_val = depth_resized.max()
        if max_val > 0:
            depth_resized = depth_resized / max_val
        depth_resized = depth_resized * 255.0

        depth_uint8 = depth_resized.cpu().numpy().astype(np.uint8)  # (h, w)

        # 5) Наложение colormap
        depth_colored_bgr = cv2.applyColorMap(depth_uint8, self.colormap)

        # 6) BGR -> RGB для отображения в QLabel
        depth_colored_rgb = cv2.cvtColor(depth_colored_bgr, cv2.COLOR_BGR2RGB)

        self.processedFrame.emit(depth_colored_rgb)
