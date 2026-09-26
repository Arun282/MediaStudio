package com.codex.lightningcharge

import android.app.*
import android.content.*
import android.content.pm.ServiceInfo
import android.graphics.Color
import android.os.*
import androidx.core.app.NotificationCompat

class ChargingService : Service() {
    private val handler = Handler(Looper.getMainLooper())
    private var charging = false
    private var lastSnapshot: BatterySnapshot? = null
    private var peakWatts = 0.0

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action != Intent.ACTION_BATTERY_CHANGED) return
            val snapshot = BatteryReader.read(this@ChargingService, intent)
            lastSnapshot = snapshot
            charging = snapshot.charging
            if (charging) peakWatts = maxOf(peakWatts, snapshot.watts)
            updateNotification(snapshot)
            if (!charging) stopSelf()
        }
    }

    override fun onCreate() {
        super.onCreate()
        createChannel()
        try {
            val notification = buildNotification("Starting charging monitor…")
            if (Build.VERSION.SDK_INT >= 34) {
                startForeground(10, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
            } else {
                startForeground(10, notification)
            }
        } catch (_: Exception) {
            stopSelf()
            return
        }

        try {
            registerReceiver(receiver, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            handler.post(updateRunnable)
        } catch (_: Exception) {
            stopSelf()
        }
    }

    private val updateRunnable = object : Runnable {
        override fun run() {
            lastSnapshot?.let { updateNotification(it) }
            if (charging) handler.postDelayed(this, 1000L)
        }
    }

    private fun updateNotification(s: BatterySnapshot) {
        val speed = when {
            !s.charging -> "Not charging"
            s.watts >= 18.0 -> "High power"
            s.watts >= 10.0 -> "Fast charging"
            else -> "Charging"
        }
        val eta = s.estimatedMinutesToFull?.let {
            val h = it / 60
            val m = it % 60
            if (h > 0) "ETA \${h}h \${m}m" else "ETA \${m}m"
        } ?: "ETA unavailable"

        val text = if (s.charging) {
            "\${s.percent}% • %.2f W • %d mA • %.1f°C".format(s.watts, s.currentMa, s.temperature)
        } else {
            "\${s.percent}% • Not charging"
        }

        getSystemService(NotificationManager::class.java).notify(
            10,
            buildNotification("\${speed} • \${text} • \${eta}")
        )
    }

    private fun buildNotification(text: String): Notification {
        val openIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 20, openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, "charging")
            .setSmallIcon(android.R.drawable.ic_lock_idle_charging)
            .setContentTitle("⚡ Lightning Charge")
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setSubText("Live charging monitor")
            .setContentIntent(pendingIntent)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setOngoing(charging)
            .setOnlyAlertOnce(true)
            .setShowWhen(false)
            .setColor(Color.rgb(80, 125, 255))
            .setCategory(NotificationCompat.CATEGORY_PROGRESS)
            .build()
    }

    private fun createChannel() {
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel("charging", "Charging monitor", NotificationManager.IMPORTANCE_LOW).apply {
                description = "Live charging percentage, wattage, current, temperature and ETA"
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            }
        )
    }

    override fun onDestroy() {
        try { unregisterReceiver(receiver) } catch (_: Exception) {}
        handler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int) = START_STICKY
    override fun onBind(intent: Intent?) = null
}
