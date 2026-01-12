import com.github.ityeri.comshop.CommandRegistrar
import com.github.ityeri.comshop.dsl.command
import com.mojang.brigadier.arguments.BoolArgumentType
import com.mojang.brigadier.arguments.FloatArgumentType
import com.mojang.brigadier.arguments.IntegerArgumentType
import com.mojang.brigadier.arguments.StringArgumentType
import io.papermc.paper.command.brigadier.argument.ArgumentTypes
import io.papermc.paper.command.brigadier.argument.resolvers.FinePositionResolver
import io.papermc.paper.command.brigadier.argument.resolvers.selector.EntitySelectorArgumentResolver
import io.papermc.paper.command.brigadier.argument.resolvers.selector.PlayerSelectorArgumentResolver
import org.bukkit.entity.Player
import org.bukkit.plugin.java.JavaPlugin


class ComshopPlugin : JavaPlugin() {

    override fun onEnable() {
        CommandRegistrar.lifecycleRegister(this)


        val greetingCommand = command("greeting") {
            requires { source -> source.sender is Player }

            arguments {
                "player" to ArgumentTypes.player()
                "message" to StringArgumentType.greedyString()
            }

            executes { source, sender ->
                val senderPlayer = sender as Player
                // Paper API 가 제공하는 player 인자 파서는 Player 대신 PlayerSelectorArgumentResolver 를 던집니다
                // ArgumentResolver 또는 SelectorArgumentResolver 로부턴
                // resolve, resolveFirst 라는 접미사를 사용하여 값을 뽑아낼수 있습니다
                val receiverPlayer = "player" to PlayerSelectorArgumentResolver::class resolveFirst source

                // String 에 대한 확장 접미사인 to 를 통해 인자 이름으로  인자 값을 가져올수 있습니다
                // "message" 인자가 Int 타입이라면 "message" to Int::class 형태입니다
                val message = "message" to String::class

                receiverPlayer.sendMessage(message)
                senderPlayer.sendMessage("Greeting is sent successfully")
            }
        }


        val typeCheckingCommand = command("typeof") {
            arguments {
                union {
                    // 파싱 순서는 코드에 쓰여진 순서를 따릅니다
                    // 예컨대, 만약 string 인자가 bool 보다 앞에 있으면,
                    // string 이 단어인 "false", "true" 을 먼저 파싱해 버리기에
                    // 그 뒤쪽의 bool 인자는 파싱될수 없습니다
                    "int" to IntegerArgumentType.integer()
                    "bool" to BoolArgumentType.bool()
                    "string" to StringArgumentType.word()
                    "float" to FloatArgumentType.floatArg()
                    "entity" to ArgumentTypes.entity()
                    "coordinate" to ArgumentTypes.finePosition()
                }
            }

            executes { source, sender ->
                // union 의 경우 인자중 하나만이 최종적으로 값이 넘어 오기에
                // 나머지는 존재하지 않는 인자로 취급되어 to 를 사용하면 에러를 반환합니다
                // nullOr 은 to 와 같은 기능이지만 존재하지 않는 인자에 대해선 null 을 반환합니다
                val intValue = "int" nullOr Int::class
                val boolValue = "bool" nullOr Boolean::class
                val stringValue = "string" nullOr String::class
                val floatValue = "float" nullOr Float::class
                val entity = ("entity" nullOr EntitySelectorArgumentResolver::class)
                    ?.let { it resolveFirst source }
                val coordinate = ("coordinate" nullOr FinePositionResolver::class)
                    ?.let { it resolve source }

                if (intValue != null) {
                    sender.sendMessage("type is int: $intValue")
                } else if (boolValue != null) {
                    sender.sendMessage("type is bool: $boolValue")
                } else if (stringValue != null) {
                    sender.sendMessage("type is string: $stringValue")
                } else if (floatValue != null) {
                    sender.sendMessage("type is float: $floatValue")
                } else if (entity != null) {
                    sender.sendMessage("type is entity: $entity")
                } else if (coordinate != null) {
                    sender.sendMessage("type is coordinate: $coordinate")
                }
            }
        }


        CommandRegistrar.register(greetingCommand)
        CommandRegistrar.register(typeCheckingCommand)
        CommandRegistrar.register(teamCommand)
    }

    override fun onDisable() {
        // Plugin shutdown logic
    }
}