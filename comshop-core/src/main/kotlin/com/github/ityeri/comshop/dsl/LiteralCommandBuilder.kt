package com.github.ityeri.comshop.dsl

import com.github.ityeri.comshop.ContextDSL
import com.github.ityeri.comshop.argument.ArgumentChainNode
import com.github.ityeri.comshop.argument.ArgumentNode
import com.mojang.brigadier.builder.ArgumentBuilder
import com.mojang.brigadier.builder.LiteralArgumentBuilder
import com.mojang.brigadier.builder.LiteralArgumentBuilder.literal
import com.mojang.brigadier.context.CommandContext
import io.papermc.paper.command.brigadier.CommandSourceStack
import org.bukkit.command.CommandSender

abstract class LiteralCommandBuilder() : CommandBuilder {
    abstract val name: String
    protected val argumentChains: MutableList<List<ArgumentNode>> = mutableListOf()
    protected val subCommands: MutableList<CommandBuilder> = mutableListOf()
    protected var executor:
            ContextDSL<CommandSourceStack>.(source: CommandSourceStack, sender: CommandSender) -> Unit =
        { _, _  -> }
    private var permissionChecker: (source: CommandSourceStack) -> Boolean = { true }

    fun requires(block: (source: CommandSourceStack) -> Boolean) {
        permissionChecker = block
    }

    fun arguments(block: ArgumentListDSL.() -> Unit) {
        argumentChains.add(ArgumentListDSL().apply(block).arguments)
    }

    fun executes(
        block: ContextDSL<CommandSourceStack>.(source: CommandSourceStack, sender: CommandSender) -> Unit
    ) {
        executor = block
    }

    fun <T: CommandBuilder> then(builder: T, block: T.() -> Unit = {}) {
        builder.apply(block)
        subCommands.add(builder)
    }


    override fun createBuilder(): LiteralArgumentBuilder<CommandSourceStack> {
        val rootBuilder = literal<CommandSourceStack>(name)

        rootBuilder.requires { source -> permissionChecker(source) }

        for (subCommand in subCommands) {
            rootBuilder.then(subCommand.createBuilder())
        }

        val executeBlock: (CommandContext<CommandSourceStack>) -> Int = { context ->
            ContextDSL(context).run { executor(context.source, context.source.sender) }
            0
        }

        // TODO 아무리 봐도 이 코드는 좀 아닌것 같음 아니다 꽤 괜찮을지도
        if (argumentChains.isEmpty()) {
            rootBuilder.executes(executeBlock)

        } else {
            val argumentChainNode = ArgumentChainNode(argumentChains)
            val argumentBuilders = argumentChainNode.connectExecuteBlock(executeBlock)
            for (builder in argumentBuilders) {
                rootBuilder.then(builder)
            }
        }

        return rootBuilder
    }
}


fun <S> buildArgumentNodes(
    nodes: List<ArgumentNode>, executeBlock: (CommandContext<S>) -> Int
): List<ArgumentBuilder<S, *>> {
    if (nodes.size == 1) {
        return nodes[0].connectExecuteBlock(executeBlock)
    }
    else {
        return nodes[0].connectArgumentBuilder(
            buildArgumentNodes(nodes.subList(1, nodes.size - 1), executeBlock)
        )
    }
}