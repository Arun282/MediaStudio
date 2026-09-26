package com.codex.lightningcharge

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.BatteryManager
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlin.math.abs

class MainActivity : AppCompatActivity() {
    private lateinit var chargingView: ChargingView

    private val batteryReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == Intent.ACTION_BATTERY_CHANGED) {
                updateBattery(intent)
                val status = intent.getIntExtra(
                    BatteryManager.EXTRA_STATUS,
                    BatteryManager.BATTERY_STATUS_UNKNOWN
                )
                val charging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                        status == BatteryManager.BATTERY_STATUS_FULL

            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        window.statusBarColor = android.graphics.Color.BLACK
        window.navigationBarColor = android.graphics.Color.BLACK

        chargingView = ChargingView(this)
        setContentView(chargingView)

        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.POST_NOTIFICATIONS
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                100
            )
        }
    }

    override fun onStart() {
        super.onStart()
        val initial = registerReceiver(
            batteryReceiver,
            IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        )
        if (initial != null) updateBattery(initial)
    }

    override fun onStop() {
        try {
            unregisterReceiver(batteryReceiver)
        } catch (_: Exception) {
        }
        super.onStop()
    }

    private fun updateBattery(intent: Intent) {
        val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, 0)
        val voltageMv = intent.getIntExtra(BatteryManager.EXTRA_VOLTAGE, 0)
        val voltage = voltageMv / 1000.0

        val status = intent.getIntExtra(
            BatteryManager.EXTRA_STATUS,
            BatteryManager.BATTERY_STATUS_UNKNOWN
        )
        val charging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                status == BatteryManager.BATTERY_STATUS_FULL

        val manager = getSystemService(BATTERY_SERVICE) as BatteryManager
        val rawCurrentUa = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW)
        } else {
            0
        }

        val currentUa = if (rawCurrentUa == Int.MIN_VALUE) 0 else abs(rawCurrentUa)
        val currentMa = currentUa / 1000
        val watts = voltage * (currentUa / 1_000_000.0)
        val temperature =
            intent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) / 10.0

        chargingView.update(
            percent = level.coerceIn(0, 100),
            watts = watts,
            voltage = voltage,
            currentMa = currentMa,
            temperature = temperature,
            charging = charging
        )
    }
}
