package com.example.wuxiaarena.p0d2f0182.content

import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.NativeProbe
import com.pico.spatial.core.ecs.resource.LoadPlan
import com.pico.spatial.core.ecs.resource.TextureProbe
import com.pico.spatial.core.ecs.resource.TextureResource
import java.util.concurrent.CancellationException
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.async
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.yield
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Runs actual SceneLighting against controlled native failures and real coroutine dispatch. */
class SceneLightingLifecycleTest {
    @Before fun resetDoubles() {
        NativeProbe.reset()
        TextureProbe.reset()
    }

    private fun plan(texture: TextureResource = TextureResource(), block: Boolean = true): LoadPlan =
        LoadPlan(texture, block).also { TextureProbe.plan = it }

    private fun awaitIo(plan: LoadPlan) {
        assertTrue("IO load did not enter", plan.entered.await(5, TimeUnit.SECONDS))
    }

    private suspend fun assertLoadCancelled(task: Deferred<Unit>): Throwable {
        val failure = runCatching { withTimeout(5_000) { task.await() } }.exceptionOrNull()
        assertTrue("Expected caller cancellation, got $failure", failure is CancellationException)
        return checkNotNull(failure)
    }

    @Test fun inFlightCloseWaitsForLateTextureCleanup() = runBlocking {
        val root = Entity()
        val lighting = SceneLighting.attach(root)
        val plan = plan()
        val load = async { lighting.loadEnvironment("test.ktx") { true } }
        try {
            yield()
            awaitIo(plan)
            lighting.close()
            assertFalse(root.children.single().valid)
            assertFalse("Pending IO still owns a resource", lighting.isReleased)
        } finally {
            plan.release.countDown()
        }
        assertLoadCancelled(load)
        assertTrue(plan.texture.closed)
        assertEquals(1, plan.texture.closeCalls)
        assertEquals(0, NativeProbe.environmentAttachments.get())
        assertTrue(lighting.isReleased)
    }

    @Test fun lateTextureCloseFailureRetainsHandleForRetry() = runBlocking {
        val lighting = SceneLighting.attach(Entity())
        val plan = plan(TextureResource(closeFailures = 1))
        val load = async { lighting.loadEnvironment("test.ktx") { true } }
        try {
            yield()
            awaitIo(plan)
            lighting.close()
            assertFalse(lighting.isReleased)
        } finally {
            plan.release.countDown()
        }
        val failure = assertLoadCancelled(load)
        assertTrue(failure.suppressed.any { it.message == "Injected texture close failure" })
        assertFalse(plan.texture.closed)
        assertFalse(lighting.isReleased)
        lighting.close()
        assertTrue(plan.texture.closed)
        assertEquals(2, plan.texture.closeCalls)
        assertEquals(0, NativeProbe.environmentAttachments.get())
        assertTrue(lighting.isReleased)
    }

    @Test fun destroyFailureBlocksAdoptionAndRemainsRetryable() = runBlocking {
        val root = Entity()
        val lighting = SceneLighting.attach(root)
        val rig = root.children.single()
        val plan = plan()
        val load = async { lighting.loadEnvironment("test.ktx") { true } }
        try {
            yield()
            awaitIo(plan)
            rig.destroyFailures = 1
            assertTrue(runCatching { lighting.close() }.exceptionOrNull() is IllegalStateException)
            assertTrue(rig.valid)
            assertFalse(lighting.isReleased)
            assertTrue(runCatching {
                lighting.loadEnvironment("second.ktx") { true }
            }.exceptionOrNull() is IllegalStateException)
            assertEquals(1, TextureProbe.loads.get())
        } finally {
            plan.release.countDown()
        }
        assertLoadCancelled(load)
        assertTrue(plan.texture.closed)
        assertEquals(0, NativeProbe.environmentAttachments.get())
        assertFalse("Rig destruction still needs a retry", lighting.isReleased)
        lighting.close()
        assertFalse(rig.valid)
        assertEquals(2, rig.destroyCalls)
        assertTrue(lighting.isReleased)
    }

    @Test fun adoptedTextureCloseFailureRetainsHandleForRetry() = runBlocking {
        val root = Entity()
        val lighting = SceneLighting.attach(root)
        val rig = root.children.single()
        val plan = plan(TextureResource(closeFailures = 1), block = false)
        withTimeout(5_000) { lighting.loadEnvironment("test.ktx") { true } }
        assertEquals(1, NativeProbe.environmentAttachments.get())
        assertTrue(runCatching { lighting.close() }.exceptionOrNull() is IllegalStateException)
        assertFalse(rig.valid)
        assertFalse(plan.texture.closed)
        assertFalse(lighting.isReleased)
        lighting.close()
        assertTrue(plan.texture.closed)
        assertEquals(2, plan.texture.closeCalls)
        assertEquals(1, rig.destroyCalls)
        assertTrue(lighting.isReleased)
    }

    @Test fun callerCancellationAtIoCompletionClosesPendingWithoutAttachment() = runBlocking {
        val lighting = SceneLighting.attach(Entity())
        val plan = plan()
        val load = async { lighting.loadEnvironment("test.ktx") { true } }
        try {
            yield()
            awaitIo(plan)
            load.cancel(CancellationException("Injected caller cancellation"))
        } finally {
            plan.release.countDown()
        }
        withTimeout(5_000) { load.join() }
        assertTrue(plan.texture.closed)
        assertEquals(1, plan.texture.closeCalls)
        assertEquals(0, NativeProbe.environmentAttachments.get())
        assertFalse("Live lighting rig still belongs to its owner", lighting.isReleased)
        lighting.close()
        assertTrue(lighting.isReleased)
    }

