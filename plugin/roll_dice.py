# encoding=utf8
import re
import ast
import os
import operator as op
from flowlauncher import FlowLauncher
from dice_rolling.utils.argument_parser import ParsingResult
from dice_rolling import RollBuilder
from random import choice as select_randomly

hints = [
    "Roll at disadvantage with 2d20kl1",
    "Combine dice with arithmetics 1d20 * 4",
    "Creating a new char? Try 6x4d6kh3",
    "The most complex one: 6x4d6+2kh3",
    "In D&D your attr. bonus is half of your attr score floored.",
    "This update didn't hurt any unicorns. Promise.",
    "Stay hydrated!",
    "Give your close ones a call once in a while",
    "Be the guy your 5y/o would look up to!",
    "Do you like prime numbers? You should! >:O",
    "System going down in 60 seconds ... jk :D",
]

# mostly from https://github.com/radareorg/radare2/blob/master/doc/fortunes.fun slightly modified
fortunes = [
    "You can't sleep now there are monsters nearby",
    "Every journey begins with a choice",
    "pneumonic",
    "Click below to prove you are not a bot",
    "Sorry, not sorry.",
    "fix it or set the machine on fire",
    "burn it before the bug spreads to other installations",
    "The signals are strong tonight",
    "It's dangerous to go alone, take this.",
    "Watch until the end!",
    "Don't forget to subscribe!",
    "Ah shit, here we go again.",
    "Checking whether this software can be played...",
    "Will it blend?",
    "Mind the trap.",
    "-. .- - .---- / -....- / ... ..- -.-. -.- ... -.-.--",
    "Disassemble?! No Disassemble Johnny No. 5!!!",
    "You crack me up!",
    "Welcome, " + os.getlogin(),
    "Search returned no hits. Did you mean 'Misassemble'?",
    "TIRED OF WAITING",
    "We fix bugs while you sleep.",
    "You find bugs while we sleep.",
    "The stripping process is not deep enough",
    "Come here, we are relatively friendly",
    "Don't wait for Travis",
    "Your problems are solved in an abandoned branch somewhere",
    "git blind --hard",
    "You need some new glasses",
    "aaaa is experimental",
    "We feed trolls",
    "Mind the tab",
    "Buy a Mac",
    "You have been designated for disassembly",
    "Coffee time!",
    "Can you challenge a perfect immortal machine?",
    "Add more blockchains to your life. lulz. don't.",
    "Congratulations! You got the segfault 1.000.000! Click [here] to win a prize!",
    "Well, it looks like it's working.",
    "There's more than one way to skin a cat",
    "git pull now",
    "git checkout hamster",
    "Noot noot",
    "This is an unregistered copy.",
    "10 reasons you want to bt on all threads - you will be shocked by number 3!",
    "This binary may contain traces of human",
    "Help subcommand will be eventually removed."
]


def filter_non_valids(text:str) -> str:
    return ''.join([char for char in text if char == ' ' or char.isalnum])


class MessageDTO:
    def __init__(self, title: str, subtitle: str = None) -> None:
        self.title = title
        self.subtitle = subtitle if subtitle is not None else select_randomly(hints + fortunes)

    def asFlowMessage(self) -> dict:
        return {
            "Title": self.title,
            "SubTitle": self.subtitle,
            "IcoPath": "assets/icon.jpg",
        }


class CustomParsingResult(ParsingResult):
    def __init__(self, request: str):
        super().__init__(request)
        self.repititions = 1
    

