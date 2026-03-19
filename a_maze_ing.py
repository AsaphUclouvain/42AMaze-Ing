#!/usr/bin/env python3

# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  a_maze_ing.py                                     :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: cel-hajj <cel-hajj@student.s19.be>        +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/03/02 07:38:57 by cel-hajj        #+#    #+#               #
#  Updated: 2026/03/13 18:02:06 by cel-hajj        ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

"""
Main entry point for the A-Maze-ing application. It coordinates parsing the
configuration file, initializing the maze generation engine, and launching
the graphical display loop.

Running Instruction:

To run this script, you have three options:

1. Install the dependencies and run the script:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install mazegen-1.0.0-py3-none-any.whl
python3 a_maze_ing.py config.txt

2. Use the rule provided in the Makefile:
make run

3. Run using the local source library:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt;
python3 a_maze_ing.py config.txt

"""
import sys
from parsing.parse_config import parse_config
from mazegen.maze_generator import MazeGenerator
from display import MazeDisplay


def main() -> None:
    """
    Executes the main routine of the application. Extracts data from the
    configuration file via command-line arguments, instantiates the maze,
    triggers the generation process, and starts the MLX renderer.

    Returns:
        None: This function does not return a value.
    """
    sys.setrecursionlimit(40000)
    config_data = parse_config(len(sys.argv), sys.argv)
    if isinstance(config_data, dict):
        maze = MazeGenerator(width=config_data["WIDTH"],
                             height=config_data["HEIGHT"],
                             seed=config_data["SEED"],
                             entry_point=config_data["ENTRY"],
                             exit_point=config_data["EXIT"],
                             algorithm=config_data["ALGORITHM"],
                             maze_type=("perfect" if config_data["PERFECT"]
                                        else "regular"),
                             output_filename=config_data["OUTPUT_FILE"])
        maze.generate()
        display = MazeDisplay(maze)
        display.run()


if __name__ == "__main__":
    main()