    @Test fun repeatedSuccessfulCloseIsIdempotent() = runBlocking {
        val root = Entity()
        val lighting = SceneLighting.attach(root)
        val rig = root.children.single()
        val plan = plan(block = false)
        withTimeout(5_000) { lighting.loadEnvironment("test.ktx") { true } }
        lighting.close()
        lighting.close()
        lighting.close()
        assertTrue(lighting.isReleased)
        assertEquals(1, rig.destroyCalls)
        assertEquals(1, plan.texture.closeCalls)
    }

    @Test fun awaitReleaseWaitsForIoCleanupThenReleases() = runBlocking {
        val root = Entity()
        val lighting = SceneLighting.attach(root)
        val rig = root.children.single()
        val plan = plan()
        val load = async { lighting.loadEnvironment("test.ktx") { true } }
        try {
            yield()
            awaitIo(plan)
            val release = async(start = CoroutineStart.UNDISPATCHED) { lighting.awaitRelease() }
            assertFalse("Release must wait for the outstanding IO result", release.isCompleted)
            assertFalse(lighting.isReleased)
            plan.release.countDown()
            assertLoadCancelled(load)
            withTimeout(5_000) { release.await() }
            assertTrue(plan.texture.closed)
            assertEquals(1, plan.texture.closeCalls)
            assertEquals(1, rig.destroyCalls)
            assertEquals(0, NativeProbe.environmentAttachments.get())
            assertTrue(lighting.isReleased)
        } finally {
            plan.release.countDown()
        }
    }

    @Test fun cancelledOldLoadCompletesGateAndWakesReleaseWaiter() = runBlocking {
        val lighting = SceneLighting.attach(Entity())
        val plan = plan()
        val load = async { lighting.loadEnvironment("test.ktx") { true } }
        try {
            yield()
            awaitIo(plan)
            val release = async(start = CoroutineStart.UNDISPATCHED) { lighting.awaitRelease() }
            assertFalse(release.isCompleted)
            load.cancel(CancellationException("Old initializer was cancelled"))
            plan.release.countDown()
            withTimeout(5_000) { load.join() }
            withTimeout(5_000) { release.await() }
            assertTrue(load.isCancelled)
            assertTrue(plan.texture.closed)
            assertEquals(1, plan.texture.closeCalls)
            assertEquals(0, NativeProbe.environmentAttachments.get())
            assertTrue(lighting.isReleased)
        } finally {
            plan.release.countDown()
        }
    }

    @Test fun cancelledWaiterDoesNotCancelIndependentLoadGate() = runBlocking {
        val lighting = SceneLighting.attach(Entity())
        val plan = plan()
        val load = async { lighting.loadEnvironment("test.ktx") { true } }
        try {
            yield()
            awaitIo(plan)
            val firstWaiter = async(start = CoroutineStart.UNDISPATCHED) { lighting.awaitRelease() }
            assertFalse(firstWaiter.isCompleted)
            firstWaiter.cancel(CancellationException("Replacement builder was cancelled"))
            withTimeout(5_000) { firstWaiter.join() }
            assertFalse("IO is still deterministically blocked", load.isCompleted)
            assertFalse(lighting.isReleased)
            val nextWaiter = async(start = CoroutineStart.UNDISPATCHED) { lighting.awaitRelease() }
            assertFalse("A cancelled prior waiter must not cancel the shared gate", nextWaiter.isCompleted)
            plan.release.countDown()
            assertLoadCancelled(load)
            withTimeout(5_000) { nextWaiter.await() }
            assertTrue(plan.texture.closed)
            assertEquals(1, plan.texture.closeCalls)
            assertTrue(lighting.isReleased)
        } finally {
            plan.release.countDown()
        }
    }

    @Test fun awaitReleaseWithoutInflightLoadCompletesImmediately() = runBlocking {
        val root = Entity()
        val lighting = SceneLighting.attach(root)
        val release = async(start = CoroutineStart.UNDISPATCHED) { lighting.awaitRelease() }
        assertTrue("No load gate exists to wait for", release.isCompleted)
        release.await()
        assertTrue(lighting.isReleased)
        assertEquals(1, root.children.single().destroyCalls)
        assertEquals(0, TextureProbe.loads.get())
    }

    @Test fun awaitReleasePropagatesCleanupFailureAndKeepsOwnerRetryable() = runBlocking {
        val root = Entity()
        val lighting = SceneLighting.attach(root)
        val rig = root.children.single()
        val plan = plan(TextureResource(closeFailures = 1), block = false)
        withTimeout(5_000) { lighting.loadEnvironment("test.ktx") { true } }
        val failure = runCatching { lighting.awaitRelease() }.exceptionOrNull()
        assertEquals("Injected texture close failure", failure?.message)
        assertFalse(lighting.isReleased)
        assertFalse(plan.texture.closed)
        assertFalse(rig.valid)
        withTimeout(5_000) { lighting.awaitRelease() }
        assertTrue(lighting.isReleased)
        assertTrue(plan.texture.closed)
        assertEquals(2, plan.texture.closeCalls)
        assertEquals(1, rig.destroyCalls)
    }
}
