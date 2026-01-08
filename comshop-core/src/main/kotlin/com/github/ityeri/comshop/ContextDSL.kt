package com.github.ityeri.comshop

import com.mojang.brigadier.context.CommandContext
import io.papermc.paper.command.brigadier.CommandSourceStack
import io.papermc.paper.command.brigadier.argument.resolvers.ArgumentResolver
import kotlin.reflect.KClass

class ContextDSL<S>(val context: CommandContext<S>) {
    infix fun <T: Any> String.to(clazz: KClass<T>): T {
        return context.getArgument<T>(this, clazz.java)
    }

    infix fun <T: Any> String.nullOr(clazz: KClass<T>): T? {
        return try {
            context.getArgument<T>(this, clazz.java)
        } catch (e: IllegalArgumentException) {
            null
        }
    }

    infix fun <T: Any> ArgumentResolver<T>.resolve(source: CommandSourceStack): T {
        return resolve(source)
    }

    infix fun <T: Any> ArgumentResolver<List<T>>.resolveFirst(source: CommandSourceStack): T {
        return resolve(source).first()
    }
}