class DiceRequest:
    # see also: https://github.com/Ajordat/dice_rolling

    GROUP_REQUEST = 0
    GROUP_REPETITIONS = 1
    GROUP_REPETITIONS_VALUE = 2
    GROUP_N_DICE = 3
    GROUP_N_SIDES = 4
    GROUP_OPTIONAL_ADDITION_TYPE = 5
    GROUP_OPTIONAL_ADDITION_VALUE = 6
    GROUP_KEEP_COMMAND = 7
    GROUP_KEEP_MODE = 8

    def __init__(self, command: re.Match) -> None:
        self.request = self.__parse_request(command)
        self.rolls = []
        self.total_sum = 0
        self.total_kept = []
        self.total_discarded = []

        self.__execute()
    
    def __execute(self):
        r = []
        for _ in range(0,self.request.repititions):
            b = RollBuilder()
            b.set_amount_of_dice(self.request.n_dice)
            b.set_number_of_sides(self.request.n_sides)
            b.addition_to_roll(self.request.addition)
            b.keep_n(self.request.keep)
            b.build()
            
            r.append(b.get_full_result())
        self.rolls = r
        self.total_sum = sum([result[0] for result in r])
        self.total_kept = [kept for result in r for kept in result[1]]
        self.total_discarded = [discarded for result in r for discarded in result[2] if result[2]]
    
    def total_to_messageDTO(self)->MessageDTO:
        title = "{} evaluated to {}".format(self.request.full_request, self.total_sum)
        subtitle = "Results: {}".format([result[0] for result in self.rolls])
        return MessageDTO(title, subtitle)
    
    def rolls_to_messageDTO(self)->list[MessageDTO]:
        return [MessageDTO(
            title="> throw {}: {}".format(str(i+1), result[0]),
            subtitle="kept {}{}".format(result[1], ", discarded {}".format(result[2]) if len(result) > 2 else "")
            ) for i, result in enumerate(self.rolls)]


    def __parse_repititions(self, command:re.Match):
        if command.group(self.GROUP_REPETITIONS):
            return command.group(self.GROUP_REPETITIONS_VALUE)
        return 1
        
    def __parse_addition(self, command:re.Match):
        type = command.group(self.GROUP_OPTIONAL_ADDITION_TYPE)
        value = command.group(self.GROUP_OPTIONAL_ADDITION_VALUE)
        
        if not type or not value:
            return 0
        factor = 1 if type == '+' else -1
        return factor * value

    def __parse_keep(self, command:re.Match):
        keep_command = command.group(self.GROUP_KEEP_COMMAND)
        if not keep_command:
            return 0
        mode = command.group(self.GROUP_KEEP_MODE)
        value = keep_command[2:]
        return int(value) * (1 if mode == 'h' else -1)

    
    def __parse_request(self, command:re.Match) -> CustomParsingResult:
        result = CustomParsingResult(command.group(self.GROUP_REQUEST))

        result.repititions = self.__parse_repititions(command)
        result.n_dice = command.group(self.GROUP_N_DICE)
        result.n_sides = command.group(self.GROUP_N_SIDES)
        result.addition = self.__parse_addition(command)
        result.keep = self.__parse_keep(command)

        return result


class SaferEvaluator:
    # src: https://stackoverflow.com/a/9558001

    # supported operators
    operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
                ast.USub: op.neg}
    
    def eval_expr(self,expr):
        return self.eval_(ast.parse(expr, mode='eval').body)

    def eval_(self,node):
        if isinstance(node, ast.Num): # <number>
            return node.n
        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return self.operators[type(node.op)](self.eval_(node.left), self.eval_(node.right))
        elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
            return self.operators[type(node.op)](self.eval_(node.operand))
        else:
            raise TypeError(node)


class RollDice(FlowLauncher):
    messages = []

    def addMessage(self, message: MessageDTO):
        self.messages.append(message.asFlowMessage())


    def resolve_dice_commands(self, line:str):
        pattern = r'((\d+)x)?(\d*)d(\d+)(?:(\+|\-)(\d+))?(k(h|l)\d+)?'
        results = re.finditer(pattern, line, re.IGNORECASE)
        return  [DiceRequest(match) for match in results]


    def query(self, arguments: str) -> list:
        args = filter_non_valids(arguments.strip())

        if len(args) == 0:
            return

        try:
            rolls = self.resolve_dice_commands(args)
            for roll in rolls:
                args = args.replace(roll.request.full_request, str(roll.total_sum))
                self.addMessage(roll.total_to_messageDTO())

                # TODO: i can imagine this to be annoying, maybe add a menu with an option to turn this off
                [self.addMessage(message) for message in roll.rolls_to_messageDTO() if len(roll.rolls) > 1]

                evaluator = SaferEvaluator()
                total_result = evaluator.eval_expr(args)
                self.messages.insert(0, MessageDTO("Total result: {}".format(total_result)).asFlowMessage())
        except ValueError:
            title = "Error: ?"
            subtitle = select_randomly(hints)
            self.addMessage(MessageDTO(title, subtitle))
        except TypeError:
            title = "Error: Are you sure, that your dices are alright?"
            subtitle = select_randomly(hints)
            self.addMessage(MessageDTO(title, subtitle))
        except SyntaxError:
            title = "Error: Are your arithmetics okay?"
            subtitle = select_randomly(hints)
            self.addMessage(MessageDTO(title, subtitle))
        except:
            title = "CRITICAL ERROR: please open a GitHub issue!"
            subtitle = "Don't forget to add the query: " + arguments 
            self.addMessage(MessageDTO(title, subtitle)) #yeah.. I could've reduced this. So what?

        return self.messages
