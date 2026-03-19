# ************************************************************************* #
#                                                                           #
#                                                      :::      ::::::::    #
#  maze_generator.py                                 :+:      :+:    :+:    #
#                                                  +:+ +:+         +:+      #
#  By: cel-hajj <cel-hajj@student.s19.be>        +#+  +:+       +#+         #
#                                              +#+#+#+#+#+   +#+            #
#  Created: 2026/03/10 23:49:39 by cel-hajj        #+#    #+#               #
#  Updated: 2026/03/19 08:34:51 by cel-hajj        ###   ########.fr        #
#                                                                           #
# ************************************************************************* #

"""
Module for generating, solving, and exporting procedural mazes.
It supports both Kruskal's and Depth-First Search (DFS) algorithms,
handling both perfect and regular maze topologies.
"""
import random
import heapq
from typing import Any, Dict, List, Tuple, Union, Set
from enum import Enum


class MazeGenerator:
    """
    Main class responsible for holding the maze grid state, applying generation
    algorithms, calculating the shortest path, and exporting the results.
    """
    Direction = Enum(
        'Direction',
        [('UP', 1), ('DOWN', 2), ('RIGHT', 3), ('LEFT', 4)]
    )

    class DSU:
        """
        Disjoint Set Union (Union-Find) data structure used primarily
        to track connected components in Kruskal's algorithm.
        """
        def __init__(self, n: int) -> None:
            """
            Initializes the DSU structure with `n` isolated elements.

            Args:
                n (int): The total number of elements (cells in the maze).

            Returns:
                None
            """
            self.parent = [i for i in range(n)]
            self.rank = [1 for i in range(n)]

        def find(self, child: int) -> int:
            """
            Finds the root parent of a given element, applying path
            compression.

            Args:
                child (int): The index of the element to find.

            Returns:
                int: The root parent index of the element.
            """
            if self.parent[child] != child:
                self.parent[child] = self.find(self.parent[child])
            return self.parent[child]

        def union(self, i: int, j: int) -> bool:
            """
            Unites the sets containing elements i and j using union by rank.

            Args:
                i (int): The first element to unite.
                j (int): The second element to unite.

            Returns:
                bool: True if a union was performed, False if they were
                already in the same set.
            """
            root_1 = self.find(i)
            root_2 = self.find(j)
            if root_1 != root_2:
                if self.rank[root_1] > self.rank[root_2]:
                    self.parent[root_2] = root_1
                elif self.rank[root_1] < self.rank[root_2]:
                    self.parent[root_1] = root_2
                else:
                    self.parent[root_1] = root_2
                    self.rank[root_2] += 1
                return True
            return False

    def __init__(self,
                 width: int,
                 height: int,
                 entry_point: Tuple[int, int],
                 exit_point: Tuple[int, int],
                 maze_type: str,
                 output_filename: str,
                 seed: int = 42,
                 algorithm: str = "Kruskal") -> None:
        """
        Initializes the MazeGenerator with configuration parameters and sets
        up initial grid states.

        Args:
            width (int): The width of the maze in cells.
            height (int): The height of the maze in cells.
            seed (int): The seed for the random number generator.
            cell_size (int): The visual size of the cell
            (used by the renderer).
            entry_point (Tuple[int, int]): The (x, y) coordinates for the maze
            entrance.
            exit_point (Tuple[int, int]): The (x, y) coordinates for the maze
            exit.
            algorithm (str): The algorithm to use
            ('Kruskal' or 'Backtracking').
            maze_type (str): The type of maze to generate
            ('perfect' or 'regular').
            output_filename (str): The name of the file to save the final maze
            representation.

        Returns:
            None
        """
        self.check_arguments({
            "WIDTH": width,
            "HEIGHT": height,
            "ENTRY": entry_point,
            "EXIT": exit_point,
            "OUTPUT_FILE": output_filename,
            "PERFECT": maze_type,
            "SEED": seed,
            "ALGORITHM": algorithm
        })
        self.width = width
        self.height = height
        self.entry_point = entry_point
        self.exit_point = exit_point
        self.algorithm = algorithm
        self.maze_type = maze_type
        self.output_filename = output_filename
        self._rng = random.Random(seed)
        self.walls: List[Tuple[int, int]] = []
        self.maze_walls: List[Tuple[int, int]] = []
        self.pattern_walls: List[Tuple[int, int]] = []
        self.pattern_cells: Set[int] = set()
        self.walls_to_remove: Set[Tuple[int, int]] = set()
        self.matrix_cells: Union[List[List[List[int]]], None] = None
        self.shortest_path: Union[List[int], None] = None
        self.set_four_cells()
        self.set_two_cells()
        self.fill_walls()

    def check_arguments(self, extracted_data: Dict[str, Any]) -> None:
        """
        Verify that the arguments have valid types and values.

        Args:
            extracted_data (Dict[str, Any]): Contains maze parameters
            as keys and their values.

        Returns:
            None
        """
        data_requirements: Dict[str, List[Any]] = {
            "WIDTH": [lambda v: 9 <= int(v) <= 200],
            "HEIGHT": [lambda v: 7 <= int(v) <= 200],
            "ENTRY": [lambda v: v[0] >= 0 and v[1] >= 0 and
                      isinstance(v, tuple)],
            "EXIT": [lambda v: v[0] >= 0 and v[1] >= 0 and
                     isinstance(v, tuple)],
            "OUTPUT_FILE": [lambda v: len(v.strip()) > 0],
            "PERFECT": [lambda v: v == "regular" or v == "perfect"],
            "SEED": [lambda v: 0 <= int(v) <= 200],
            "ALGORITHM": [lambda v: v == "Kruskal" or v == "Backtracking"]
        }
        validation_conditions = {
            "WIDTH": "Integer between 9 and 200 (inclusive)",
            "HEIGHT": "Integer between 7 and 200 (inclusive)",
            "ENTRY": "Two non-negative integers in a tuple, e.g., (0,5)",
            "EXIT": "Two non-negative integers in a tuple, e.g., (2,19)",
            "OUTPUT_FILE": "Non-empty string specifying the output file \
name",
            "PERFECT": "Should be: 'perfect' or 'regular'",
            "SEED": "Integer between 0 and 200 (inclusive)",
            "ALGORITHM": "Either 'Kruskal' or 'Backtracking"
        }
        keys = list(extracted_data.keys())
        results: List[Any] = []
        try:
            for i in range(len(keys)):
                results.append(
                    data_requirements[keys[i]][0](extracted_data[keys[i]])
                )
        except ValueError:
            raise ValueError(validation_conditions[keys[i]])
        for i in range(len(results)):
            if not results[i]:
                raise ValueError(validation_conditions[keys[i]])

        if extracted_data["ENTRY"] == extracted_data["EXIT"]:
            raise ValueError("the ENTRY coordinates are identical to the \
EXIT coordinates. ENTRY and EXIT must be distinct.")
        elif (extracted_data["ENTRY"][0] >= extracted_data["WIDTH"] or
                extracted_data["ENTRY"][1] >= extracted_data["HEIGHT"]):
            raise ValueError("The ENTRY coordinates are outside the \
allowed grid boundaries. Both ENTRY x and y must be less than WIDTH and \
HEIGHT respectively.")
        elif (extracted_data["EXIT"][0] >= extracted_data["WIDTH"] or
                extracted_data["EXIT"][1] >= extracted_data["HEIGHT"]):
            raise ValueError("The EXIT coordinates are outside the \
allowed grid boundaries. Both EXIT x and y must be less than WIDTH and \
HEIGHT respectively.")

        w = extracted_data["WIDTH"]
        h = extracted_data["HEIGHT"]
        left_cells_4 = (w - 7) // 2
        top_cells = (h - 5) // 2
        left_cells_2 = (w - 7) // 2 + 4

        pattern_coords: Set[Tuple[int, int]] = set()

        for i in range(5):
            if i == 2:
                pattern_coords.add((left_cells_4, top_cells + i))
                pattern_coords.add((left_cells_4 + 1, top_cells + i))
                pattern_coords.add((left_cells_4 + 2, top_cells + i))
            elif i > 2:
                pattern_coords.add((left_cells_4 + 2, top_cells + i))
            else:
                pattern_coords.add((left_cells_4, top_cells + i))

        for i in range(5):
            if i == 1:
                pattern_coords.add((left_cells_2 + 2, top_cells + i))
            elif i == 3:
                pattern_coords.add((left_cells_2, top_cells + i))
            else:
                pattern_coords.add((left_cells_2, top_cells + i))
                pattern_coords.add((left_cells_2 + 1, top_cells + i))
                pattern_coords.add((left_cells_2 + 2, top_cells + i))

        if extracted_data["ENTRY"] in pattern_coords:
            raise ValueError("The ENTRY coordinates cannot be spawned \
inside the '42' pattern walls.")
        if extracted_data["EXIT"] in pattern_coords:
            raise ValueError("The EXIT coordinates cannot be spawned \
inside the '42' pattern walls.")

    def set_four_cells(self) -> None:
        """
        Calculates and stores the cell indices corresponding to the '4'
        in the mandatory '42' pattern integrated into the maze.

        Args:
            None

        Returns:
            None
        """
        w = self.width
        h = self.height
        left_cells = (w - 7) // 2
        top_cells = (h - 5) // 2
        pattern_cells = self.pattern_cells
        for i in range(5):
            if i == 2:
                pattern_cells.add((top_cells + i) * w + left_cells)
                pattern_cells.add((top_cells + i) * w + left_cells + 1)
                pattern_cells.add((top_cells + i) * w + left_cells + 2)
            elif i > 2:
                pattern_cells.add((top_cells + i) * w + left_cells + 2)
            else:
                pattern_cells.add((top_cells + i) * w + left_cells)

    def set_two_cells(self) -> None:
        """
        Calculates and stores the cell indices corresponding to the '2'
        in the mandatory '42' pattern integrated into the maze.

        Args:
            None

        Returns:
            None
        """
        w = self.width
        h = self.height
        left_cells = (w - 7) // 2 + 4
        top_cells = (h - 5) // 2
        pattern_cells = self.pattern_cells
        for i in range(5):
            if i == 1:
                pattern_cells.add((top_cells + i) * w + left_cells + 2)
            elif i == 3:
                pattern_cells.add((top_cells + i) * w + left_cells)
            else:
                pattern_cells.add((top_cells + i) * w + left_cells)
                pattern_cells.add((top_cells + i) * w + left_cells + 1)
                pattern_cells.add((top_cells + i) * w + left_cells + 2)

    def fill_walls(self) -> None:
        """
        Populates the initial wall grid, linking adjacent cells and isolating
        the '42' pattern walls from standard maze generation walls.

        Args:
            None

        Returns:
            None
        """
        w = self.width
        h = self.height
        walls = self.walls
        pattern_cells = self.pattern_cells
        pattern_walls = self.pattern_walls
        for y in range(h):
            for x in range(w):
                index = y * w + x
                if x < w - 1:
                    if index in pattern_cells or index + 1 in pattern_cells:
                        pattern_walls.append((index, index + 1))
                    else:
                        walls.append((index, index + 1))
                if y < h - 1:
                    if index in pattern_cells or index + w in pattern_cells:
                        pattern_walls.append((index, index + w))
                    else:
                        walls.append((index, index + w))

    def kruskal_fill_matrix_cells(self) -> None:
        """
        Converts the retained walls from Kruskal's algorithm into a 3D matrix
        representing the bounding boxes (Top, Right, Bottom, Left) of each
        cell.

        Args:
            None

        Returns:
            None
        """
        h = self.height
        w = self.width
        self.matrix_cells = [[[0, 0, 0, 0] for _ in range(w)]
                             for _ in range(h)]
        mat = self.matrix_cells
        walls = self.maze_walls + self.pattern_walls
        for l1, l2 in zip(mat[0], mat[h - 1]):
            l1[0] = 1
            l2[2] = 1
        for row in mat:
            row[0][3] = 1
            row[w - 1][1] = 1
        for wall in walls:
            x1 = wall[0] % w
            y1 = wall[0] // w
            x2 = wall[1] % w
            y2 = wall[1] // w
            if wall[1] - wall[0] == 1:
                mat[y1][x1][1] = 1
                mat[y2][x2][3] = 1
            elif wall[1] - wall[0] == w:
                mat[y1][x1][2] = 1
                mat[y2][x2][0] = 1

    def dfs_fill_matrix_cells(self) -> None:
        """
        Converts the remaining walls from the DFS algorithm into a 3D matrix
        representing the bounding boxes (Top, Right, Bottom, Left) of each
        cell.

        Args:
            None

        Returns:
            None
        """
        h = self.height
        w = self.width
        self.matrix_cells = [[[0, 0, 0, 0] for _ in range(w)]
                             for _ in range(h)]
        mat = self.matrix_cells
        for l1, l2 in zip(mat[0], mat[h - 1]):
            l1[0] = 1
            l2[2] = 1
        for row in mat:
            row[0][3] = 1
            row[w - 1][1] = 1
        walls = self.walls + self.pattern_walls
        for wall in walls:
            if wall not in self.walls_to_remove:
                x1 = wall[0] % w
                y1 = wall[0] // w
                x2 = wall[1] % w
                y2 = wall[1] // w
                if wall[1] - wall[0] == 1:
                    mat[y1][x1][1] = 1
                    mat[y2][x2][3] = 1
                elif wall[1] - wall[0] == w:
                    mat[y1][x1][2] = 1
                    mat[y2][x2][0] = 1

    def get_neighbors(self, cur: int) -> List[Tuple[int, Any]]:
        """
        Retrieves valid grid neighbors for a cell that are within maze
        boundaries.

        Args:
            cur (int): The 1D index of the current cell.

        Returns:
            List[Tuple[int, Any]]: A list of tuples containing the neighbor's
                                   1D index and relative Direction.
        """
        h = self.height
        w = self.width
        i = cur // w
        j = cur % w
        to_visit: List[Tuple[int, Any]] = []
        if i > 0:
            up = w * (i - 1) + j
            to_visit.append((up, self.Direction.UP))
        if i < h - 1:
            bottom = w * (i + 1) + j
            to_visit.append((bottom, self.Direction.DOWN))
        if j > 0:
            left = w * i + j - 1
            to_visit.append((left, self.Direction.LEFT))
        if j < w - 1:
            right = w * i + j + 1
            to_visit.append((right, self.Direction.RIGHT))
        return to_visit

    def add_to_walls_to_remove(self, cur: int, cell: int,
                               direction: Direction) -> None:
        """
        Registers a specific wall connecting two cells to be destroyed.

        Args:
            cur (int): The 1D index of the current cell.
            cell (int): The 1D index of the adjacent cell.
            direction (Direction): The direction from `cur` to `cell`.

        Returns:
            None
        """
        match direction:
            case self.Direction.UP:
                self.walls_to_remove.add((cell, cur))
            case self.Direction.DOWN:
                self.walls_to_remove.add((cur, cell))
            case self.Direction.LEFT:
                self.walls_to_remove.add((cell, cur))
            case self.Direction.RIGHT:
                self.walls_to_remove.add((cur, cell))

    def kruskal_generate_perfect(self) -> None:
        """
        Generates a perfect maze (no loops, one unique path between any two
        points) using a randomized Kruskal's algorithm and Disjoint Set Union.

        Args:
            None

        Returns:
            None
        """
        self._rng.shuffle(self.walls)
        dsu = self.DSU(self.height * self.width)
        maze_walls = self.maze_walls
        maze_walls.clear()
        for wall in self.walls:
            cell1, cell2 = wall
            if dsu.find(cell1) != dsu.find(cell2):
                dsu.union(cell1, cell2)
            else:
                maze_walls.append(wall)

    def kruskal_generate_regular(self) -> None:
        """
        Generates a regular maze (contains loops and multiple paths)
        using Kruskal's algorithm by randomly omitting some wall bounds.

        Args:
            None

        Returns:
            None
        """
        self._rng.shuffle(self.walls)
        dsu = self.DSU(self.height * self.width)
        maze_walls = self.maze_walls
        maze_walls.clear()
        for wall in self.walls:
            cell1, cell2 = wall
            if dsu.find(cell1) != dsu.find(cell2):
                dsu.union(cell1, cell2)
            else:
                if self._rng.random() < 0.05:
                    pass
                else:
                    maze_walls.append(wall)

    def dfs_generate_perfect(self) -> None:
        """
        Generates a perfect maze using a recursive Depth-First Search
        (Backtracking) algorithm.

        Args:
            None

        Returns:
            None
        """
        def helper(cur: int, visited: Set[int]) -> None:
            """
            Recursive helper function traversing unvisited cells to carve
            paths.

            Args:
                cur (int): The 1D index of the current cell.
                visited (Set[int]): A set tracking already processed cells.

            Returns:
                None
            """
            neighbors = self.get_neighbors(cur)
            self._rng.shuffle(neighbors)
            for cell, direction in neighbors:
                if cell not in visited:
                    self.add_to_walls_to_remove(cur, cell, direction)
                    visited.add(cell)
                    helper(cell, visited)
        start = self.entry_point[1] * self.width + self.entry_point[0]
        visited = set()
        for cell in self.pattern_cells:
            visited.add(cell)
        helper(start, visited)

    def dfs_generate_regular(self) -> None:
        """
        Generates a regular maze (with loops) using DFS by randomly breaking
        down extra walls post-generation.

        Args:
            None

        Returns:
            None
        """
        self.dfs_generate_perfect()
        for wall in self.walls:
            if wall not in self.walls_to_remove and self._rng.random() < 0.05:
                self.walls_to_remove.add(wall)

    def solve_maze(self) -> None:
        """
        Solves the generated maze finding the absolute shortest path from entry
        to exit using Dijkstra's algorithm. Populates the `shortest_path`
        attribute.

        Args:
            None

        Returns:
            None
        """
        if self.matrix_cells is None:
            return
        matrix_cells = self.matrix_cells
        width = self.width
        height = self.height
        start = self.entry_point[1] * width + self.entry_point[0]
        end = self.exit_point[1] * width + self.exit_point[0]

        def get_available_neighbor(node: int) -> List[int]:
            """
            Checks the matrix bounds to find neighbors accessible without
            walls.

            Args:
                node (int): The 1D index of the current cell.

            Returns:
                List[int]: A list of reachable 1D cell indices.
            """
            j = node // width
            i = node % width
            neighbor = []
            if matrix_cells[j][i][0] == 0:
                neighbor.append(width * (j - 1) + i)
            if matrix_cells[j][i][1] == 0:
                neighbor.append(width * j + i + 1)
            if matrix_cells[j][i][2] == 0:
                neighbor.append(width * (j + 1) + i)
            if matrix_cells[j][i][3] == 0:
                neighbor.append(width * j + i - 1)
            return neighbor

        def dijkstra() -> Union[List[int], None]:
            """
            Executes Dijkstra's algorithm to navigate through the matrix and
            backtrack the shortest path.

            Args:
                None

            Returns:
                Union[List[int], None]: An ordered list of 1D node indices
                from entry to exit, or None if no path exists.
            """
            distance = [float('inf')] * (width * height)
            distance[start] = 0
            parent: Dict[Any, Any] = {start: None}
            pq = [(0, start)]
            while pq:
                cur_dist, cur_ver = heapq.heappop(pq)
                if cur_ver == end:
                    path: List[Any] = []
                    while cur_ver is not None:
                        path.append(cur_ver)
                        cur_ver = parent[cur_ver]
                    return path[::-1]
                if cur_dist != distance[cur_ver]:
                    continue
                neighbor_list = get_available_neighbor(cur_ver)
                for neighbor in neighbor_list:
                    dist = cur_dist + 1
                    if dist < distance[neighbor]:
                        parent[neighbor] = cur_ver
                        distance[neighbor] = dist
                        heapq.heappush(pq, (dist, neighbor))
            return None
        self.shortest_path = dijkstra()

    def generate_output_file(self) -> None:
        """
        Parses the cell matrix into a hexadecimal bitmask layout and writes the
        maze layout, entry/exit coordinates, and path directions to the output
        file.

        Args:
            None

        Returns:
            None
        """
        if self.matrix_cells is None or self.shortest_path is None:
            return
        mat = self.matrix_cells
        shortest_path = self.shortest_path
        try:
            with open(self.output_filename, "w", encoding="utf-8") as file:
                for y in range(self.height):
                    hex_seq = ""
                    for x in range(self.width):
                        val = (mat[y][x][0] + mat[y][x][1] * 2 +
                               mat[y][x][2] * 4 + mat[y][x][3] * 8)
                        hex_seq += f"{val:X}"
                    hex_seq += "\n"
                    file.write(hex_seq)
                file.write("\n")
                file.write(f"{self.entry_point[0]},{self.entry_point[1]}\n")
                file.write(f"{self.exit_point[0]},{self.exit_point[1]}\n")
                direction = ""
                for i in range(len(shortest_path) - 1):
                    if shortest_path[i + 1] - shortest_path[i] == self.width:
                        direction += "S"
                    if shortest_path[i + 1] - shortest_path[i] == -self.width:
                        direction += "N"
                    if shortest_path[i + 1] - shortest_path[i] == 1:
                        direction += "E"
                    if shortest_path[i + 1] - shortest_path[i] == -1:
                        direction += "W"
                direction += "\n"
                file.write(direction)
        except (FileNotFoundError, PermissionError, FileExistsError) as e:
            print("Something went wrong: ", e)

    def generate(self) -> None:
        """
        The master entry point to generate the maze layout, solve the shortest
        path, dump data to the output file, and clean up temporary generation
        memory.

        Args:
            None

        Returns:
            None
        """
        if self.algorithm == 'Backtracking':
            if self.maze_type == 'perfect':
                self.dfs_generate_perfect()
            else:
                self.dfs_generate_regular()
            self.dfs_fill_matrix_cells()
        else:
            if self.maze_type == 'perfect':
                self.kruskal_generate_perfect()
            else:
                self.kruskal_generate_regular()
            self.kruskal_fill_matrix_cells()
        self.solve_maze()
        self.generate_output_file()

        self.maze_walls.clear()
        self.walls_to_remove.clear()
