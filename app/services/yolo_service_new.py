import numpy as np
import cv2
import base64
from app.core.config import settings
from typing import Dict, List, Union, Any
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO  # 导入YOLOv8

class YOLO8Service:
    def __init__(self):
        self.model = None
        self.is_initialized = False

    async def initialize(self):
        """初始化YOLOv8模型"""
        print("初始化YOLOv8模型")
        if not self.is_initialized:
            try:
                print(f"加载模型，路径: {settings.YOLO8_MODEL_PATH}")  # 仍使用相同的配置路径
                
                # YOLOv8的初始化方式更简单
                self.model = YOLO(settings.YOLO8_MODEL_PATH)
                print("模型加载成功!")
                
                # 设置置信度和IOU阈值
                self.model.conf = settings.CONFIDENCE_THRESHOLD
                self.model.iou = settings.IOU_THRESHOLD
                self.is_initialized = True
                print("模型参数设置完成")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"模型加载失败: {str(e)}")
                self.model = None
                self.is_initialized = False
                raise Exception(f"Failed to load YOLOv8 model: {str(e)}")
        return self.is_initialized

    async def process_image(self, image_path: Union[str, Path]) -> Dict:
        """处理单张图片"""
        print("处理单张图片")
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 读取图片
            if isinstance(image_path, str):
                image_path = Path(image_path)
            
            # 使用YOLOv8进行目标检测
            results = self.model(str(image_path))
            
            # 解析检测结果
            detections = self._parse_results(results[0])
            head_up_rate = self._calculate_head_up_rate(detections)
            
            # 生成可视化图像
            visualized_img = results[0].plot()
            
            # 将图像编码为base64字符串
            _, buffer = cv2.imencode('.jpg', visualized_img)
            img_str = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'status': 'success',
                'detections': detections,
                'head_up_rate': head_up_rate,
                'image_path': str(image_path),
                'visualization': img_str  # 添加可视化图像
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'image_path': str(image_path)
            }

    async def process_video(self, video_path: Union[str, Path]) -> Dict:
        """处理视频文件"""
        print("处理视频文件")
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
                    
                    # 添加到结果列表
                    frame_result = {
                        'frame_number': frame_number,
                        'timestamp': frame_number / fps,
                        'detections': detection_result['detections'],
                        'head_up_rate': detection_result['head_up_rate']
                    }
                    
                    print("visualization:", detection_result.get('visualization', None))
                    # 如果有可视化，也添加
                    if 'visualization' in detection_result:
                        frame_result['visualization'] = detection_result['visualization']
                        
                    results.append(frame_result)
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
        print("处理单个视频帧")

        if not self.is_initialized or self.model is None:
            print("模型未初始化，尝试初始化")
            await self.initialize()
            if self.model is None:
                raise Exception("模型初始化失败，无法处理视频帧")

        try:
            print("视频帧-开始处理")
            # YOLOv8处理帧
            results = self.model(frame)
            
            print("视频帧-解析结果")
            detections = self._parse_results(results[0])
            
            print("视频帧-计算抬头率")
            head_up_rate = self._calculate_head_up_rate(detections)
            
            # 生成可视化图像
            visualized_img = results[0].plot()
            
            # 将图像编码为base64字符串
            _, buffer = cv2.imencode('.jpg', visualized_img)
            img_str = base64.b64encode(buffer).decode('utf-8')
            
            
            return {
                'detections': detections,
                'head_up_rate': head_up_rate,
                'timestamp': datetime.now().timestamp(),
                'visualization': img_str  # 返回可视化结果
            }
            
        except Exception as e:
            raise Exception(f"Error processing frame: {str(e)}")

    def _parse_results(self, result) -> List[Dict]:
        """解析YOLOv8检测结果"""
        detections = []
        
        # YOLOv8结果格式与YOLOv5不同
        boxes = result.boxes
        for i in range(len(boxes)):
            box = boxes[i]
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            confidence = float(box.conf[0])
            cls = int(box.cls[0])
            
            detections.append({
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'confidence': confidence,
                'class': cls,
                'class_name': result.names[cls]
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

    def _visualize_results(self, image: np.ndarray, result) -> np.ndarray:
        """自定义可视化结果，与示例代码效果一致"""
        img = image.copy()
        
        # 处理所有检测到的框
        boxes = result.boxes
        for box in boxes:
            # 获取边界框坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            
            # 获取类别和置信度
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            # 设置标签文本和颜色（类别0为绿色，类别1为红色）
            label = f'Class {cls}: {conf:.2f}'
            color = (0, 255, 0) if cls == 0 else (0, 0, 255)
            
            # 绘制矩形框
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            # 添加标签文本
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return img
# 创建服务实例
yolo_service = YOLO8Service()