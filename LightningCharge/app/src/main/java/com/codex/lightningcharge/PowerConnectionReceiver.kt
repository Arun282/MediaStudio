package com.codex.lightningcharge

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.content.ContextCompat

class PowerConnectionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        try {
            when (intent?.action) {
                Intent.ACTION_POWER_CONNECTED -> {
                    val serviceIntent = Intent(context, ChargingService::class.java)
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        ContextCompat.startForegroundService(context, serviceIntent)
                    } else {
                        context.startService(serviceIntent)
                    }
                }
                Intent.ACTION_POWER_DISCONNECTED -> {
                    context.stopService(Intent(context, ChargingService::class.java))
                }
            }
        } catch (_: Exception) {
            // Never crash the app process on a device-specific background restriction.
        }
    }
}
