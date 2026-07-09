# Fabric Detect - 面料疵点实时检测 Android App

打开即预览，AI 实时检测破洞 (hole)、污渍 (dirt)、线头 (thread) 三类面料缺陷。

## 运行要求
- Android Studio Hedgehog (2023.1.1) 或更高
- Android 12+ 设备
- JDK 17

## 构建
1. Android Studio → Open → 选择 `android_app/` 目录
2. Sync Gradle
3. Run

## 技术栈
- Jetpack Compose + Material 3
- CameraX 实时预览
- ONNX Runtime 推理（两个模型）
- 双模型管线：detectbest.onnx (hole/dirt) + obbbest.onnx (thread)
