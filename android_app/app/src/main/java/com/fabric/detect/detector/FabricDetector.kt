package com.fabric.detect.detector

import android.content.Context
import android.graphics.Bitmap
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.nio.FloatBuffer
import java.util.Collections

data class Detection(
    val label: String,
    val conf: Float,
    val x1: Float = 0f,
    val y1: Float = 0f,
    val x2: Float = 0f,
    val y2: Float = 0f,
    val points: List<Offset> = emptyList(),
    val isOBB: Boolean = false
)

data class Offset(val x: Float, val y: Float)

private data class Preprocessed(
    val tensor: OnnxTensor,
    val origW: Float,
    val origH: Float
)

class FabricDetector(private val context: Context) {

    private var env: OrtEnvironment? = null
    private var detectSession: OrtSession? = null
    private var obbSession: OrtSession? = null
    private var genericSession: OrtSession? = null
    private var loaded = false
    private var genericLoaded = false

    companion object {
        private const val IMG_SIZE = 640
        private const val NUM_PREDS = 8400
        private const val CONF_THRESHOLD = 0.25f
        private const val IOU_THRESHOLD = 0.45f

        private val COCO_LABELS = arrayOf(
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
            "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
            "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
            "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
            "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
            "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
            "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
            "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
            "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
            "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
            "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
            "toothbrush"
        )
        private const val COCO_NUM_CLASSES = 80
    }

    fun load() {
        if (loaded) return
        env = OrtEnvironment.getEnvironment()
        detectSession = env?.createSession(
            context.assets.open("detectbest.onnx").readBytes(),
            OrtSession.SessionOptions()
        )
        obbSession = env?.createSession(
            context.assets.open("obbbest.onnx").readBytes(),
            OrtSession.SessionOptions()
        )
        try {
            genericSession = env?.createSession(
                context.assets.open("yolov8n.onnx").readBytes(),
                OrtSession.SessionOptions()
            )
            genericLoaded = true
        } catch (e: Exception) {
            e.printStackTrace()
            genericLoaded = false
        }
        loaded = true
    }

    fun isGenericAvailable(): Boolean = genericLoaded

    fun detect(bitmap: Bitmap): List<Detection> {
        if (!loaded) return emptyList()
        val resized = Bitmap.createScaledBitmap(bitmap, IMG_SIZE, IMG_SIZE, true)

        var preprocessed: Preprocessed? = null
        val detectResults = mutableListOf<Detection>()
        val obbResults = mutableListOf<Detection>()

        try {
            preprocessed = preprocess(resized, bitmap.width.toFloat(), bitmap.height.toFloat())

            detectSession?.run(Collections.singletonMap("images", preprocessed.tensor))?.use { outputs ->
                val output = outputs.get(0) as OnnxTensor
                detectResults.addAll(postprocessDetect(output, preprocessed.origW, preprocessed.origH))
            }

            obbSession?.run(Collections.singletonMap("images", preprocessed.tensor))?.use { outputs ->
                val output = outputs.get(0) as OnnxTensor
                obbResults.addAll(postprocessOBB(output, preprocessed.origW, preprocessed.origH))
            }
        } catch (e: Exception) {
            e.printStackTrace()
        } finally {
            preprocessed?.tensor?.close()
            if (resized != bitmap) resized.recycle()
        }

        val results = mutableListOf<Detection>()
        for (d in detectResults) {
            if (d.label != "thread") results.add(d)
        }
        results.addAll(obbResults)
        return results
    }

    fun detectGeneric(bitmap: Bitmap): List<Detection> {
        if (!loaded || !genericLoaded) return emptyList()
        val resized = Bitmap.createScaledBitmap(bitmap, IMG_SIZE, IMG_SIZE, true)

        var preprocessed: Preprocessed? = null
        val results = mutableListOf<Detection>()

        try {
            preprocessed = preprocess(resized, bitmap.width.toFloat(), bitmap.height.toFloat())

            genericSession?.run(Collections.singletonMap("images", preprocessed.tensor))?.use { outputs ->
                val output = outputs.get(0) as OnnxTensor
                results.addAll(postprocessGeneric(output, preprocessed.origW, preprocessed.origH))
            }
        } catch (e: Exception) {
            e.printStackTrace()
        } finally {
            preprocessed?.tensor?.close()
            if (resized != bitmap) resized.recycle()
        }

        return results
    }

