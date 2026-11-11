package com.example.wuxiaarena.p0d2f0182.content

/** Transparent corneas retain their PBR layer while the opaque body and eyes flash. */
internal fun isFlashableBodyMaterial(name: String): Boolean =
    name.startsWith("tripo_", ignoreCase = true) &&
        !name.startsWith("tripo_cornea_", ignoreCase = true)
