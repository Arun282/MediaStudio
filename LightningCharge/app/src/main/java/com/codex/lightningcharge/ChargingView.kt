package com.codex.lightningcharge

import android.content.Context
import android.graphics.*
import android.view.View
import kotlin.math.min

class ChargingView(context: Context) : View(context) {
    private var snapshot = BatterySnapshot(0,100,0.0,0,0.0,0.0,false,0,0,0,"",0.0,0.0,null,null)
    private var peakWatts = 0.0
    private var avgWatts = 0.0
    private var phase = 0f
    private val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        typeface = Typeface.create("sans", Typeface.NORMAL)
        textAlign = Paint.Align.CENTER
    }

    init {
        setBackgroundColor(Color.BLACK)
        post(object : Runnable {
            override fun run() {
                phase += 0.025f
                invalidate()
                postDelayed(this, 16L)
            }
        })
    }

    fun update(data: BatterySnapshot, peak: Double, average: Double) {
        snapshot = data
        peakWatts = peak
        avgWatts = average
        invalidate()
    }

    override fun onDraw(c: Canvas) {
        super.onDraw(c)
        val cx = width / 2f
        val cy = height * .30f
        val radius = min(width, height) * .205f
        val pct = snapshot.percent.coerceIn(0, 100)

        if (snapshot.charging) {
            for (i in 5 downTo 1) {
                ringPaint.style = Paint.Style.STROKE
                ringPaint.strokeWidth = 4f + i * 7f
                ringPaint.color = Color.argb(15, 40, 80 + i * 15, 255)
                c.drawCircle(cx, cy, radius + i * 3f, ringPaint)
            }
        }

        ringPaint.style = Paint.Style.STROKE
        ringPaint.strokeCap = Paint.Cap.ROUND
        ringPaint.strokeWidth = 12f
        ringPaint.color = Color.rgb(48, 52, 75)
        c.drawCircle(cx, cy, radius, ringPaint)
        ringPaint.color = Color.rgb(80, 125, 255)
        c.drawArc(cx-radius, cy-radius, cx+radius, cy+radius, -90f, 360f*pct/100f, false, ringPaint)

        if (snapshot.charging) {
            ringPaint.strokeWidth = 4f
            ringPaint.color = Color.rgb(145, 185, 255)
            val arc = RectF(cx-radius-16, cy-radius-16, cx+radius+16, cy+radius+16)
            c.drawArc(arc, phase*57f, 70f, false, ringPaint)
            c.drawArc(arc, phase*-43f+180f, 35f, false, ringPaint)
        }

        textPaint.color = Color.WHITE
        textPaint.textSize = radius * .34f
        c.drawText("\${pct}%", cx, cy + 5f, textPaint)

        textPaint.color = Color.rgb(125, 170, 255)
        textPaint.textSize = radius * .19f
        c.drawText(String.format("%.2f W", snapshot.watts), cx, cy + radius*.38f, textPaint)

        textPaint.color = Color.rgb(255, 220, 70)
        textPaint.textSize = radius * .26f
        c.drawText("⚡", cx, cy-radius*.52f, textPaint)

        val state = when {
            !snapshot.charging -> "CONNECT CHARGER"
            snapshot.watts >= 18.0 -> "HIGH POWER"
            snapshot.watts >= 10.0 -> "FAST CHARGING"
            else -> "CHARGING"
        }
        textPaint.color = Color.LTGRAY
        textPaint.textSize = 21f
        c.drawText(state, cx, height*.53f, textPaint)

        textPaint.color = Color.WHITE
        textPaint.textSize = 15f
        c.drawText(
            String.format("%.2f V  •  %d mA  •  %.1f°C", snapshot.voltage, snapshot.currentMa, snapshot.temperature),
            cx, height*.585f, textPaint
        )

        textPaint.color = Color.LTGRAY
        textPaint.textSize = 14f
        val time = snapshot.estimatedMinutesToFull?.let { formatMinutes(it) } ?: "--"
        c.drawText("ETA FULL  \${time}   •   \${BatteryReader.pluggedLabel(snapshot.plugged)}", cx, height*.64f, textPaint)

        c.drawText(
            "PEAK %.2f W   •   AVG %.2f W".format(peakWatts, avgWatts),
            cx, height*.695f, textPaint
        )

        val health = BatteryReader.healthLabel(snapshot.health)
        c.drawText(
            "HEALTH \${health}   •   \${snapshot.technology.ifBlank { "BATTERY" }}",
            cx, height*.75f, textPaint
        )

        val cycles = snapshot.cycleCount?.toString() ?: "--"
        c.drawText(
            "CYCLES \${cycles}   •   CAP %.0f mAh".format(snapshot.chargeCounterMah),
            cx, height*.805f, textPaint
        )

        textPaint.color = Color.DKGRAY
        textPaint.textSize = 12f
        c.drawText("Actual power = voltage × current • device-reported data", cx, height*.875f, textPaint)
    }

    private fun formatMinutes(minutes: Int): String {
        val h = minutes / 60
        val m = minutes % 60
        return if (h > 0) "\${h}h \${m}m" else "\${m}m"
    }
}
