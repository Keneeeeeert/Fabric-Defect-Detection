# Colab 训练指南 - 服装成衣面料疵点检测

## 一、准备工作

1. 打开 https://colab.research.google.com/
2. 登录 Google 账号 → 新建笔记本
3. 菜单: 代码执行程序 → 更改运行时类型 → T4 GPU → 保存

## 二、启动前运行这段验证 GPU

```
!nvidia-smi
```

看到 Tesla T4 就对了。

## 三、上传数据集

左侧文件夹图标 → 拖入 dataset.zip 和 dataset_obb.zip

## 四、解压数据集

```
!unzip -q dataset.zip -d /content/
!unzip -q dataset_obb.zip -d /content/
```

## 五、安装依赖

```
!pip install ultralytics
```

## 六、训练 - 常规检测 (hole + dirt + thread)

```
!yolo train model=yolov8n.pt data=/content/dataset/data.yaml epochs=100 imgsz=640 patience=30 batch=32 device=0 mixup=0.1 copy_paste=0.1 project=/content/runs name=detect
```

## 七、训练 - OBB 旋转框检测 (thread 专用)

```
!yolo train model=yolov8n-obb.pt data=/content/dataset_obb/data.yaml epochs=100 imgsz=640 patience=30 batch=32 device=0 degrees=45 shear=10 project=/content/runs name=obb
```

## 八、下载模型

训练完在左侧文件夹 /content/runs/detect/weights/best.pt
右键 → 下载

同样下载 /content/runs/obb/weights/best.pt

## 九、验证集评估 (可选)

```
!yolo val model=/content/runs/detect/weights/best.pt data=/content/dataset/data.yaml
!yolo val model=/content/runs/obb/weights/best.pt data=/content/dataset_obb/data.yaml
```
