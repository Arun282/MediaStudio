package com.codex.lightningcharge

import android.content.Intent
import android.os.BatteryManager
import android.os.Build
import kotlin.math.abs

data class BatterySnapshot(
    val percent: Int,
    val scale: Int,
    val voltage: Double,
    val currentMa: Int,
    val watts: Double,
    val temperature: Double,
    val charging: Boolean,
    val status: Int,
    val health: Int,
    val plugged: Int,
    val technology: String,
    val chargeCounterMah: Double,
    val energyCounterWh: Double,
    val cycleCount: Int?,
    val estimatedMinutesToFull: Int?
)

object BatteryReader {
    fun read(context: android.content.Context, intent: Intent): BatterySnapshot {
        val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, 0).coerceAtLeast(0)
        val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, 100).coerceAtLeast(1)
        val percent = ((level * 100f) / scale).toInt().coerceIn(0, 100)
        val voltage = intent.getIntExtra(BatteryManager.EXTRA_VOLTAGE, 0) / 1000.0
        val status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, BatteryManager.BATTERY_STATUS_UNKNOWN)
        val charging = status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL
        val health = intent.getIntExtra(BatteryManager.EXTRA_HEALTH, BatteryManager.BATTERY_HEALTH_UNKNOWN)
        val plugged = intent.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0)
        val technology = intent.getStringExtra(BatteryManager.EXTRA_TECHNOLOGY).orEmpty()
        val temperature = intent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) / 10.0

        val manager = context.getSystemService(android.content.Context.BATTERY_SERVICE) as BatteryManager
        val rawCurrentUa = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW)
        } else 0
        val currentUa = if (rawCurrentUa == Int.MIN_VALUE) 0 else abs(rawCurrentUa)
        val currentMa = currentUa / 1000
        val watts = voltage * (currentUa / 1_000_000.0)

        val chargeCounterUah = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CHARGE_COUNTER)
        } else Int.MIN_VALUE
        val chargeCounterMah = if (chargeCounterUah > 0) chargeCounterUah / 1000.0 else 0.0

        val energyNwh = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            manager.getLongProperty(BatteryManager.BATTERY_PROPERTY_ENERGY_COUNTER)
        } else Long.MIN_VALUE
        val energyCounterWh = if (energyNwh > 0) energyNwh / 1_000_000_000.0 else 0.0

        val cycleCount = if (Build.VERSION.SDK_INT >= 34) {
            intent.getIntExtra(BatteryManager.EXTRA_CYCLE_COUNT, -1).takeIf { it >= 0 }
        } else null

        val estimatedMinutes = if (charging && percent in 1..99 && currentMa >= 100 && chargeCounterMah > 0) {
            val estimatedFullMah = chargeCounterMah / (percent / 100.0)
            val remainingMah = (estimatedFullMah - chargeCounterMah).coerceAtLeast(0.0)
            (remainingMah / (currentMa / 1000.0) * 60.0).toInt().coerceIn(1, 24 * 60)
        } else null

        return BatterySnapshot(
            percent, scale, voltage, currentMa, watts, temperature, charging, status, health,
            plugged, technology, chargeCounterMah, energyCounterWh, cycleCount, estimatedMinutes
        )
    }

    fun healthLabel(health: Int): String = when (health) {
        BatteryManager.BATTERY_HEALTH_GOOD -> "GOOD"
        BatteryManager.BATTERY_HEALTH_OVERHEAT -> "OVERHEAT"
        BatteryManager.BATTERY_HEALTH_DEAD -> "DEAD"
        BatteryManager.BATTERY_HEALTH_OVER_VOLTAGE -> "OVER VOLTAGE"
        BatteryManager.BATTERY_HEALTH_UNSPECIFIED_FAILURE -> "ERROR"
        else -> "UNKNOWN"
    }

    fun pluggedLabel(plugged: Int): String = when (plugged) {
        BatteryManager.BATTERY_PLUGGED_AC -> "AC"
        BatteryManager.BATTERY_PLUGGED_USB -> "USB"
        BatteryManager.BATTERY_PLUGGED_WIRELESS -> "WIRELESS"
        else -> if (plugged != 0) "CONNECTED" else "BATTERY"
    }
}
