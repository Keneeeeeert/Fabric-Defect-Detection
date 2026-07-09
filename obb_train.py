from ultralytics import YOLO


def main():
    model = YOLO("yolov8n-obb.pt")

    results = model.train(
        data="dataset_obb/data.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        device="cpu",
        workers=8,
        patience=30,
        save=True,
        save_period=10,
        project="runs",
        name="thread_obb",
        exist_ok=True,
        pretrained=True,
        optimizer="auto",
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=45.0,
        translate=0.1,
        scale=0.5,
        shear=10.0,
        perspective=0.0005,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
    )

    metrics = model.val()
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")

    model.export(format="onnx")


if __name__ == "__main__":
    main()
