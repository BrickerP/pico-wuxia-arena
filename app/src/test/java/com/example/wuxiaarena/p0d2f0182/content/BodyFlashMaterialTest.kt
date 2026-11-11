package com.example.wuxiaarena.p0d2f0182.content

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BodyFlashMaterialTest {
    @Test fun opaqueBodyHeadAndEyesFlash() {
        for (name in listOf("tripo_body", "tripo_head", "tripo_eyeball_L_Eye")) {
            assertTrue(isFlashableBodyMaterial(name))
        }
    }

    @Test fun transparentCorneasAndWeaponSlotsKeepTheirMaterials() {
        for (name in listOf("tripo_cornea_L_Eye", "TRIPO_CORNEA_R_EYE", "Steel | sharpened edge", "")) {
            assertFalse(isFlashableBodyMaterial(name))
        }
    }
}
