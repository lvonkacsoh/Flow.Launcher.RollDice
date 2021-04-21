# encoding=utf8
import re

from typing import List
from flowlauncher import FlowLauncher
from dice_rolling import RollBuilder


class RollDice(FlowLauncher):
    ICON_PATH = "assets\\icon.jpg"
    KEY_DICE = "d"
    PATTERN_DICE = r'[0-9]{1,}d[0-9]{1,}'
    PATTERN_RAW_COMMAND = r'([0-9]{1,}d[0-9]{1,}|[0-9]{1,})( [\+|\-\*\/] ([0-9]{1,}d[0-9]{1,}|[0-9]{1,}))*'

    regex_is_valid_input = re.compile(PATTERN_RAW_COMMAND)
    regex_dices = re.compile(PATTERN_DICE)
    query_results = []

    def add_message(self, text: str, subtext: str = None):
        self.query_results.append({
            "Title": text,
            "SubTitle": subtext,
            "IcoPath": self.ICON_PATH,
        })

    # part of the FlowLauncher lifecycle, 'key' is a single string of whatever you type after "roll "
    def query(self, raw_arguments: str) -> List[dict]:
        if len(raw_arguments) == 0:
            return self.add_message("Maybe enter something, dingus..", "")

        if not self.is_valid_input(raw_arguments):
            self.add_message("ERROR: Invalid pattern",
                             "Note: Try something like 'roll 1d20 + 3d6 * 2'")
            return self.query_results

        rolls = self.regex_dices.findall(raw_arguments)
        resultMap = {roll: self.roll_dice(roll) for roll in rolls}

        to_eval = raw_arguments
        for roll in resultMap:
            result_list = resultMap[roll]
            result_sum = sum(result_list)
            to_eval = to_eval.replace(roll, str(result_sum))

        total_result = str(eval(to_eval))
        self.add_message("Result: {}".format(total_result))

        for roll in resultMap:
            self.add_message("{} evaluated to {}".format(
                roll, resultMap[roll]))

        return self.query_results

    def is_valid_input(self, input: str) -> bool:
        return bool(self.regex_is_valid_input.fullmatch(input))

    def roll_dice(self, dice: str) -> List[int]:
        args = dice.split(self.KEY_DICE)
        builder = RollBuilder()
        builder.set_amount_of_dice(int(args[0]))
        builder.set_number_of_sides(int(args[1]))
        builder.build()
        return builder.get_result()
