package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.pico.spatial.core.ecs.BoundingBox
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.ModelEntity
import com.pico.spatial.core.ecs.resource.BlendingMode
import com.pico.spatial.core.ecs.resource.MaterialCullingMode
import com.pico.spatial.core.ecs.resource.MeshModel
import com.pico.spatial.core.ecs.resource.MeshResource
import com.pico.spatial.core.ecs.resource.UnlitMaterial
import com.pico.spatial.core.math.Color4
import com.pico.spatial.core.math.Vector3

/** A translucent 65ms wake and a 12ms hot edge swept by the actual Stage-space blade samples. */
internal class PlayerBladeTrail(private val root: Entity) : AutoCloseable {
    private val history = BladeTrailGeometry()
    private var entity: ModelEntity? = null
    private var mesh: MeshResource? = null
    private var material: UnlitMaterial? = null
    private var round = Long.MIN_VALUE
    private var opponentRound = 0
    private var hand: Hand? = null
    private var inputOrigin: InputOrigin? = null
    private var closed = false
    private var failed = false
    private val receipts = BladeTrailReceiptBudget()
    private val frameReceipts = BladeTrailFrameReceipt()
    private var firstPresentReceipt = false
    private var receiptOpen = false
    private var presentCalls = 0L
    private var inactiveCalls = 0L
    private var missingEndpoints = 0L
    private var identityClears = 0L
    private var changedPoses = 0L
    private var generationChanges = 0L
    private var lastReceiptBase: com.example.wuxiaarena.core.math.Vector3? = null
    private var lastReceiptTip: com.example.wuxiaarena.core.math.Vector3? = null
    private var lastReceiptGeneration: Long? = null
    private var restCalls = 0L
    private var geometryNulls = 0L
    private var creates = 0L
    private var replaces = 0L
    private var enables = 0L
    private var lastReceiptCall: Long? = null
    private var minCallGap = Long.MAX_VALUE
    private var maxCallGap = 0L

    init { runCatching { Log.i(TAG, "receipt=constructed rootValid=${root.valid}") } }

