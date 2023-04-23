# RollDice (Flow.Launcher.Plugin.RollDice)

A quick way to roll some dices.

![screenshot](assets/RollDice_screenshot.jpg)

## About

Rolls the given dices, sums the results and evaluates the equation.
The details of each roll are listed below the result.

In update pre-2.0 I added some fun messages based on the linux fortune package because I felt like it.

## Requirements

To use Python Plugins within Flow you'll need Python 3.10 or later installed on your system.
You also may need to select your Python installation directory in the Flow Launcher Settings.
As of v1.8, Flow Launcher should take care of the installation of Python for you if it is not on your system.

## Installing

The Plugin has been officially added to the supported list of plugins.
Use `pm install RollDice` to install.

However you can also manually add it.

### Manual

Add the plugins folder to %APPDATA%\Roaming\FlowLauncher\Plugins\ and run the Flow command `restart Flow Launcher`.

#### Python Package Requirements

This plugin depends on the python `flowlauncher` and `dice-rolling` packages.

> Without these packages installed in your python environment the plugin won't work!

The easiest way to install them, is to open a CLI like Powershell, navigate into the plugins folder and run the following command:

`pip install -r requirements.txt`

## Usage

As of version pre-2.0 you can do stuff like this:`6x4d6kh3 + 5`.
I highly recommend to check this awesome package out: [dice-rolling](https://github.com/Ajordat/dice_rolling).

| Command |Example | Description |
| --- | --- | --- |
| `roll {dices}` | `roll 1d20` | Rolls an amount of dices with the given sides and sums up the result |
| `roll {repititions}x{dices}` | `roll 6x1d20` | Repeats the throw n times |
| `roll {dices}{addition}` | `roll 4d6+3` | adds three to the throw result (this is not part of my arithmetics) |
| `roll {dices}{keep}` | `roll 4d6kh3` | Keeps the highest three of four throws, see [here](https://github.com/Ajordat/dice_rolling) for more |
| `roll {repititions}x{dices}{addition}{keep}{arithmetics}` | `roll 4d6+3kh3 + 5` | Does all of the above and adds 5 to the throw |

Currently there are some jank elements to this.
For example, the arithmetics solver still has some bugs if you want to do smth like `1d4 + 4d6` or `1d4 + 5 * 3`.
I'll address this in the full 2.0 release.


## Problems, errors and feature requests

Open an issue in this repo.
