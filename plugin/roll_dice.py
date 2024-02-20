# encoding=utf8
import re
import ast
import operator as op
from flowlauncher import FlowLauncher
from dice_rolling.utils.argument_parser import ParsingResult
from dice_rolling import RollBuilder
from fortunes import rnd_fortune
from itertools import chain


def filter_non_valids(text: str) -> str:
    return ''.join([char for char in text if char == ' ' or char.isalnum])


class MessageDTO:
    def __init__(self, title: str, subtitle: str = None):
        self.title = title
        self.subtitle = subtitle if subtitle is not None else rnd_fortune()

    def as_flow_message(self) -> dict:
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
    GROUP_N_SIDES = 4  # also may contain F for fate die
    GROUP_OPTIONAL_ADDITION_TYPE = 5
    GROUP_OPTIONAL_ADDITION_VALUE = 6
    GROUP_KEEP_COMMAND = 7
    GROUP_KEEP_MODE = 8

    def __init__(self, command: re.Match):
        self.request = self.__parse_request(command)
        self.rolls = []
        self.total_sum = 0
        self.total_kept = []
        self.total_discarded = []

        self.__execute()

    def __execute(self):
        r = []
        for _ in range(0, self.request.repititions):
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
        self.total_discarded = [
            discarded for result in r for discarded in result[2] if result[2]]

    def total_to_messageDTO(self) -> MessageDTO:
        title = "{} evaluated to {}".format(
            self.request.full_request, self.total_sum)
        subtitle = "Results: {}".format(
            list(chain.from_iterable([result[1] for result in self.rolls])))  # list flattening
        return MessageDTO(title, subtitle)

    def rolls_to_messageDTO(self) -> list[MessageDTO]:
        return [MessageDTO(
            title="> throw {}: {}".format(str(i+1), result[0]),
            subtitle="kept {}{}".format(result[1], ", discarded {}".format(
                result[2]) if len(result) > 2 else "")
        ) for i, result in enumerate(self.rolls)]

    def __parse_repititions(self, command: re.Match):
        if command.group(self.GROUP_REPETITIONS):
            return command.group(self.GROUP_REPETITIONS_VALUE)
        return 1

    def __parse_addition(self, command: re.Match):
        type = command.group(self.GROUP_OPTIONAL_ADDITION_TYPE)
        value = command.group(self.GROUP_OPTIONAL_ADDITION_VALUE)

        if not type or not value:
            return 0
        factor = 1 if type == '+' else -1
        return factor * value

    def __parse_keep(self, command: re.Match):
        keep_command = command.group(self.GROUP_KEEP_COMMAND)
        if not keep_command:
            return 0
        mode = command.group(self.GROUP_KEEP_MODE)
        value = keep_command[2:]
        return int(value) * (1 if mode == 'h' else -1)

    def __parse_fate_roll(self, command: re.Match):
        result = CustomParsingResult(command.group(self.GROUP_REQUEST))

        result.repititions = self.__parse_repititions(command)
        result.n_dice = command.group(self.GROUP_N_DICE)
        result.keep = self.__parse_keep(command)
        # we'll treat a fate die like a 1d3-2 to act in the common fate range of [-1,0,1]
        result.n_sides = 3
        result.addition = -2

        return result

    def __parse_default_roll(self, command: re.Match):
        result = CustomParsingResult(command.group(self.GROUP_REQUEST))

        result.repititions = self.__parse_repititions(command)
        result.n_dice = command.group(self.GROUP_N_DICE)
        result.n_sides = command.group(self.GROUP_N_SIDES)
        result.addition = self.__parse_addition(command)
        result.keep = self.__parse_keep(command)

        return result

    def __parse_request(self, command: re.Match) -> CustomParsingResult:
        if command.group(self.GROUP_N_SIDES) == 'F':
            return self.__parse_fate_roll(command)
        return self.__parse_default_roll(command)


class SaferEvaluator:
    # src: https://stackoverflow.com/a/9558001

    # supported operators
    operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                 ast.Div: op.truediv}

    def eval_expr(self, expr):
        return self.eval_(ast.parse(expr, mode='eval').body)

    def eval_(self, node):
        if isinstance(node, ast.Constant):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return self.operators[type(node.op)](self.eval_(node.left), self.eval_(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return self.operators[type(node.op)](self.eval_(node.operand))
        else:
            raise TypeError(node)


class RollDice(FlowLauncher):
    messages = []

    def addMessage(self, message: MessageDTO):
        self.messages.append(message.as_flow_message())

    def resolve_dice_commands(self, line: str):
        pattern = r'((\d+)x)?(\d*)d(\d+|F)(?:(\+|\-)(\d+))?(k(h|l)\d+)?'
        # pattern_fate = r'(\d+F)'
        results = re.finditer(pattern, line, re.IGNORECASE)
        return [DiceRequest(match) for match in results]

    def resolve_query(self, arguments: str):
        args = filter_non_valids(arguments.strip())
        evaluator = SaferEvaluator()

        try:
            rolls = self.resolve_dice_commands(args)
            for roll in rolls:
                args = args.replace(
                    roll.request.full_request, str(roll.total_sum))
                self.addMessage(roll.total_to_messageDTO())

                # TODO: i can imagine this to be annoying, maybe add a menu with an option to turn this off
                [self.addMessage(message) for message in roll.rolls_to_messageDTO() if len(
                    roll.rolls) > 1]

            total_result = evaluator.eval_expr(args)
            self.messages.insert(0, MessageDTO(
                "Total result: {}".format(total_result)).as_flow_message())
        except ValueError:
            title = "Error: Are your arithmetics okay?"
            self.addMessage(MessageDTO(title))
        except TypeError:
            title = "Error: Are you sure, that your dices are alright?"
            self.addMessage(MessageDTO(title))
        except Exception:
            title = "CRITICAL ERROR: please open a GitHub issue!"
            subtitle = "Don't forget to add the query: " + arguments
            self.addMessage(MessageDTO(title, subtitle))

    def query(self, arguments: str) -> list:
        if len(arguments) == 0:
            return

        self.resolve_query(arguments)

        return self.messages
