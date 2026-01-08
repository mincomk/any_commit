package com.github.ityeri.comshop.dsl

import com.github.ityeri.comshop.LiteralCommandBuilder

fun command(name: String, block: CommandDSL.() -> Unit = {}): CommandDSL {
    val commandDsl = CommandDSL(name)
    commandDsl.apply(block)
    return commandDsl
}

@ComshopDSL
class CommandDSL(override val name: String) : LiteralCommandBuilder()