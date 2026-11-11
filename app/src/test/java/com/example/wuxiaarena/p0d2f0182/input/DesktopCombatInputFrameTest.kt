package com.example.wuxiaarena.p0d2f0182.input

import android.view.KeyEvent
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class DesktopCombatInputFrameTest {
    private val head = ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0))

    @Before
    fun enablePreview() {
        DesktopCombatInput.configure(true)
        DesktopCombatInput.reset()
    }

    @After
    fun disablePreview() {
        DesktopCombatInput.configure(false)
    }

    @Test
    fun identicalTriggersAndAndroidKeyDownBeforeTheNextFrameDoNotRestartThePath() {
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        val started = longField("startedAtNanos")
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        assertTrue(DesktopCombatInput.handleKey(KeyEvent.KEYCODE_1, true, 0))
        assertEquals(started, longField("startedAtNanos"))
        assertEquals(0L, longField("actionStartedInFrame"))
    }

    @Test
    fun aNewSampledFramePermitsAnIntentionalNewActionOfTheSameKind() {
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        val previousFrame = longField("actionStartedInFrame")
        assertNotNull(DesktopCombatInput.frame(head, System.nanoTime()))
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        assertNotEquals(previousFrame, longField("actionStartedInFrame"))
        assertEquals(DesktopCombatAction.SLASH, field("action"))
    }

    @Test
    fun differentActionsInTheSameFrameKeepTheirRequestOrder() {
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        DesktopCombatInput.trigger(DesktopCombatAction.THRUST)
        assertEquals(DesktopCombatAction.THRUST, field("action"))
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        assertEquals(DesktopCombatAction.SLASH, field("action"))
    }

    @Test
    fun keyboardHoldCanPromoteATappedGuardAndReleaseSurvivesADuplicateTap() {
        DesktopCombatInput.trigger(DesktopCombatAction.GUARD_OVERHEAD)
        val started = longField("startedAtNanos")
        assertTrue(DesktopCombatInput.handleKey(KeyEvent.KEYCODE_V, true, 0))
        assertEquals(started, longField("startedAtNanos"))
        assertEquals(true, field("guardHeld"))
        DesktopCombatInput.trigger(DesktopCombatAction.GUARD_OVERHEAD)
        assertEquals(true, field("guardHeld"))
        assertTrue(DesktopCombatInput.handleKey(KeyEvent.KEYCODE_V, false, 0))
        val release = field("guardReleasedAtNanos")
        assertNotNull(release)
        DesktopCombatInput.trigger(DesktopCombatAction.GUARD_OVERHEAD)
        assertEquals(false, field("guardHeld"))
        assertEquals(release, field("guardReleasedAtNanos"))
    }

    @Test
    fun resetDisableAndEnableClearTheCoalescingIdentity() {
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        DesktopCombatInput.reset()
        assertEquals(-1L, longField("actionStartedInFrame"))
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        assertEquals(0L, longField("actionStartedInFrame"))
        DesktopCombatInput.configure(false)
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        assertFalse(DesktopCombatInput.enabled)
        assertNull(field("action"))
        assertEquals(-1L, longField("actionStartedInFrame"))
        DesktopCombatInput.configure(true)
        DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
        assertEquals(DesktopCombatAction.SLASH, field("action"))
    }

    private fun longField(name: String): Long = DesktopCombatInput::class.java.getDeclaredField(name).let {
        it.isAccessible = true
        it.getLong(DesktopCombatInput)
    }

    private fun field(name: String): Any? = DesktopCombatInput::class.java.getDeclaredField(name).let {
        it.isAccessible = true
        it.get(DesktopCombatInput)
    }
}
