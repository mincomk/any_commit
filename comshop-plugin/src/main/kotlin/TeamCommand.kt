import com.github.ityeri.comshop.dsl.command
import com.mojang.brigadier.arguments.StringArgumentType
import io.papermc.paper.command.brigadier.argument.ArgumentTypes
import io.papermc.paper.command.brigadier.argument.resolvers.selector.PlayerSelectorArgumentResolver
import net.kyori.adventure.text.Component
import net.kyori.adventure.text.format.TextColor
import org.bukkit.entity.Player

val teamCommand = command("myteam") {
    requires { source -> source.sender.isOp }

    then("new") {
        arguments {
            "name" to StringArgumentType.word()
            "color" to ArgumentTypes.hexColor()
        }

        executes { source, sender ->
            val teamName = "name" to String::class

            if (teamName !in teams) {
                teams.put(
                    "name" to String::class,
                    Team("name" to String::class, "color" to TextColor::class)
                )
            } else {
                sender.sendMessage("Team \"$teamName\" is already exists")
            }
        }
    }

    then("add") {
        arguments {
            "name" to StringArgumentType.word()
            "player" to ArgumentTypes.player()
        }

        executes { source, sender ->
            val teamName = "name" to String::class
            val team = teams[teamName]

            if (team != null) {
                team.members.add(
                    "player" to PlayerSelectorArgumentResolver::class resolveFirst source
                )
            } else {
                sender.sendMessage("Team \"$teamName\" not found")
            }
        }
    }

    executes { source, sender ->
        sender.sendMessage("There are ${teams.size} teams:")

        teams.values.forEach { team ->
            sender.sendMessage(
                Component.text(" |  ")
                    .append(Component.text(team.name, team.color))
            )
        }
    }
}

val teams: MutableMap<String, Team> = mutableMapOf()

class Team(val name: String, val color: TextColor) {
    val members: MutableList<Player> = mutableListOf()
}