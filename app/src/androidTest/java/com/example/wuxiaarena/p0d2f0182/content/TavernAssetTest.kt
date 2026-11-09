package com.example.wuxiaarena.p0d2f0182.content

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.DataInputStream
import java.io.FileNotFoundException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class TavernAssetTest {
    @Test
    fun packagedModelHasAGltf2Header() {
        val assets = InstrumentationRegistry.getInstrumentation().targetContext.assets
        val header = ByteArray(12)
        DataInputStream(assets.open("models/tavern_slice.glb")).use { it.readFully(header) }

        assertArrayEquals(byteArrayOf(0x67, 0x6c, 0x54, 0x46), header.copyOfRange(0, 4))
        assertEquals(2, ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN).getInt(4))
    }

    @Test
    fun absentModelIsNotReportedAsAnExistingAsset() {
        val assets = InstrumentationRegistry.getInstrumentation().targetContext.assets

        assertThrows(FileNotFoundException::class.java) {
            assets.open("models/absent_test_model.glb").close()
        }
    }
}
