package com.github.ityeri.comshop.dsl

import com.github.ityeri.comshop.argument.ArgumentChainNode
import com.github.ityeri.comshop.argument.ArgumentNode
import com.github.ityeri.comshop.argument.SingleArgumentNode
import com.mojang.brigadier.arguments.ArgumentType

class ArgumentListDSL {
    internal val arguments: MutableList<ArgumentNode> = mutableListOf()

    infix fun <T> String.to(argumentType: ArgumentType<T>) {
        arguments.add(SingleArgumentNode(argumentType, this))
    }

    infix fun <T> String.to(block: () -> ArgumentType<T>) {
        arguments.add(SingleArgumentNode(block(), this))
    }

    fun then(block: ArgumentChainDSL.() -> Unit) {
        arguments.add(ArgumentChainDSL().apply(block).build())
    }

    fun union(block: ArgumentListDSL.() -> Unit) {
        val unionArguments = ArgumentListDSL().apply(block).arguments
        val argumentUnionNode = ArgumentChainNode(unionArguments.map { listOf(it) })
        arguments.add(argumentUnionNode)
    }
}