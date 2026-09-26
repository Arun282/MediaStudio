package com.codex.lightningcharge

import android.app.*
import android.content.*
import android.content.pm.ServiceInfo
import android.graphics.Color
import android.os.*
import androidx.core.app.NotificationCompat
import kotlin.math.abs

class ChargingService : Service() {
    private val handler = Handler(Looper.getMainLooper())
    private var charging = false
    private var lastIntent: Intent? = null

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action != Intent.ACTION_BATTERY_CHANGED) return

            lastIntent = intent
            val status = intent.getIntExtra(
                BatteryManager.EXTRA_STATUS,
                BatteryManager.BATTERY_STATUS_UNKNOWN
            )
            charging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                    status == BatteryManager.BATTERY_STATUS_FULL

            updateNotification(intent)

            // Stop monitoring after the cable is removed, avoiding unnecessary
            // background work and battery drain.
            if (!charging) {
                stopSelf()
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        createChannel()

        try {
            val notification = buildNotification("Charging monitor active")
            if (Build.VERSION.SDK_INT >= 34) {
                startForeground(
                    10,
                    notification,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE
                )
            } else {
                startForeground(10, notification)
            }
        } catch (_: Exception) {
            stopSelf()
            return
        }

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
        val batteryManager = getSystemService(BATTERY_SERVICE) as BatteryManager

        val rawCurrentUa = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW)
        } else {
            0
        }

        val currentUa = if (rawCurrentUa == Int.MIN_VALUE) 0 else abs(rawCurrentUa)
        val watts = (voltageMv / 1000.0) * (currentUa / 1_000_000.0)
        val temp = i.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) / 10.0

        val text = if (charging) {
            "$level% • %.1f W • %.1f°C".format(watts, temp)
        } else {
            "Not charging • $level%"
        }

        getSystemService(NotificationManager::class.java).notify(
            10,
            buildNotification(text)
        )
    }

    private fun buildNotification(text: String): Notification {
        val openIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            20,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, "charging")
            .setSmallIcon(android.R.drawable.ic_lock_idle_charging)
            .setContentTitle("⚡ Lightning Charge")
            .setContentText(text)
            .setSubText("Live charging power")
            .setContentIntent(pendingIntent)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setOngoing(charging)
            .setOnlyAlertOnce(true)
            .setShowWhen(false)
            .setColor(Color.rgb(80, 125, 255))
            .build()
    }

    private fun createChannel() {
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(
                "charging",
                "Charging monitor",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Live charging percentage, wattage and temperature"
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            }
        )
    }

    override fun onDestroy() {
        try {
            unregisterReceiver(receiver)
        } catch (_: Exception) {
        }
        handler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onBind(intent: Intent?) = null
}
