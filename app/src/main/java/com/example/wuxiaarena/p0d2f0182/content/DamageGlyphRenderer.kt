package com.example.wuxiaarena.p0d2f0182.content

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.Typeface
import com.pico.spatial.core.ecs.BoundingBox
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.LookAtComponent
import com.pico.spatial.core.ecs.LookAtForwardDirection
import com.pico.spatial.core.ecs.ModelEntity
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.ecs.resource.BlendingMode
import com.pico.spatial.core.ecs.resource.MaterialCullingMode
import com.pico.spatial.core.ecs.resource.MeshModel
import com.pico.spatial.core.ecs.resource.MeshResource
import com.pico.spatial.core.ecs.resource.TextureResource
import com.pico.spatial.core.ecs.resource.UnlitMaterial
import com.pico.spatial.core.math.Color4
import com.pico.spatial.core.math.Vector2
import com.pico.spatial.core.math.Vector3

internal class DamageGlyphRenderer(private val parent: Entity) : AutoCloseable {
    private data class Slot(
        val entity: ModelEntity,
        val mesh: MeshResource,
        val material: UnlitMaterial,
        var content: DamagePopupContent? = null,
        var opacity: Float = -1f,
    )

    private val slots = mutableListOf<Slot>()
    private val resources = ArrayDeque<() -> Unit>()
    private val bounds = BoundingBox(Vector3(0f, 0f, 0f), Vector3(.22f, .08f, .003f))

    fun initialize(tags: List<String>) {
        check(resources.isEmpty())
        try {
            val bitmap = glyphAtlas(tags)
            val texture = try { TextureResource.create(bitmap) } finally { bitmap.recycle() }
            resources.addFirst { texture.close() }
            texture.toGlobal()
            val initial = model(DamagePopupContent(0, 1, false, false, false))
            repeat(DamagePopupTimeline.SLOT_COUNT) { index ->
                val mesh = MeshResource.createWithMeshModel(initial, bounds, "damage_glyphs_$index")
                resources.addFirst { mesh.close() }
                mesh.toGlobal()
                val material = UnlitMaterial.create(BlendingMode.TRANSPARENT)
                resources.addFirst { material.close() }
                material.toGlobal()
                material.setBaseColorTexture(texture)
                material.setCullingMode(MaterialCullingMode.BACK)
                material.setDepthTest(true)
                material.setDepthWrite(false)
                val entity = ModelEntity(mesh, material)
                resources.addFirst { if (entity.valid) entity.destroy() }
                entity.enabled = false
                check(parent.addChild(entity)) { "Could not attach damage glyphs" }
                entity.components.set(LookAtComponent().apply {
                    alignLocalUpToWorldUp = true
                    lookAtForwardDirection = LookAtForwardDirection.POSITIVE_Z
                    setViewerAsTarget()
                })
                slots += Slot(entity, mesh, material)
            }
        } catch (error: Exception) {
            try { close() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
            throw error
        }
    }

    fun present(frames: List<DamagePopupFrame>) {
        slots.forEachIndexed { index, slot ->
            val frame = frames.firstOrNull { it.slot == index }
            if (frame == null) {
                if (slot.content != null) slot.entity.enabled = false
                slot.content = null
                return@forEachIndexed
            }
            if (slot.content != frame.content) {
                check(slot.mesh.replaceWithMeshModel(model(frame.content), bounds)) { "Damage glyph mesh rejected" }
                slot.material.setBaseColor(when {
                    frame.content.fatal || (!frame.content.guarded && frame.content.headHit) -> Color4(.91f, .70f, .36f, 1f)
                    frame.content.guarded -> Color4(.72f, .64f, .51f, 1f)
                    else -> Color4(.95f, .89f, .78f, 1f)
                })
                slot.content = frame.content
                slot.entity.enabled = true
            }
            val point = Vector3(frame.position.x.toFloat(), frame.position.y.toFloat(), frame.position.z.toFloat())
            check(point.x.isFinite() && point.y.isFinite() && point.z.isFinite())
            val transform = checkNotNull(slot.entity.components[TransformComponent::class.java])
            transform.setPosition(parent.convertPositionFrom(point, null))
            transform.setScaleVector(Vector3(frame.scale, frame.scale, frame.scale))
            if (slot.opacity != frame.opacity) {
                slot.material.setOpacity(frame.opacity)
                slot.opacity = frame.opacity
            }
        }
    }

    override fun close() {
        slots.clear()
        var failure: Exception? = null
        while (resources.isNotEmpty()) {
            try { resources.removeFirst().invoke() } catch (error: Exception) {
                if (failure == null) failure = error else failure.addSuppressed(error)
            }
        }
        failure?.let { throw it }
    }

    private fun model(content: DamagePopupContent): MeshModel {
        val vertices = mutableListOf<Vector3>()
        val uv = mutableListOf<Vector2>()
        val indices = mutableListOf<Int>()
        for (quad in damageGlyphQuads(content)) {
            val offset = vertices.size
            vertices += Vector3(quad.left, quad.bottom, 0f)
            vertices += Vector3(quad.right, quad.bottom, 0f)
            vertices += Vector3(quad.right, quad.top, 0f)
            vertices += Vector3(quad.left, quad.top, 0f)
            val left = (quad.glyph % COLUMNS).toFloat() / COLUMNS
            val top = (quad.glyph / COLUMNS).toFloat() / ROWS
            val right = left + 1f / COLUMNS
            val bottom = top + 1f / ROWS
            uv += Vector2(left, bottom)
            uv += Vector2(right, bottom)
            uv += Vector2(right, top)
            uv += Vector2(left, top)
            indices.addAll(listOf(offset, offset + 1, offset + 2, offset, offset + 2, offset + 3))
        }
        return MeshModel(positions = vertices, triangleIndices = indices, uv0 = uv)
    }

    private fun glyphAtlas(tags: List<String>): Bitmap {
        require(tags.size == 3)
        val bitmap = Bitmap.createBitmap(CELL * COLUMNS, CELL * ROWS, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            typeface = Typeface.create("sans-serif", Typeface.BOLD)
            textSize = 54f
            strokeJoin = Paint.Join.ROUND
        }
        for ((index, token) in ((0..9).map(Int::toString) + tags).withIndex()) {
            val ink = Rect()
            paint.getTextBounds(token, 0, token.length, ink)
            require(!ink.isEmpty)
            canvas.save()
            canvas.translate((index % COLUMNS + .5f) * CELL, (index / COLUMNS + .5f) * CELL)
            canvas.scale(50f / ink.width(), 48f / ink.height())
            val x = -ink.exactCenterX()
            val y = -ink.exactCenterY()
            paint.color = Color.rgb(32, 28, 24)
            paint.style = Paint.Style.STROKE
            paint.strokeWidth = 3.5f
            canvas.drawText(token, x, y, paint)
            paint.style = Paint.Style.FILL
            paint.color = Color.WHITE
            canvas.drawText(token, x, y, paint)
            canvas.restore()
        }
        return bitmap
    }

    private companion object {
        const val CELL = 64
        const val COLUMNS = 8
        const val ROWS = 4
    }
}
