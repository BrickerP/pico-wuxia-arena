package com.example.wuxiaarena.p0d2f0182.content

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class DamageGlyphLayoutTest {
    private val normal = DamagePopupContent(1L, 105, headHit = false, fatal = false, guarded = false)

    @Test
    fun actualAmountIsCenteredAndNeverTruncated() {
        val digits = damageGlyphQuads(normal)
        assertEquals(listOf(1, 0, 5), digits.map { it.glyph })
        assertEquals(-digits.first().left, digits.last().right, 0.00001f)
        assertEquals(-digits[1].left, digits[1].right, 0.00001f)
        assertEquals(-digits.first().bottom, digits.first().top, 0.00001f)
        val large = damageGlyphQuads(normal.copy(amount = Int.MAX_VALUE))
        assertEquals(Int.MAX_VALUE.toString(), large.joinToString("") { it.glyph.toString() })
    }

    @Test
    fun onlyTheHighestPriorityLabelFitsBelowTheRaisedNumber() {
        for ((content, expected) in listOf(
            normal.copy(fatal = true, guarded = true, headHit = true) to FATAL_GLYPH,
            normal.copy(guarded = true, headHit = true) to GUARDED_GLYPH,
            normal.copy(headHit = true) to HEAD_GLYPH,
        )) {
            val quads = damageGlyphQuads(content)
            assertEquals(listOf(1, 0, 5, expected), quads.map { it.glyph })
            val label = quads.last()
            assertEquals(-label.left, label.right, 0.00001f)
            assertTrue(label.top < quads.first().bottom)
            assertTrue(quads.first().bottom > damageGlyphQuads(normal).first().bottom)
        }
    }
}
