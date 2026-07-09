package com.fabric.detect.ui

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.util.Size
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Cameraswitch
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.fabric.detect.detector.Detection
import com.fabric.detect.detector.FabricDetector
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.Executors

@Composable
fun CameraScreen() {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    var cameraSelector by remember { mutableStateOf(CameraSelector.DEFAULT_BACK_CAMERA) }
    val detections = remember { mutableStateListOf<Detection>() }
    var imageWidth by remember { mutableIntStateOf(0) }
    var imageHeight by remember { mutableIntStateOf(0) }
    var frameCount by remember { mutableIntStateOf(0) }
    var modelReady by remember { mutableStateOf(false) }
    var isGenericMode by remember { mutableStateOf(false) }
    var genericAvailable by remember { mutableStateOf(false) }
    var permissionGranted by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA)
                    == PackageManager.PERMISSION_GRANTED
        )
    }

    val detector = remember { FabricDetector(context) }
    val bgExecutor = remember { Executors.newSingleThreadExecutor() }

    // Use a ref so the analyzer lambda always sees the latest mode
    val genericModeRef = remember { mutableStateOf(false) }
    genericModeRef.value = isGenericMode

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        permissionGranted = granted
    }

    LaunchedEffect(Unit) {
        if (!permissionGranted) {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    LaunchedEffect(Unit) {
        withContext(Dispatchers.IO) {
            detector.load()
        }
        modelReady = true
        genericAvailable = detector.isGenericAvailable()
    }

    DisposableEffect(Unit) {
        onDispose {
            detector.close()
            bgExecutor.shutdownNow()
        }
    }

    val imageAnalyzer = remember {
        ImageAnalysis.Builder()
            .setTargetResolution(Size(640, 480))
            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
            .build()
            .also {
                it.setAnalyzer(bgExecutor) { imageProxy ->
                    if (!modelReady) {
                        imageProxy.close()
                        return@setAnalyzer
                    }
                    try {
                        // Use CameraX built-in toBitmap() for reliable YUV→Bitmap conversion
                        val rawBitmap = imageProxy.toBitmap()

                        // Handle sensor rotation
                        val rotationDegrees = imageProxy.imageInfo.rotationDegrees
                        val bitmap = if (rotationDegrees != 0) {
                            val matrix = Matrix()
                            matrix.postRotate(rotationDegrees.toFloat())
                            Bitmap.createBitmap(
                                rawBitmap, 0, 0,
                                rawBitmap.width, rawBitmap.height,
                                matrix, true
                            ).also {
                                if (it != rawBitmap) rawBitmap.recycle()
                            }
                        } else {
                            rawBitmap
                        }

                        imageWidth = bitmap.width
                        imageHeight = bitmap.height

                        val results = if (genericModeRef.value) {
                            detector.detectGeneric(bitmap)
                        } else {
                            detector.detect(bitmap)
                        }
                        detections.clear()
                        detections.addAll(results)
                        bitmap.recycle()
                        frameCount++
                    } catch (e: Exception) {
                        e.printStackTrace()
                    } finally {
                        imageProxy.close()
                    }
                }
            }
    }

    Scaffold(modifier = Modifier.fillMaxSize()) { padding ->
        Box(modifier = Modifier.fillMaxSize().padding(padding)) {
            if (!permissionGranted) return@Box

            // key(cameraSelector) forces the AndroidView to recreate when camera changes
            key(cameraSelector) {
                AndroidView(
                    modifier = Modifier.fillMaxSize(),
                    factory = { ctx ->
                        val previewView = PreviewView(ctx)
                        val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                        cameraProviderFuture.addListener({
                            val cameraProvider = cameraProviderFuture.get()
                            val preview = androidx.camera.core.Preview.Builder().build().also {
                                it.setSurfaceProvider(previewView.surfaceProvider)
                            }
                            try {
                                cameraProvider.unbindAll()
                                cameraProvider.bindToLifecycle(
                                    lifecycleOwner, cameraSelector, preview, imageAnalyzer
                                )
                            } catch (_: Exception) {
                            }
                        }, ContextCompat.getMainExecutor(ctx))
                        previewView
                    },
                    update = { _ -> }
                )
            }

            // Detection overlay
            Canvas(modifier = Modifier.fillMaxSize()) {
                if (imageWidth == 0 || frameCount < 3) return@Canvas

                // Map detection coordinates (image space) to canvas (screen space)
                val scaleX = size.width / imageWidth.toFloat()
                val scaleY = size.height / imageHeight.toFloat()

                for (det in detections) {
                    val c = when (det.label) {
                        "hole" -> Color.Red
                        "dirt" -> Color(0xFF00AA00)
                        "thread" -> Color.Blue
                        else -> Color(0xFFFF6600)
                    }

                    if (det.isOBB) {
                        val pts = det.points
                        if (pts.size >= 4) {
                            val path = Path()
                            path.moveTo(pts[0].x * scaleX, pts[0].y * scaleY)
                            for (j in 1 until pts.size) {
                                path.lineTo(pts[j].x * scaleX, pts[j].y * scaleY)
                            }
                            path.close()
                            drawPath(path, c, style = Stroke(width = 3f))
                        }
                    } else {
                        drawRect(
                            color = c,
                            topLeft = Offset(det.x1 * scaleX, det.y1 * scaleY),
                            size = androidx.compose.ui.geometry.Size(
                                (det.x2 - det.x1) * scaleX,
                                (det.y2 - det.y1) * scaleY
                            ),
                            style = Stroke(width = 3f)
                        )
                    }
                }

                val canvas = drawContext.canvas.nativeCanvas
                val paint = android.graphics.Paint().apply {
                    isAntiAlias = true
                    textSize = 36f
                    isFakeBoldText = true
                    setShadowLayer(4f, 1f, 1f, android.graphics.Color.BLACK)
                }
                for (det in detections) {
                    paint.color = when (det.label) {
                        "hole" -> android.graphics.Color.RED
                        "dirt" -> 0xFF00AA00.toInt()
                        "thread" -> android.graphics.Color.BLUE
                        else -> 0xFFFF6600.toInt()
                    }
                    val label = "${det.label} ${"%.2f".format(det.conf)}"
                    val x = if (det.isOBB) det.points[0].x * scaleX else det.x1 * scaleX
                    val y = if (det.isOBB) det.points[0].y * scaleY - 10f else det.y1 * scaleY - 10f
                    canvas.drawText(label, x, y.coerceAtLeast(30f), paint)
                }
            }

            // Bottom controls
            Row(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(24.dp),
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Mode switch: Fabric <-> Generic YOLO
                if (genericAvailable) {
                    Text(
                        text = if (isGenericMode) "通用" else "布料",
                        color = Color.White,
                        fontSize = 14.sp
                    )
                    Switch(
                        checked = isGenericMode,
                        onCheckedChange = {
                            isGenericMode = it
                            detections.clear()
                        },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = Color.White,
                            checkedTrackColor = Color(0xFF4CAF50),
                            uncheckedThumbColor = Color.White,
                            uncheckedTrackColor = Color(0xFF2196F3)
                        )
                    )
                }

                // Camera switch button
                IconButton(
                    onClick = {
                        cameraSelector = if (cameraSelector == CameraSelector.DEFAULT_BACK_CAMERA) {
                            CameraSelector.DEFAULT_FRONT_CAMERA
                        } else {
                            CameraSelector.DEFAULT_BACK_CAMERA
                        }
                    }
                ) {
                    Icon(
                        imageVector = Icons.Default.Cameraswitch,
                        contentDescription = "Switch Camera",
                        tint = Color.White
                    )
                }
            }
        }
    }
}
