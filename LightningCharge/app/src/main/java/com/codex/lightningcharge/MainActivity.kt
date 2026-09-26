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
import kotlin.math.max

class MainActivity : AppCompatActivity() {
    private lateinit var chargingView: ChargingView
    private var sessionPeakWatts = 0.0
    private var sessionSumWatts = 0.0
    private var sessionSamples = 0
    private var sessionStarted = false

    private val batteryReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == Intent.ACTION_BATTERY_CHANGED) updateBattery(intent)
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
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.POST_NOTIFICATIONS), 100)
        }
    }

    override fun onStart() {
        super.onStart()
        val initial = registerReceiver(batteryReceiver, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        if (initial != null) updateBattery(initial)
    }

    override fun onStop() {
        try { unregisterReceiver(batteryReceiver) } catch (_: Exception) {}
        super.onStop()
    }

    private fun updateBattery(intent: Intent) {
        val snapshot = BatteryReader.read(this, intent)
        if (snapshot.charging && !sessionStarted) {
            sessionStarted = true
            sessionPeakWatts = 0.0
            sessionSumWatts = 0.0
            sessionSamples = 0
        } else if (!snapshot.charging && sessionStarted) {
            saveSessionPeak()
            sessionStarted = false
        }

        if (snapshot.charging) {
            sessionPeakWatts = max(sessionPeakWatts, snapshot.watts)
            sessionSumWatts += snapshot.watts
            sessionSamples++
        }

        val avg = if (sessionSamples > 0) sessionSumWatts / sessionSamples else 0.0
        chargingView.update(snapshot, sessionPeakWatts, avg)
    }

    private fun saveSessionPeak() {
        if (sessionSamples == 0) return
        val prefs = getSharedPreferences("charging_stats", MODE_PRIVATE)
        prefs.edit()
            .putFloat("last_peak_w", sessionPeakWatts.toFloat())
            .putFloat("last_avg_w", (sessionSumWatts / sessionSamples).toFloat())
            .apply()
    }
}
