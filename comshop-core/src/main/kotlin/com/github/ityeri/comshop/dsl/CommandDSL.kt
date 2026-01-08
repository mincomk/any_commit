package com.github.ityeri.comshop.dsl

import com.github.ityeri.comshop.dsl.ComshopDSL
import com.github.ityeri.comshop.LiteralCommandBuilder

@ComshopDSL
class CommandDSL(override val name: String) : LiteralCommandBuilder() {
    companion object {
        fun command(name: String, block: CommandDSL.() -> Unit = {}): CommandDSL {
            val commandDsl = CommandDSL(name)
            commandDsl.apply(block)
            return commandDsl
        }
    }

    fun then(name: String, block: CommandDSL.() -> Unit) {
        val commandDsl = CommandDSL(name)
        subCommands.add(commandDsl)
        commandDsl.apply(block)
    }
}