    fun present(state: ArenaViewState) {
        val receiptNow = System.nanoTime()
        val sourceBase = state.playerBladeBase
        val sourceTip = state.playerBladeTip
        val sourceBlade = if (sourceBase != null && sourceTip != null) sourceTip - sourceBase else null
        val validSource = sourceBase?.isFinite() == true && sourceTip?.isFinite() == true &&
            sourceBlade?.isFinite() == true && sourceBlade.length().let { it.isFinite() && it > 0.0 } &&
            state.playerBladeTipSpeed.isFinite() && state.playerBladeTipSpeed >= 0.0
        val canArmReceipt = !closed && !failed && root.valid && state.roundGeneration >= round &&
            state.sceneReady && state.inputReady && state.pauseReason == null &&
            state.result == TrialResult.FIGHTING && validSource
        receiptOpen = receipts.collecting(receiptNow, canArmReceipt)
        if (!firstPresentReceipt) {
            firstPresentReceipt = true
            runCatching { Log.i(TAG, "receipt=first_present round=${state.roundGeneration} result=${state.result}") }
        }
        if (receiptOpen) {
            presentCalls++
            if (state.playerBladeAtRest) restCalls++
            if (sourceBase != lastReceiptBase || sourceTip != lastReceiptTip) changedPoses++
            lastReceiptGeneration?.let { if (it != state.playerMotionGeneration) generationChanges++ }
            lastReceiptBase = sourceBase
            lastReceiptTip = sourceTip
            lastReceiptGeneration = state.playerMotionGeneration
            lastReceiptCall?.let { before ->
                if (receiptNow >= before) {
                    val gap = receiptNow - before
                    minCallGap = minOf(minCallGap, gap)
                    maxCallGap = maxOf(maxCallGap, gap)
                }
            }
            lastReceiptCall = receiptNow
        }
        if (closed || failed || !root.valid || state.roundGeneration < round) {
            receipt(state, receiptNow, "owner_rejected")
            return
        }
        try {
            if (state.roundGeneration != round || state.roundNumber != opponentRound ||
                state.dominantHand != hand || state.inputOrigin != inputOrigin
            ) {
                if (receiptOpen) identityClears++
                clear()
                round = state.roundGeneration
                opponentRound = state.roundNumber
                hand = state.dominantHand
                inputOrigin = state.inputOrigin
            }
            val base = state.playerBladeBase
            val tip = state.playerBladeTip
            val active = state.sceneReady && state.inputReady && state.pauseReason == null &&
                (state.result == TrialResult.FIGHTING || state.result == TrialResult.ROUND_CLEAR)
            if (!active || base == null || tip == null) {
                if (receiptOpen) {
                    if (!active) inactiveCalls++
                    if (base == null || tip == null) missingEndpoints++
                }
                clear()
                receipt(state, receiptNow, "inactive_or_missing")
                return
            }
            val ribbon = history.sample(
                base, tip, System.nanoTime(), state.playerBladeTipSpeed,
                state.playerBladeAtRest, state.playerMotionGeneration,
            )
            if (ribbon == null) {
                if (receiptOpen) geometryNulls++
                entity?.takeIf { it.valid }?.enabled = false
                receipt(state, System.nanoTime(), "geometry_null")
                return
            }
            // The entity is root-local, while tracking samples are in Stage coordinates.
            val positions = ribbon.positions.map { point ->
                root.convertPositionFrom(Vector3(point.x.toFloat(), point.y.toFloat(), point.z.toFloat()), null)
                    .also { check(it.x.isFinite() && it.y.isFinite() && it.z.isFinite()) }
            }
            val model = MeshModel(
                positions = positions,
                triangleIndices = ribbon.triangleIndices,
                colors = ribbon.alphas.mapIndexed { index, alpha ->
                    if (index < ribbon.coreVertexOffset) Color4(0.78f, 0.88f, 0.96f, alpha * 0.26f)
                    else Color4(1.0f, 0.96f, 0.82f, alpha * 0.86f)
                },
            )
            val bounds = boundsOf(positions)
            val existing = mesh
            if (existing == null) {
                create(model, bounds)
                if (receiptOpen) creates++
            } else {
                check(existing.replaceWithMeshModel(model, bounds)) { "Blade ribbon mesh update was rejected" }
                if (receiptOpen) replaces++
            }
            checkNotNull(entity).enabled = true
            if (receiptOpen) enables++
            receipt(state, System.nanoTime(), "submitted", ribbon, model.colors?.size ?: 0,
                if (existing == null) "create" else "replace")
        } catch (error: Exception) {
            failed = true
            close()
            Log.w(TAG, "Player blade trail became unavailable", error)
        }
    }

    /** Call before destroying root, including partially initialized scenes. */
    override fun close() {
        if (closed) return
        closed = true
        history.clear()
        try { entity?.takeIf { it.valid }?.destroy() } catch (error: Exception) {
            Log.w(TAG, "Unable to destroy blade trail entity", error)
        }
        entity = null
        try { mesh?.close() } catch (error: Exception) {
            Log.w(TAG, "Unable to release blade trail mesh", error)
        }
        mesh = null
        try { material?.close() } catch (error: Exception) {
            Log.w(TAG, "Unable to release blade trail material", error)
        }
        material = null
    }

    private fun clear() {
        history.clear()
        entity?.takeIf { it.valid }?.enabled = false
    }

    private fun create(model: MeshModel, bounds: BoundingBox) {
        MeshModel.validateOrThrow(model)
        val nextMesh = MeshResource.createWithMeshModel(model, bounds, "player_blade_trail")
        mesh = nextMesh
        nextMesh.toGlobal()
        val nextMaterial = UnlitMaterial.create(BlendingMode.TRANSPARENT)
        material = nextMaterial
        nextMaterial.toGlobal()
        nextMaterial.setBaseColor(Color4(1f, 1f, 1f, 1f))
        nextMaterial.setCullingMode(MaterialCullingMode.NONE)
        nextMaterial.setDepthTest(true)
        nextMaterial.setDepthWrite(false)
        nextMaterial.setApplyToneMapping(true)
        val nextEntity = ModelEntity(nextMesh, nextMaterial)
        entity = nextEntity
        nextEntity.enabled = false
        check(root.addChild(nextEntity)) { "Unable to attach player blade trail" }
    }

