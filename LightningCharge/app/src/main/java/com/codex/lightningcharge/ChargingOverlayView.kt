package com.codex.lightningcharge

import android.content.Context
import android.graphics.*
import android.view.View
import kotlin.math.min

class ChargingOverlayView(context: Context) : View(context) {
    private var snapshot: BatterySnapshot? = null
    private var pulse = 0f
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER }

    fun update(data: BatterySnapshot) {
        snapshot = data
        invalidate()
    }

    override fun onDraw(c: Canvas) {
        val s = snapshot ?: return
        val w = width.toFloat()
        val h = height.toFloat()
        val r = min(w, h) * .39f
        val cx = w / 2f
        val cy = h / 2f

        paint.style = Paint.Style.FILL
        paint.color = Color.argb(225, 8, 12, 24)
        c.drawCircle(cx, cy, r + 8f, paint)

        paint.style = Paint.Style.STROKE
        paint.strokeWidth = 7f
        paint.strokeCap = Paint.Cap.ROUND
        paint.color = Color.rgb(55, 62, 85)
        c.drawCircle(cx, cy, r, paint)
        paint.color = Color.rgb(80, 125, 255)
        c.drawArc(cx-r, cy-r, cx+r, cy+r, -90f, 360f * s.percent / 100f, false, paint)

        paint.style = Paint.Style.FILL
        paint.color = Color.WHITE
        paint.textSize = r * .42f
        c.drawText(s.percent.toString() + "%", cx, cy + 7f, paint)

        paint.color = Color.rgb(125, 170, 255)
        paint.textSize = r * .24f
        c.drawText(String.format("%.1fW", s.watts), cx, cy + r * .42f, paint)

        paint.color = Color.rgb(255, 220, 70)
        paint.textSize = r * .30f
        c.drawText("⚡", cx, cy - r * .48f, paint)

        pulse += .08f
        postInvalidateDelayed(40L)
    }
}
