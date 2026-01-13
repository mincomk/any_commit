# comshop

> [kommand](https://github.com/monun/kommand) 에 영감을 받아 만들어진 
> [Brigadier](https://github.com/mojang/Brigadier) 의 DSL 래퍼이자 페이퍼용 명령어 라이브러리

[Brigadier](https://github.com/mojang/Brigadier) 는 모장에서 명령어 파싱을 위해 사용하는 라이브러리이며,
[kommand](https://github.com/monun/kommand) 는 내부적으로 Brigadier 를 사용합니다.
때문에 Brigadier 와 kommand 의 명령어 정의는 구조적으로 유사합니다.

Brigadier
```java
literal("test")
    .then(argument("number", IntegerArgumentType.integer())
        .then(argument("word", StringArgumentType.word())
            .then(argument("flag", BoolArgumentType.bool())
                .executes(context -> {
                    int number = IntegerArgumentType.getInteger(context, "number");
                    String word = StringArgumentType.getString(context, "word");
                    boolean flag = BoolArgumentType.getBool(context, "flag");
                    return 0;
                })
            )
        )
    );
```

kommand
```kotlin
kommand {
    register("test") {
        then("number" to intArgument) {
            then("word" to word) {
                then("flag" to bool) {
                    executes { context ->
                        val number: Int by context
                        val word: String by context
                        val flag: Boolean by context
                    }
                }
            }
        }
    }
}
```

kommand 는 Brigadier 와 비슷하면서도 코틀린 친화적인 형태로 명령어를 정의할수 있습니다.
하지만 Brigadier 와 비슷하게, 인자가 많아지면서
코드의 들여쓰기와 길이가 크게 늘어납니다. 
또한 재귀적인 체인 형태로 명령어 노드가 이어지고 코드가 쓰여지는 kommand 와 Brigadier 의 특성상,
인자 정의부분, 실행 블록, 하위 명령어 블록을 명확하게 구분하기 어렵습니다

아래는 같은 구조의 명령어를 comshop 을 활용해 작성한 코드입니다
```kotlin
command("test") {
    arguments {
        "number" to IntegerArgumentType.integer()
        "word" to StringArgumentType.word()
        "flag" to BoolArgumentType.bool()
    }

    executes {
        val number = "number" to Int::class
        val word = "word" to String::class
        val flag = "flag" to Boolean::class
    }
}
```

코드의 들여쓰기가 줄며, 인자를 정의하는 부분과 실행블록이 명확히 구분됩니다.
하위 명령어는 then() 을 활용해 같은 형태로 정의할수 있습니다

---

* Supported Paper api versions
  * 1.21.10 - java 21

* TODO
  * 1.21.11 - java 21
  * 아마도 기타 구버전...

# dependency

comshop 은 JitPack 을 통해 배포됩니다

kotlin
```kotlin
repositories {
    maven("https://jitpack.io") {
        name = "jitpack"
    }
}

dependencies {
    implementation("com.github.ityeri:comshop:v1.0.0-beta.3")
}
```

groovy
```groovy
repositories {
    maven {
        url "https://jitpack.io"
        name = "jitpack"
    }
}

dependencies {
    implementation 'com.github.ityeri:comshop:v1.0.0-beta.3'
}
```

# usage

## DSL 로 명령어 만들어 보기

```kotlin
val greetingCommand = command("greeting") {
    // 명령어를 사용할수 있는 조건을 정의하는 부분
    requires { source -> source.sender is Player }

    // 명령어의 인자를 정의하는 부분
    arguments {
        "player" to ArgumentTypes.player()
        "message" to StringArgumentType.greedyString()
    }

    // 명령어의 실행 블럭
    executes { source, sender ->
        val senderPlayer = sender as Player
        val receiverPlayer = "player" to PlayerSelectorArgumentResolver::class resolveFirst source
        val message = "message" to String::class

        receiverPlayer.sendMessage(message)
        senderPlayer.sendMessage("Greeting is sent successfully")
    }
}
```
| 프로젝트 내부의 예제 `example-plugin/src/main/kotlin/ComshopPlugin.kt` 일부에서 발최

인게임에서:
```
/greeting player_name 안녕!
>>> 안녕!
```

## 하위 명령어 만들기

하나의 명령어가 여러개의 하위 명령어를 가지기도 합니다. 
마인크래프트의 내장 명령어인 `/team` 명령어를 예시로 들수 있습니다

```
/team add newTeam
```
```
/team join newTeam player_name
```
```
/team remove newTeam
```

트리로 그리면 이렇습니다

```
team
 |--add
 |--join
 \--remove
```

`then` 매서드를 활용하면 위와 같은 하위 명령어를 정의할수 있습니다

```kotlin
val teamCommand = command("myteam") {
    requires { source -> source.sender.isOp }

    executes { source, sender ->
        sender.sendMessage("There are ${teams.size} teams:")

        teams.values.forEach { team ->
            sender.sendMessage(
                Component.text(" |  ")
                    .append(Component.text(team.name + "\n", team.color))
                    .append(Component.text(" |   |  members: "))
                    .append(Component.text(
                        team.members.joinToString(", ") { it.name }
                    ))
            )
        }
    }

    then("new") {
        arguments {
            ...
        }

        executes {
            ...
        }
    }

    then("add") {
        arguments {
            ...
        }

        executes {
            ...
        }
    }
}
```
| 프로젝트 내부의 예제 `example-plugin/src/main/kotlin/TeamCommand.kt` 일부에서 발최

`then` 블럭은 `command` DSL 과 동일하게 작성할수 있습니다.

코드가 너무 길어진다면 이렇게 분리할수도 있습니다:

```kotlin
val newCommand = command("new") {
    arguments {
        ...
    }

    executes { 
        ...
    }
}

---

val addCommand = command("add") {
    arguments {
        ...
    }

    executes {
        ...
    }
}

---

val teamCommand = command("myteam") {
    requires { source -> source.sender.isOp }

    executes { source, sender ->
        sender.sendMessage("There are ${teams.size} teams:")

        teams.values.forEach { team ->
            sender.sendMessage(
                Component.text(" |  ")
                    .append(Component.text(team.name + "\n", team.color))
                    .append(Component.text(" |   |  members: "))
                    .append(Component.text(
                        team.members.joinToString(", ") { it.name }
                    ))
            )
        }
    }

    then(newCommand)
    then(addCommand)
}
```
| 프로젝트 내부의 예제 `example-plugin/src/main/kotlin/TeamCommand.kt` 일부에서 발최

## 명령어 등록하기

명렁어 등록을 위해선 `CommandRegistrar` 를 사용합니다.
실제로 명령어를 등록할땐, Paper API 의 라이프사이클 API 를 사용합니다

---

comshop 이 서버의 명렁어 등록 시점에 개입할수 있도록
서버의 라이프사이클 매니저에 등록합니다.

```kotlin
CommandRegistrar.lifecycleRegister(plugin) // plugin: JavaPlugin
```

---

명령어를 추가합니다. 
실제로 명령어가 서버에 추가되는 시점은
`LifecycleEvents.COMMANDS` 가 트리거 될때입니다.

```kotlin
CommandRegistrar.register(command) // command: CommandBuilder
```

> `lifecycleRegister(plugin)` 와 `register(command)` 를 호출하는 순서는 중요하지 않습니다.
> 다만 둘다 `LifecycleEvents.COMMANDS` 이전 시점엔 완료 되어 있어야 합니다

## 사용할수 있는 인수 타입들

Brigadier 의 `ArgumentType` 구현체는 모두 가능합니다. 

### Brigadier 내장

`com.mojang.brigadier.arguments` 패키지 내부.
기초적인 타입들을 파싱하기 위한 인수 타입들이 있습니다

| 이름 | 리턴 타입 | 사용처 |
|---|---|---|
| `IntegerArgumentType.integer` | `Int` | 64비트 부호있는 정수 파싱 |
| `LongArgumentType.longArg` | `Ling` | 64비트 부호있는 정수 파싱 |
| `FloatArgumentType.floatArg` | `Float` | 32비트 부동소수점 실수 파싱 |
| `DoubleArgumentType.doubleArg` | `Double` | 64비트 부동소수점 실수 파싱 |
| `StringArgumentType.word` | `String` | 띄어쓰기 없는 한 단어 파싱 |
| `StringArgumentType.string` | `String` | 띄어쓰기 가능한 끝따옴표로 묶인 문자열 파싱 |
| `StringArgumentType.greedyString` | `String` | 띄어쓰기 가능한 큰따옴표로 묶이지 않은 문자열 파싱 (보통 명령어 맨 끝 인수로 옴)
| `BoolArgumentType.bool` | `Boolean` | `true`, `false` 불리언 파싱 |

### Paper api 측 Brigadier 지원

`io.papermc.paper.command.brigadier.argument` 패키지 내부.
마인크래프트 고유 타입 파싱을 위한 인수 타입들이 다수 있습니다

페이퍼에서 제공하는 대부분의 인수 타입은 보통 그 타입을 그대로 반환하지 않고,
`...SelectorArgumentResolver` 라 하는 래퍼에 의해 래핑되어 반환됩니다.
(예컨대, `ArgumentType.player` 는 `Player` 가 아닌 
`PlayerSelectorArgumentResolver` 를 반환합니다)

paper api 에서 Brigadier 를 위해 지원하는 타입들은 
[Paper docs - Development / API / Command API / Arguments](
https://docs.papermc.io/paper/dev/command-api/arguments/minecraft/
) 에 정리되어 있습니다

# examples

전체 예제코드 내지 테스트 코드는 
라이브러리 소스코드의 `example-plugin` 모듈 내에 포함되어 있습니다

# TODO - 앞으로 추가될"수도" 있는것

* 인수 분기   
    comshop 은 아직 인수 분기를 지원하지 않습니다.

* 동적 인수   
    제대로 테스트 되지 않았습니다. 타 동적 인수 구현이 존재할순 있습니다.
    길이가 특정되지 않는 명령어의 구현 또한 불문명합니다 
    (예로, as 와 at 등을 여럿 연결할수 있는 execute 같은 명령어)

* 인수 타입 커스텀 시스템   
    현재 브리가디어는 `CustomArgumentType` 을 통해 인수 타입 커스텀을 지원하지만,
    추후 comshop 의 목적에 맞춰 자체 커스텀 인수가 추가될수 있습니다
