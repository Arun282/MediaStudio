package com.codex.lightningcharge

import android.app.*
import android.content.*
import android.os.*
import android.graphics.Color
import androidx.core.app.NotificationCompat
import kotlin.math.abs

class ChargingService : Service() {
    private val handler = Handler(Looper.getMainLooper())
    private var charging = false
    private var lastIntent: Intent? = null
    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == Intent.ACTION_BATTERY_CHANGED) {
                lastIntent = intent
                val status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
                charging = status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL
                updateNotification(intent)
            }
        }
    }
    override fun onCreate() {
        super.onCreate()
        createChannel()
        startForeground(10, buildNotification("Charging monitor active"))
        registerReceiver(receiver, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        handler.post(updateRunnable)
    }
    private val updateRunnable = object : Runnable {
        override fun run() {
            lastIntent?.let { updateNotification(it) }
            handler.postDelayed(this, 1000)
        }
    }
    private fun updateNotification(i: Intent) {
        val level = i.getIntExtra(BatteryManager.EXTRA_LEVEL, 0)
        val voltageMv = i.getIntExtra(BatteryManager.EXTRA_VOLTAGE, 0)
        val currentUa = i.getIntExtra(BatteryManager.EXTRA_CURRENT_NOW, 0)
        val watts = (voltageMv / 1000.0) * (abs(currentUa) / 1_000_000.0)
        val temp = i.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) / 10.0
        val text = if (charging) "$level% • %.1f W • %.1f°C".format(watts, temp) else "Not charging • $level%"
        getSystemService(NotificationManager::class.java).notify(10, buildNotification(text))
    }
    private fun buildNotification(text: String): Notification =
        NotificationCompat.Builder(this, "charging")
            .setSmallIcon(android.R.drawable.ic_lock_idle_charging)
            .setContentTitle("⚡ Lightning Charge")
            .setContentText(text)
            .setOngoing(charging)
            .setOnlyAlertOnce(true)
            .setColor(Color.rgb(80,125,255))
            .build()
    private fun createChannel() {
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel("charging", "Charging monitor", NotificationManager.IMPORTANCE_LOW)
        )
    }
    override fun onDestroy() {
        try { unregisterReceiver(receiver) } catch (_: Exception) {}
        handler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }
    override fun onBind(intent: Intent?) = null
}
