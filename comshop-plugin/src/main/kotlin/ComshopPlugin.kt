import com.github.ityeri.comshop.dsl.CommandDSL.Companion.command
import com.github.ityeri.comshop.CommandRegistrar
import com.mojang.brigadier.arguments.BoolArgumentType
import com.mojang.brigadier.arguments.FloatArgumentType
import com.mojang.brigadier.arguments.IntegerArgumentType
import com.mojang.brigadier.arguments.StringArgumentType
import io.papermc.paper.command.brigadier.argument.ArgumentTypes
import io.papermc.paper.command.brigadier.argument.resolvers.selector.PlayerSelectorArgumentResolver
import net.kyori.adventure.text.format.TextColor
import org.bukkit.plugin.java.JavaPlugin


class ComshopPlugin : JavaPlugin() {

    override fun onEnable() {
        CommandRegistrar.lifecycleRegister(this)


        val greetingCommand = command("greeting") {
            requires { source -> source.sender.isOp }

            arguments {
                "float" to FloatArgumentType.floatArg()
                union {
                    "test1" to BoolArgumentType.bool()
                    "test1" to ArgumentTypes.hexColor()
                    "test1" to IntegerArgumentType.integer()
                }
                "message" to {
                    StringArgumentType.word()
                }
            }

            executes { source ->
                println("float: ${"float" to Float::class}")

                println("test1: ${"test1" nullOr Boolean::class}")
                println("test2: ${"test2" nullOr TextColor::class}")
                println("test3: ${"test3" nullOr Int::class}")

                println("message: ${"message" to String::class}")

                0
            }

            then("pplayer") {
                arguments {
                    "player" to ArgumentTypes.player()
                    "message" to StringArgumentType.word()
                }

                executes { source ->
                    val playerResolver = "player" to PlayerSelectorArgumentResolver::class
                    val player = playerResolver.resolve(source).first()
                    val message = "message" to String::class

                    player.sendMessage(message)

                    0
                }
            }
        }

        CommandRegistrar.register(greetingCommand)
//        CommandRegistrar.register(ExampleCommand())
    }

    override fun onDisable() {
        // Plugin shutdown logic
    }
}