    private fun preprocess(bitmap: Bitmap, origW: Float, origH: Float): Preprocessed {
        val pixels = IntArray(IMG_SIZE * IMG_SIZE)
        bitmap.getPixels(pixels, 0, IMG_SIZE, 0, 0, IMG_SIZE, IMG_SIZE)

        val floatData = FloatArray(3 * IMG_SIZE * IMG_SIZE)
        for (i in pixels.indices) {
            val p = pixels[i]
            floatData[i] = ((p shr 16) and 0xFF) / 255.0f
            floatData[IMG_SIZE * IMG_SIZE + i] = ((p shr 8) and 0xFF) / 255.0f
            floatData[2 * IMG_SIZE * IMG_SIZE + i] = (p and 0xFF) / 255.0f
        }

        val shape = longArrayOf(1, 3, IMG_SIZE.toLong(), IMG_SIZE.toLong())
        val tensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(floatData), shape)
        return Preprocessed(tensor, origW, origH)
    }

    private fun postprocessDetect(
        output: OnnxTensor, origW: Float, origH: Float
    ): List<Detection> {
        val data = output.floatBuffer
        val labels = arrayOf("hole", "dirt", "thread")
        val allBoxes = mutableListOf<Box>()

        for (i in 0 until NUM_PREDS) {
            val cx = data[0 * NUM_PREDS + i]
            val cy = data[1 * NUM_PREDS + i]
            val w  = data[2 * NUM_PREDS + i]
            val h  = data[3 * NUM_PREDS + i]

            var maxScore = 0f
            var maxCls = 0
            for (c in 0 until 3) {
                val score = data[(4 + c) * NUM_PREDS + i]
                if (score > maxScore) {
                    maxScore = score
                    maxCls = c
                }
            }

            if (maxScore >= CONF_THRESHOLD) {
                val x1 = cx - w / 2f
                val y1 = cy - h / 2f
                val x2 = cx + w / 2f
                val y2 = cy + h / 2f
                allBoxes.add(Box(floatArrayOf(x1, y1, x2, y2), maxCls, maxScore, labels[maxCls]))
            }
        }

        val results = mutableListOf<Detection>()
        for (cls in 0 until 3) {
            val clsBoxes = allBoxes.filter { it.cls == cls }
            val keep = nms(clsBoxes, IOU_THRESHOLD)
            for (k in keep) {
                val b = clsBoxes[k]
                results.add(Detection(
                    label = b.label,
                    conf = b.score,
                    x1 = b.bbox[0] / IMG_SIZE * origW,
                    y1 = b.bbox[1] / IMG_SIZE * origH,
                    x2 = b.bbox[2] / IMG_SIZE * origW,
                    y2 = b.bbox[3] / IMG_SIZE * origH
                ))
            }
        }
        return results
    }

    private fun postprocessGeneric(
        output: OnnxTensor, origW: Float, origH: Float
    ): List<Detection> {
        val data = output.floatBuffer
        val allBoxes = mutableListOf<Box>()

        for (i in 0 until NUM_PREDS) {
            val cx = data[0 * NUM_PREDS + i]
            val cy = data[1 * NUM_PREDS + i]
            val w  = data[2 * NUM_PREDS + i]
            val h  = data[3 * NUM_PREDS + i]

            var maxScore = 0f
            var maxCls = 0
            for (c in 0 until COCO_NUM_CLASSES) {
                val score = data[(4 + c) * NUM_PREDS + i]
                if (score > maxScore) {
                    maxScore = score
                    maxCls = c
                }
            }

            if (maxScore >= CONF_THRESHOLD) {
                val x1 = cx - w / 2f
                val y1 = cy - h / 2f
                val x2 = cx + w / 2f
                val y2 = cy + h / 2f
                allBoxes.add(Box(floatArrayOf(x1, y1, x2, y2), maxCls, maxScore, COCO_LABELS[maxCls]))
            }
        }

        val results = mutableListOf<Detection>()
        for (cls in 0 until COCO_NUM_CLASSES) {
            val clsBoxes = allBoxes.filter { it.cls == cls }
            if (clsBoxes.isEmpty()) continue
            val keep = nms(clsBoxes, IOU_THRESHOLD)
            for (k in keep) {
                val b = clsBoxes[k]
                results.add(Detection(
                    label = b.label,
                    conf = b.score,
                    x1 = b.bbox[0] / IMG_SIZE * origW,
                    y1 = b.bbox[1] / IMG_SIZE * origH,
                    x2 = b.bbox[2] / IMG_SIZE * origW,
                    y2 = b.bbox[3] / IMG_SIZE * origH
                ))
            }
        }
        return results
    }

    private fun postprocessOBB(
        output: OnnxTensor, origW: Float, origH: Float
    ): List<Detection> {
        val data = output.floatBuffer
        val allBoxes = mutableListOf<Box>()

        for (i in 0 until NUM_PREDS) {
            val cx = data[0 * NUM_PREDS + i]
            val cy = data[1 * NUM_PREDS + i]
            val w  = data[2 * NUM_PREDS + i]
            val h  = data[3 * NUM_PREDS + i]
            val score = data[4 * NUM_PREDS + i]
            val angle = data[5 * NUM_PREDS + i]

            if (score >= CONF_THRESHOLD) {
                val pts = obbToCorners(cx, cy, w, h, angle)
                val minX = pts.filterIndexed { idx, _ -> idx % 2 == 0 }.min()
                val minY = pts.filterIndexed { idx, _ -> idx % 2 == 1 }.min()
                val maxX = pts.filterIndexed { idx, _ -> idx % 2 == 0 }.max()
                val maxY = pts.filterIndexed { idx, _ -> idx % 2 == 1 }.max()
                allBoxes.add(Box(
                    floatArrayOf(minX, minY, maxX, maxY),
                    0, score, "thread",
                    obbPts = pts
                ))
            }
        }

        val keep = nms(allBoxes, IOU_THRESHOLD)
        return keep.map { idx ->
            val b = allBoxes[idx]
            val pts = b.obbPts!!
            Detection(
                label = "thread",
                conf = b.score,
                points = (0 until 4).map { j ->
                    Offset(
                        pts[j * 2] / IMG_SIZE * origW,
                        pts[j * 2 + 1] / IMG_SIZE * origH
                    )
                },
                isOBB = true
            )
        }
    }

    private fun obbToCorners(cx: Float, cy: Float, w: Float, h: Float, angle: Float): FloatArray {
        val cosA = kotlin.math.cos(angle)
        val sinA = kotlin.math.sin(angle)
        val hw = w / 2f
        val hh = h / 2f
        return floatArrayOf(
            cx - hw * cosA + hh * sinA, cy - hw * sinA - hh * cosA,
            cx + hw * cosA + hh * sinA, cy + hw * sinA - hh * cosA,
            cx + hw * cosA - hh * sinA, cy + hw * sinA + hh * cosA,
            cx - hw * cosA - hh * sinA, cy - hw * sinA + hh * cosA
        )
    }

    private fun sigmoid(x: Float): Float =
        (1f / (1f + kotlin.math.exp(-x.coerceIn(-20f, 20f))))

    private fun nms(boxes: List<Box>, iouThresh: Float): List<Int> {
        val sorted = boxes.indices.sortedByDescending { boxes[it].score }
        val keep = mutableListOf<Int>()
        for (i in sorted) {
            var suppressed = false
            for (j in keep) {
                if (iou(boxes[i].bbox, boxes[j].bbox) > iouThresh) {
                    suppressed = true
                    break
                }
            }
            if (!suppressed) keep.add(i)
        }
        return keep
    }

    private fun iou(a: FloatArray, b: FloatArray): Float {
        val x1 = maxOf(a[0], b[0])
        val y1 = maxOf(a[1], b[1])
        val x2 = minOf(a[2], b[2])
        val y2 = minOf(a[3], b[3])
        val inter = maxOf(0f, x2 - x1) * maxOf(0f, y2 - y1)
        val areaA = (a[2] - a[0]) * (a[3] - a[1])
        val areaB = (b[2] - b[0]) * (b[3] - b[1])
        return inter / (areaA + areaB - inter + 1e-5f)
    }

    fun close() {
        detectSession?.close()
        obbSession?.close()
        genericSession?.close()
        env?.close()
        loaded = false
    }

    private data class Box(
        val bbox: FloatArray,
        val cls: Int,
        val score: Float,
        val label: String,
        val obbPts: FloatArray? = null
    )
}
