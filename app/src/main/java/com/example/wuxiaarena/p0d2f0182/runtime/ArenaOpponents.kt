package com.example.wuxiaarena.p0d2f0182.runtime

internal data class ArenaOpponent(val name: String, val asset: String)

internal val arenaOpponents = listOf(
    ArenaOpponent("试刀客", "asset://models/opponents/base.glb"),
    ArenaOpponent("青衫护院", "asset://models/opponents/indigo.glb"),
    ArenaOpponent("玄甲守擂", "asset://models/opponents/veteran.glb"),
)
