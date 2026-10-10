"""
Wrapper لكشف أضرار العربيات بـ YOLOv8.

الفكرة:
- نحمّل الموديل مرة واحدة ونخليه في الرام (Singleton)
- نغلف نتايج YOLO المعقدة في dict بسيط
- نضيف أسماء عربية للعرض
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from ultralytics import YOLO

# أسماء الكلاسات بالعربي
CLASS_NAMES_AR: Dict[str, str] = {
    "crack":         "شرخ",
    "dent":          "انبعاج",
    "glass shatter": "كسر زجاج",
    "lamp broken":   "كسر فانوس",
    "scratch":       "خدش",
    "tire flat":     "إطار مفرغ", }

class CarDamageDetector:
    """
    Wrapper لـ YOLOv8.
    
    الاستخدام:
        detector = CarDamageDetector.get_instance("models/best.pt")
        detections = detector.predict(image_array)
    """

    # ─── Singleton ───
    _instance: Optional["CarDamageDetector"] = None

    def __init__(
        self,
        model_path: str,
        conf: float = 0.25,
        iou: float = 0.45,
    ):
        """
        Args:
            model_path: مسار ملف الموديل (.pt)
            conf:       حد الثقة الأدنى للكشف (0-1)
            iou:        حد الـ IoU لدمج البوكسات المتداخلة
        """
        # التحقق من وجود الموديل
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model not found at: {model_path}")

        # تحميل الموديل
        self.model = YOLO(model_path)
        self.conf = conf
        self.iou = iou
        # خريطة {0: 'crack', 1: 'dent', ...}
        self.class_names: Dict[int, str] = self.model.names

    # Singleton Accessor

    @classmethod
    def get_instance(cls, model_path: str, **kwargs) -> "CarDamageDetector":
        """
        بيرجع نفس الـ instance في كل مرة.
        أول مرة بيعمل واحد جديد، وبعدها بيرجع نفسه.
        """
        if cls._instance is None:
            cls._instance = cls(model_path, **kwargs)
        return cls._instance

    # Core: Predict

    def predict(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        يعمل inference على صورة numpy array (BGR).
        
        Returns:
            قائمة من الـ detections، كل واحدة:
            {
                "class_id":     0,
                "class_name":   "crack",
                "class_name_ar": "شرخ",
                "confidence":   0.85,
                "bbox":         [x1, y1, x2, y2],
                "area":         12345.0,
            }
        """
        results = self.model.predict(
            image,
            conf=self.conf,
            iou=self.iou,
            verbose=False,
        )

        detections: List[Dict[str, Any]] = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                cls_id = int(box.cls[0])
                name = self.class_names.get(cls_id, str(cls_id))

                # إحداثيات البوكس
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())

                detections.append({
                    "class_id":      cls_id,
                    "class_name":    name,
                    "class_name_ar": CLASS_NAMES_AR.get(name, ""),
                    "confidence":    round(float(box.conf[0]), 4),
                    "bbox":          [
                        round(x1, 2),
                        round(y1, 2),
                        round(x2, 2),
                        round(y2, 2),
                    ],
                    "area":          round((x2 - x1) * (y2 - y1), 2),
                })

        return detections

    # Convenience: Predict from bytes

    def predict_file(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        نفس الـ predict، لكن تقبل bytes (من upload مباشرة).
        """
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Invalid image: could not decode")

        return self.predict(img)

    # Drawing: يضع بوكسات على الصورة
    
    def draw(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        يرسم البوكسات والأسماء على نسخة من الصورة.
        يرجّع نسخة جديدة (لا يعدّل الأصلية).
        """
        out = image.copy()

        for det in detections:
            x1, y1, x2, y2 = map(int, det["bbox"])
            label = f'{det["class_name"]} {det["confidence"]:.2f}'

            # رسم البوكس
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # خلفية للنص
            (tw, th), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )
            cv2.rectangle(
                out,
                (x1, y1 - th - 6),
                (x1 + tw, y1),
                (0, 0, 255),
                -1,
            )

            # النص
            cv2.putText(
                out,
                label,
                (x1, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

        return out