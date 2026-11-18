package com.example.wuxiaarena.p0d2f0182.content

internal const val FATAL_GLYPH = 10
internal const val HEAD_GLYPH = 11
internal const val GUARDED_GLYPH = 12

internal data class DamageGlyphQuad(
    val glyph: Int,
    val left: Float,
    val right: Float,
    val bottom: Float,
    val top: Float,
)

internal fun damageGlyphQuads(content: DamagePopupContent): List<DamageGlyphQuad> {
    require(content.amount >= 0)
    val digits = content.amount.toString()
    val label = when {
        content.fatal -> FATAL_GLYPH
        content.guarded -> GUARDED_GLYPH
        content.headHit -> HEAD_GLYPH
        else -> null
    }
    val digitY = if (label == null) 0f else 0.018f
    return buildList {
        digits.forEachIndexed { index, digit ->
            val centerX = (index - (digits.length - 1) * 0.5f) * 0.035f
            add(DamageGlyphQuad(digit.digitToInt(), centerX - 0.019f, centerX + 0.019f,
                digitY - 0.033f, digitY + 0.033f))
        }
        if (label != null) add(DamageGlyphQuad(label, -0.031f, 0.031f, -0.050f, -0.018f))
    }
}
