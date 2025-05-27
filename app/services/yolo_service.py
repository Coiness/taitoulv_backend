import torch
import numpy as np
import cv2
from app.core.config import settings
from typing import Dict, List, Union, Any
from pathlib import Path
from datetime import datetime

class YOLO5Service:
    def __init__(self):
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.is_initialized = False

    async def initialize(self):
        """初始化YOLO5模型"""
        if not self.is_initialized:
            try:
                self.model = torch.hub.load('ultralytics/yolov5', 'custom',
                                          path=settings.YOLO5_MODEL_PATH,
                                          device=self.device)
                self.model.conf = settings.CONFIDENCE_THRESHOLD
                self.model.iou = settings.IOU_THRESHOLD
                self.is_initialized = True
            except Exception as e:
                raise Exception(f"Failed to load YOLO5 model: {str(e)}")
        return True

    async def process_image(self, image_path: Union[str, Path]) -> Dict:
        """处理单张图片"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 读取图片
            if isinstance(image_path, str):
                image_path = Path(image_path)
            
            # 进行目标检测
            results = self.model(str(image_path))
            
            # 解析检测结果
            detections = self._parse_results(results)
            head_up_rate = self._calculate_head_up_rate(detections)
            
            return {
                'status': 'success',
                'detections': detections,
                'head_up_rate': head_up_rate,
                'image_path': str(image_path)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'image_path': str(image_path)
            }

    async def process_video(self, video_path: Union[str, Path]) -> Dict:
        """处理视频文件"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            results = []
            frame_number = 0
            total_head_up_rate = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # 每秒处理一帧
                if frame_number % fps == 0:
                    # 处理帧
                    detection_result = await self.process_frame(frame)
                    results.append({
                        'frame_number': frame_number,
                        'timestamp': frame_number / fps,
                        'detections': detection_result['detections'],
                        'head_up_rate': detection_result['head_up_rate']
                    })
                    total_head_up_rate += detection_result['head_up_rate']
                
                frame_number += 1
            
            cap.release()
            
            # 计算平均抬头率
            avg_head_up_rate = total_head_up_rate / len(results) if results else 0
            
            return {
                'status': 'success',
                'video_info': {
                    'total_frames': frame_count,
                    'fps': fps,
                    'duration': frame_count / fps
                },
                'results': results,
                'average_head_up_rate': avg_head_up_rate
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'video_path': str(video_path)
            }

    async def process_frame(self, frame: np.ndarray) -> Dict:
        """处理单个视频帧"""
        try:
            results = self.model(frame)
            detections = self._parse_results(results)
            head_up_rate = self._calculate_head_up_rate(detections)
            
            return {
                'detections': detections,
                'head_up_rate': head_up_rate,
                'timestamp': datetime.now().timestamp()
            }
            
        except Exception as e:
            raise Exception(f"Error processing frame: {str(e)}")

    def _parse_results(self, results) -> List[Dict]:
        """解析YOLO5检测结果"""
        detections = []
        for pred in results.xyxy[0]:
            x1, y1, x2, y2, conf, cls = pred.cpu().numpy()
            detections.append({
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'confidence': float(conf),
                'class': int(cls),
                'class_name': results.names[int(cls)]
            })
        return detections

    def _calculate_head_up_rate(self, detections: List[Dict]) -> float:
        """计算抬头率"""
        if not detections:
            return 0.0
        
        # 假设类别0表示"抬头"，类别1表示"低头"
        head_up_count = sum(1 for det in detections if det['class'] == 0)
        total_count = len(detections)
        
        return head_up_count / total_count if total_count > 0 else 0.0

# 创建服务实例
yolo_service = YOLO5Service()
