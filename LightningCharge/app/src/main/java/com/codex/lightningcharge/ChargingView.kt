package com.codex.lightningcharge

import android.content.Context
import android.graphics.*
import android.view.View
import kotlin.math.min

class ChargingView(context: Context) : View(context) {
    private var percent = 0
    private var watts = 0.0
    private var voltage = 0.0
    private var currentMa = 0
    private var temperature = 0.0
    private var charging = false
    private var phase = 0f
    private val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        typeface = Typeface.create("sans", Typeface.NORMAL)
        textAlign = Paint.Align.CENTER
    }
    init {
        setBackgroundColor(Color.BLACK)
        post(object : Runnable {
            override fun run() { phase += 0.025f; invalidate(); postDelayed(this, 16L) }
        })
    }
    fun update(percent:Int, watts:Double, voltage:Double, currentMa:Int, temperature:Double, charging:Boolean) {
        this.percent=percent; this.watts=watts; this.voltage=voltage; this.currentMa=currentMa; this.temperature=temperature; this.charging=charging; invalidate()
    }
    override fun onDraw(c:Canvas) {
        super.onDraw(c)
        val cx=width/2f; val cy=height*.43f; val radius=min(width,height)*.25f
        if(charging) for(i in 5 downTo 1){ ringPaint.style=Paint.Style.STROKE; ringPaint.strokeWidth=5f+i*8f; ringPaint.color=Color.argb(18,40,80+i*15,255); c.drawCircle(cx,cy,radius+i*3f,ringPaint) }
        ringPaint.style=Paint.Style.STROKE; ringPaint.strokeCap=Paint.Cap.ROUND; ringPaint.strokeWidth=13f; ringPaint.color=Color.rgb(55,60,90); c.drawCircle(cx,cy,radius,ringPaint)
        ringPaint.color=Color.rgb(80,125,255); c.drawArc(cx-radius,cy-radius,cx+radius,cy+radius,-90f,360f*percent.coerceIn(0,100)/100f,false,ringPaint)
        if(charging){ ringPaint.strokeWidth=4f; ringPaint.color=Color.rgb(145,185,255); val arc=RectF(cx-radius-18,cy-radius-18,cx+radius+18,cy+radius+18); c.drawArc(arc,phase*57f,70f,false,ringPaint); c.drawArc(arc,phase*-43f+180f,35f,false,ringPaint) }
        textPaint.color=Color.WHITE; textPaint.textSize=radius*.36f; c.drawText("$percent%",cx,cy-4f,textPaint)
        textPaint.color=Color.rgb(125,170,255); textPaint.textSize=radius*.20f; c.drawText(String.format("%.1f W",watts),cx,cy+radius*.36f,textPaint)
        textPaint.color=Color.rgb(255,220,70); textPaint.textSize=radius*.28f; c.drawText("⚡",cx,cy-radius*.48f,textPaint)
        textPaint.color=Color.LTGRAY; textPaint.textSize=22f; c.drawText(if(charging)"FAST CHARGING" else "CONNECT CHARGER",cx,height*.70f,textPaint)
        textPaint.color=Color.GRAY; textPaint.textSize=16f; c.drawText(String.format("%.2f V  •  %d mA  •  %.1f°C",voltage,currentMa,temperature),cx,height*.75f,textPaint)
        textPaint.color=Color.DKGRAY; textPaint.textSize=13f; c.drawText("Actual power = voltage × current",cx,height*.81f,textPaint)
    }
}