    /** Five summaries, one first-submit and one first UI-batch hide; two owner receipts. */
    private fun receipt(
        state: ArenaViewState, now: Long, outcome: String,
        ribbon: BladeTrailGeometry.Ribbon? = null, colorCount: Int = 0, operation: String = "-",
    ) {
        runCatching {
            if (receiptOpen && receipts.collecting(now, false)) {
                frameReceipts.observe(BladeTrailFrameSample(
                    state.diagnosticUiFrameNanos, state.diagnosticPublishSource, state.diagnosticHandStamp,
                    now, outcome, state.playerBladeAtRest, state.playerMotionGeneration,
                    state.roundGeneration, state.roundNumber, state.dominantHand, state.inputOrigin,
                    state.result.name, state.sceneReady, state.inputReady,
                ))
            }
        }
        val kind = receipts.next(now, outcome == "submitted", frameReceipts.firstPair != null) ?: return
        // Diagnostics cannot turn a successful frame into a rendering failure.
        runCatching {
            val peak = ribbon?.alphas?.mapIndexed { index, alpha ->
                alpha * if (index < ribbon.coreVertexOffset) 0.26f else 0.86f
            }?.maxOrNull()
            val entityState = runCatching { "entityValid=${entity?.valid} enabled=${entity?.enabled}" }
                .getOrElse { "entityState=read_unavailable:${it.javaClass.simpleName}" }
            val coreReceipt = "receipt=$kind nowNs=$now outcome=$outcome operation=$operation " +
                "round=${state.roundGeneration}/${state.roundNumber} result=${state.result} " +
                "ready=${state.sceneReady}/${state.inputReady} pause=${state.pauseReason} " +
                "rest=${state.playerBladeAtRest} speed=${state.playerBladeTipSpeed} motionGen=${state.playerMotionGeneration} " +
                "calls=$presentCalls inactive=$inactiveCalls missing=$missingEndpoints identityClear=$identityClears " +
                "restCalls=$restCalls changedPoses=$changedPoses generationChanges=$generationChanges " +
                "nulls=$geometryNulls create=$creates replace=$replaces enable=$enables " +
                "vertices=${ribbon?.positions?.size ?: 0} colors=$colorCount triangles=${(ribbon?.triangleIndices?.size ?: 0) / 3} " +
                "cpuPeakAlpha=$peak $entityState " +
                "base=${state.playerBladeBase} tip=${state.playerBladeTip} head=${state.playerHeadPosition} " +
                "sourceOrigin=${state.inputOrigin} " +
                "minCallGapNs=${if (minCallGap == Long.MAX_VALUE) null else minCallGap} maxCallGapNs=$maxCallGap " +
                "frameKind=COMPOSE_UI_BATCH_NOT_GPU uiFrameNs=${state.diagnosticUiFrameNanos} " +
                "publishSource=${state.diagnosticPublishSource} handObservationStamp=${state.diagnosticHandStamp} " +
                "handStampClock=HOST_RECEIPT " + frameReceipts.receiptFields()
            val line = bladeTrailReceiptLine(coreReceipt,
                { material?.getOpacity()?.toString() },
                { material?.getBaseColor()?.alpha?.toString() })
            Log.i(TAG, line)
        }
    }

    private fun boundsOf(positions: List<Vector3>): BoundingBox {
        val minX = positions.minOf { it.x }
        val minY = positions.minOf { it.y }
        val minZ = positions.minOf { it.z }
        val maxX = positions.maxOf { it.x }
        val maxY = positions.maxOf { it.y }
        val maxZ = positions.maxOf { it.z }
        return BoundingBox(
            center = Vector3((minX + maxX) * 0.5f, (minY + maxY) * 0.5f, (minZ + maxZ) * 0.5f),
            halfExtent = Vector3((maxX - minX) * 0.5f, (maxY - minY) * 0.5f, (maxZ - minZ) * 0.5f),
        )
    }

    private companion object {
        const val TAG = "ArenaBladeTrail"
    }
}

/** Getter failures are fields in the receipt, never a reason to lose submission evidence. */
internal fun bladeTrailReceiptLine(
    core: String, readOpacity: () -> String?, readBaseAlpha: () -> String?,
): String {
    val opacity = runCatching { readOpacity() ?: "not_created" }
        .getOrElse { "read_unavailable:${it.javaClass.simpleName}" }
    val baseAlpha = runCatching { readBaseAlpha() ?: "not_created" }
        .getOrElse { "read_unavailable:${it.javaClass.simpleName}" }
    return "$core materialOpacity=$opacity materialBaseAlpha=$baseAlpha"
}

/** Log budget only. It never controls sampling, geometry, visibility or gameplay. */
internal class BladeTrailReceiptBudget {
    private var start: Long? = null
    private var lastSummary: Long? = null
    private var summaries = 0
    private var firstSubmit = false
    private var firstPair = false

    fun collecting(now: Long, eligibleRoundRunning: Boolean): Boolean {
        val began = start ?: if (eligibleRoundRunning) now.also { start = it } else return false
        return now - began in 0L until 6_000_000_000L
    }

    fun next(now: Long, submitted: Boolean, hasFirstPair: Boolean = false): String? {
        if (!collecting(now, false)) return null
        if (submitted && !firstSubmit) {
            firstSubmit = true
            return "first_submit"
        }
        if (hasFirstPair && !firstPair) {
            firstPair = true
            return "first_ui_batch_hide"
        }
        if (summaries < 5 && (lastSummary == null || now - checkNotNull(lastSummary) >= 1_000_000_000L)) {
            summaries++
            lastSummary = now
            return "summary"
        }
        return null
    }
}

/** Provenance of an already-completed presentation operation, never a GPU-frame claim. */
internal data class BladeTrailFrameSample(
    val uiFrameNanos: Long?,
    val publishSource: String,
    val handStamp: ObservationStamp?,
    val wallNanos: Long,
    val outcome: String,
    val rest: Boolean,
    val motionGeneration: Long,
    val roundGeneration: Long,
    val roundNumber: Int,
    val hand: Hand,
    val inputOrigin: InputOrigin?,
    val result: String,
    val sceneReady: Boolean,
    val inputReady: Boolean,
) {
    fun receiptFields(): String =
        "uiFrameNs=$uiFrameNanos publishSource=$publishSource handObservationStamp=$handStamp " +
            "wallNs=$wallNanos outcome=$outcome rest=$rest motionGen=$motionGeneration " +
            "round=$roundGeneration/$roundNumber hand=$hand origin=$inputOrigin result=$result " +
            "ready=$sceneReady/$inputReady"
}

/** Counts real submit-to-hide operation edges inside one explicitly supplied UI batch. */
internal class BladeTrailFrameReceipt {
    data class HidePair(val submitted: BladeTrailFrameSample, val hidden: BladeTrailFrameSample) {
        val identityBoundary: Boolean get() = submitted.roundGeneration != hidden.roundGeneration ||
            submitted.roundNumber != hidden.roundNumber || submitted.hand != hidden.hand ||
            submitted.inputOrigin != hidden.inputOrigin || submitted.motionGeneration != hidden.motionGeneration

        fun receiptFields(): String = "identityBoundary=$identityBoundary " +
            "before={${submitted.receiptFields()}} after={${hidden.receiptFields()}}"
    }

    private var submitted: BladeTrailFrameSample? = null
    var sameUiBatchHides = 0L
        private set
    var sameUiBatchRestHides = 0L
        private set
    var sameUiBatchNullHides = 0L
        private set
    var identityBoundaryHides = 0L
        private set
    var firstPair: HidePair? = null
        private set

    fun observe(sample: BladeTrailFrameSample) {
        if (sample.uiFrameNanos == null || sample.uiFrameNanos != submitted?.uiFrameNanos) submitted = null
        if (sample.uiFrameNanos == null) return
        if (sample.outcome == "submitted") {
            submitted = sample
            return
        }
        if (sample.outcome != "geometry_null" && sample.outcome != "inactive_or_missing") return
        val before = submitted ?: return
        val pair = HidePair(before, sample)
        sameUiBatchHides++
        if (sample.rest) sameUiBatchRestHides++
        if (sample.outcome == "geometry_null") sameUiBatchNullHides++
        if (pair.identityBoundary) identityBoundaryHides++
        if (firstPair == null) firstPair = pair
        submitted = null
    }

    fun receiptFields(): String = "sameUiBatchHides=$sameUiBatchHides " +
        "sameUiBatchRestHides=$sameUiBatchRestHides sameUiBatchNullHides=$sameUiBatchNullHides " +
        "identityBoundaryHides=$identityBoundaryHides firstUiBatchHide={${firstPair?.receiptFields() ?: "none"}}"
}
