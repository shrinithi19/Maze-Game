import sys
import random
import pygame

# -----------------------------
# CONFIG & CONSTANTS
# -----------------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARKGRAY = (169, 169, 169)
YELLOW = (222, 178, 0)
PINK = (225, 96, 253)
BLUE = (0, 0, 255)
ORANGE = (255, 99, 71)
LIGHTORANGE = (255, 176, 56)
INTERMEDIARYORANGE = (255, 154, 0)
LIGHTBLUE = (60, 170, 255)
DARKBLUE = (0, 101, 178)
BEIGE = (178, 168, 152)

BORDER_THICKNESS = 1
CELL_SIZE = 25

MAZE_PIXELS = 600
INFO_BAR_HEIGHT = 80
SCREEN_WIDTH = MAZE_PIXELS
SCREEN_HEIGHT = MAZE_PIXELS + INFO_BAR_HEIGHT

ROWS = MAZE_PIXELS // CELL_SIZE   # 24
COLS = MAZE_PIXELS // CELL_SIZE   # 24

FONTSIZE_TITLE = 50
FONTSIZE_INFO = 25
FONTSIZE_MAZE = 20


# -----------------------------
# HELPER: TEXT RENDERING
# -----------------------------
def draw_text(surface: pygame.Surface, message: str, color, size: int, x: int, y: int) -> None:
    """Draw text on a surface at (x, y)."""
    font = pygame.font.SysFont(None, size)
    text_surface = font.render(message, True, color)
    surface.blit(text_surface, (x, y))


# -----------------------------
# NODE & BORDER
# -----------------------------
class NodeBorder:
    """Represents a single wall around a maze cell."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.color = BLACK
        self.rect = pygame.Rect(x, y, width, height)

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect)


class Node:
    """Single cell in the maze grid."""

    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

        # Pixel position of the top-left corner of the cell
        self.x = col * CELL_SIZE
        self.y = row * CELL_SIZE

        self.width = CELL_SIZE
        self.height = CELL_SIZE
        self.color = DARKGRAY

        self.visited = False        # used by DFS (maze generation)
        self.explored = False       # used by BFS (maze solving)
        self.parent = None          # used by BFS backtracking

        # Borders (walls)
        self.top_border = NodeBorder(self.x,
                                     self.y,
                                     CELL_SIZE,
                                     BORDER_THICKNESS)
        self.bottom_border = NodeBorder(self.x,
                                        self.y + CELL_SIZE - BORDER_THICKNESS,
                                        CELL_SIZE,
                                        BORDER_THICKNESS)
        self.left_border = NodeBorder(self.x,
                                      self.y,
                                      BORDER_THICKNESS,
                                      CELL_SIZE)
        self.right_border = NodeBorder(self.x + CELL_SIZE - BORDER_THICKNESS,
                                       self.y,
                                       BORDER_THICKNESS,
                                       CELL_SIZE)

        # Neighbor information
        self.neighbors: list[Node] = []             # geometric neighbors
        self.connected_neighbors: list[Node] = []   # neighbors with walls removed

    def render(self, surface: pygame.Surface) -> None:
        # Draw cell body
        pygame.draw.rect(surface, self.color,
                         pygame.Rect(self.x, self.y, self.width, self.height))

        # Draw borders
        self.top_border.render(surface)
        self.bottom_border.render(surface)
        self.left_border.render(surface)
        self.right_border.render(surface)


# -----------------------------
# MAZE
# -----------------------------
class Maze:
    """Maze grid + generation (DFS) + solving (BFS)."""

    def __init__(self, start_row: int, start_col: int, goal_row: int, goal_col: int):
        self.rows = ROWS
        self.cols = COLS

        self.start_row = start_row
        self.start_col = start_col
        self.goal_row = goal_row
        self.goal_col = goal_col

        self.grid: list[list[Node]] = []
        self.total_nodes = self.rows * self.cols
        self.maze_created = False

        # Build grid
        for row in range(self.rows):
            row_list = []
            for col in range(self.cols):
                row_list.append(Node(row, col))
            self.grid.append(row_list)

        self._define_neighbors()

    def _define_neighbors(self) -> None:
        """Define geometric (up/down/left/right) neighbors for all nodes."""
        for row in range(self.rows):
            for col in range(self.cols):
                node = self.grid[row][col]

                if row > 0:
                    node.neighbors.append(self.grid[row - 1][col])  # top
                if row < self.rows - 1:
                    node.neighbors.append(self.grid[row + 1][col])  # bottom
                if col > 0:
                    node.neighbors.append(self.grid[row][col - 1])  # left
                if col < self.cols - 1:
                    node.neighbors.append(self.grid[row][col + 1])  # right

    @staticmethod
    def _add_edge(a: Node, b: Node) -> None:
        """Mark two nodes as connected in the maze graph."""
        a.connected_neighbors.append(b)
        b.connected_neighbors.append(a)

    @staticmethod
    def _remove_visited_neighbors(node: Node) -> None:
        node.neighbors = [n for n in node.neighbors if not n.visited]

    @staticmethod
    def _break_border(a: Node, b: Node, color) -> None:
        """Change border colors between two neighboring nodes (simulate removing wall)."""
        # Same row -> horizontal movement
        if a.row == b.row:
            if b.col == a.col + 1:  # moved right
                a.right_border.color = color
                b.left_border.color = color
            elif b.col == a.col - 1:  # moved left
                a.left_border.color = color
                b.right_border.color = color
        # Same column -> vertical movement
        elif a.col == b.col:
            if b.row == a.row + 1:  # moved down
                a.bottom_border.color = color
                b.top_border.color = color
            elif b.row == a.row - 1:  # moved up
                a.top_border.color = color
                b.bottom_border.color = color

    # ---------- DFS: MAZE GENERATION ----------
    def generate(self, surface: pygame.Surface) -> None:
        """Generate maze using DFS with explicit stack."""
        current = random.choice(random.choice(self.grid))
        current.visited = True
        current.color = GREEN
        stack = [current]
        visited_count = 1

        while visited_count < self.total_nodes and stack:
            self._remove_visited_neighbors(current)

            if current.neighbors:
                neighbor = random.choice(current.neighbors)
                self._break_border(current, neighbor, GREEN)
                self._add_edge(current, neighbor)

                current = neighbor
                current.visited = True
                current.color = GREEN
                stack.append(current)
                visited_count += 1
            else:
                # backtrack
                current.color = YELLOW
                for border in (
                    current.top_border,
                    current.bottom_border,
                    current.left_border,
                    current.right_border,
                ):
                    if border.color == GREEN:
                        border.color = YELLOW

                stack.pop()
                if stack:
                    current = stack[-1]

            self.render(surface)
            draw_text(surface, "GENERATING MAZE", WHITE,
                      FONTSIZE_INFO, 215, MAZE_PIXELS + 20)
            pygame.display.flip()

        self.maze_created = True

    # ---------- BFS: MAZE SOLVING ----------
    def solve_with_bfs(self, surface: pygame.Surface, player: "Player") -> None:
        """Solve maze from player's current position to goal using BFS."""
        start_node = self.grid[player.row][player.col]
        start_node.explored = True

        queue = [start_node]
        found = False

        while queue and not found:
            node = queue.pop(0)
            node.color = PINK

            for border in (
                node.top_border,
                node.bottom_border,
                node.left_border,
                node.right_border,
            ):
                if border.color == YELLOW:
                    border.color = PINK

            for neighbor in node.connected_neighbors:
                if not neighbor.explored:
                    neighbor.explored = True
                    neighbor.parent = node
                    queue.append(neighbor)

                    if neighbor.row == self.goal_row and neighbor.col == self.goal_col:
                        found = True
                        break

            self.render(surface)
            draw_text(surface, "SOLVING MAZE", WHITE,
                      FONTSIZE_INFO, 218, MAZE_PIXELS + 20)
            player.render(surface)
            pygame.display.flip()

        # backtrack from goal to start to highlight final path
        current = self.grid[self.goal_row][self.goal_col]
        while current.parent is not None and current.parent.parent is not None:
            current = current.parent
            current.color = ORANGE

            for border in (
                current.top_border,
                current.bottom_border,
                current.left_border,
                current.right_border,
            ):
                if border.color == PINK:
                    border.color = ORANGE

            self.render(surface)
            player.render(surface)
            pygame.display.flip()

    # ---------- RENDER ----------
    def render(self, surface: pygame.Surface) -> None:
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col].render(surface)

        if self.maze_created:
            self.grid[self.start_row][self.start_col].color = BEIGE
            self.grid[self.goal_row][self.goal_col].color = LIGHTBLUE


# -----------------------------
# PLAYER
# -----------------------------
class Player:
    """Red square controlled by the player."""

    def __init__(self, start_row: int, start_col: int):
        self.row = start_row
        self.col = start_col
        self.color = RED

        self.width = CELL_SIZE - 2 * BORDER_THICKNESS
        self.height = CELL_SIZE - 2 * BORDER_THICKNESS
        self._update_pixel_position()

    def _update_pixel_position(self) -> None:
        self.x = self.col * CELL_SIZE + BORDER_THICKNESS
        self.y = self.row * CELL_SIZE + BORDER_THICKNESS

    def update(self, maze_grid: list[list[Node]], events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            node = maze_grid[self.row][self.col]

            if event.key == pygame.K_LEFT:
                if self.col > 0 and node.left_border.color != BLACK:
                    self.col -= 1
            elif event.key == pygame.K_RIGHT:
                if self.col < COLS - 1 and node.right_border.color != BLACK:
                    self.col += 1
            elif event.key == pygame.K_UP:
                if self.row > 0 and node.top_border.color != BLACK:
                    self.row -= 1
            elif event.key == pygame.K_DOWN:
                if self.row < ROWS - 1 and node.bottom_border.color != BLACK:
                    self.row += 1

            self._update_pixel_position()

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(
            surface,
            self.color,
            pygame.Rect(self.x, self.y, self.width, self.height),
        )


# -----------------------------
# GAME
# -----------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Maze Game")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.maze: Maze | None = None
        self.player: Player | None = None

        self.start_row = 0
        self.start_col = 0
        self.goal_row = 0
        self.goal_col = 0

        self.running = True
        self.game_started = False
        self.maze_solved = False
        self.player_won = False

    # ---------- SETUP ----------
    def _pick_random_points(self) -> None:
        self.start_row = random.randint(0, ROWS - 1)
        self.start_col = random.randint(0, COLS - 1)

        self.goal_row = random.randint(0, ROWS - 1)
        self.goal_col = random.randint(0, COLS - 1)

        # ensure start != goal
        while self.goal_row == self.start_row and self.goal_col == self.start_col:
            self.goal_row = random.randint(0, ROWS - 1)
            self.goal_col = random.randint(0, COLS - 1)

    def _load_new_maze(self) -> None:
        self._pick_random_points()
        self.maze = Maze(self.start_row, self.start_col, self.goal_row, self.goal_col)
        self.player = Player(self.start_row, self.start_col)
        self.maze_solved = False
        self.player_won = False

    # ---------- SCREENS ----------
    def _show_start_screen(self) -> None:
        self.screen.fill(DARKBLUE)
        pygame.draw.rect(self.screen, BEIGE, pygame.Rect(40, 40, 530, 580))
        pygame.draw.rect(self.screen, LIGHTBLUE, pygame.Rect(40, 100, 530, 450))
        pygame.draw.rect(self.screen, BLACK, pygame.Rect(110, 150, 380, 350))
        pygame.draw.rect(self.screen, DARKBLUE, pygame.Rect(110, 150, 380, 100))

        draw_text(self.screen, "MAZE ADVENTURES", LIGHTORANGE,
                  FONTSIZE_TITLE, 125, 185)
        draw_text(self.screen, "PRESS (ESC) TO CLOSE GAME", INTERMEDIARYORANGE,
                  FONTSIZE_INFO + 5, 150, 375)
        pygame.display.flip()
        pygame.time.wait(200)

        draw_text(self.screen, "PRESS (S) TO START GAME", INTERMEDIARYORANGE,
                  FONTSIZE_INFO + 5, 160, 350)
        pygame.display.flip()

    # ---------- GAME FLOW ----------
    def _handle_common_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def run(self) -> None:
        # Start screen loop
        while not self.game_started and self.running:
            self._show_start_screen()
            events = pygame.event.get()
            self._handle_common_events(events)

            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                    self.game_started = True

            self.clock.tick(30)

        if not self.running:
            pygame.quit()
            sys.exit(0)

        # Load maze and generate it
        self._load_new_maze()
        assert self.maze is not None and self.player is not None
        self.screen.fill(BLACK)
        self.maze.generate(self.screen)

        # Main game loop
        while self.running:
            events = pygame.event.get()
            self._handle_common_events(events)

            if not self.running:
                break

            # Restart
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self._load_new_maze()
                        self.screen.fill(BLACK)
                        self.maze.generate(self.screen)
                    elif event.key == pygame.K_q and not self.maze_solved and not self.player_won:
                        # give up -> auto-solve with BFS
                        self.screen.fill(BLACK)
                        self.maze.solve_with_bfs(self.screen, self.player)
                        self.maze_solved = True

            # Update player if game not already solved or won
            if not self.maze_solved and not self.player_won:
                self.player.update(self.maze.grid, events)

            # Win condition
            if (self.player.row == self.goal_row
                    and self.player.col == self.goal_col):
                self.player_won = True

            # RENDER
            self._render()

            self.clock.tick(60)

        pygame.quit()
        sys.exit(0)

    # ---------- RENDER ----------
    def _render(self) -> None:
        self.screen.fill(BLACK)
        assert self.maze is not None and self.player is not None

        # Maze + player
        self.maze.render(self.screen)
        self.player.render(self.screen)

        # Info bar
        if not self.maze_solved and not self.player_won:
            # Legend
            pygame.draw.rect(self.screen, RED, pygame.Rect(0, MAZE_PIXELS + 1,
                                                            CELL_SIZE, CELL_SIZE))
            draw_text(self.screen, "- PLAYER", WHITE, FONTSIZE_MAZE,
                      CELL_SIZE + 3, MAZE_PIXELS + 6)

            pygame.draw.rect(self.screen, BEIGE,
                             pygame.Rect(0, MAZE_PIXELS + CELL_SIZE + 2,
                                         CELL_SIZE, CELL_SIZE))
            draw_text(self.screen, "- STARTING POINT", WHITE, FONTSIZE_MAZE,
                      CELL_SIZE + 3, MAZE_PIXELS + CELL_SIZE + 8)

            pygame.draw.rect(self.screen, LIGHTBLUE,
                             pygame.Rect(0, MAZE_PIXELS + 2 * CELL_SIZE + 3,
                                         CELL_SIZE, CELL_SIZE))
            draw_text(self.screen, "- GOAL", WHITE, FONTSIZE_MAZE,
                      CELL_SIZE + 3, MAZE_PIXELS + 2 * CELL_SIZE + 9)

            draw_text(self.screen, "PRESS (R) TO RETRY GAME", WHITE,
                      FONTSIZE_MAZE, 220, MAZE_PIXELS + 10)
            draw_text(self.screen, "PRESS (Q) TO GIVE UP", WHITE,
                      FONTSIZE_MAZE, 230, MAZE_PIXELS + 30)
            draw_text(self.screen, "PRESS (ESC) TO CLOSE GAME", WHITE,
                      FONTSIZE_MAZE, 212, MAZE_PIXELS + 50)

        elif self.player_won:
            draw_text(self.screen, "YOU WIN", BLUE, FONTSIZE_MAZE + 3,
                      264, MAZE_PIXELS + 10)
            draw_text(self.screen, "PRESS (R) TO RETRY GAME", WHITE,
                      FONTSIZE_MAZE, 220, MAZE_PIXELS + 30)
            draw_text(self.screen, "PRESS (ESC) TO CLOSE GAME", WHITE,
                      FONTSIZE_MAZE, 212, MAZE_PIXELS + 50)
        else:
            draw_text(self.screen, "YOU LOSE", RED, FONTSIZE_MAZE + 3,
                      262, MAZE_PIXELS + 10)
            draw_text(self.screen, "PRESS (R) TO RETRY GAME", WHITE,
                      FONTSIZE_MAZE, 220, MAZE_PIXELS + 30)
            draw_text(self.screen, "PRESS (ESC) TO CLOSE GAME", WHITE,
                      FONTSIZE_MAZE, 212, MAZE_PIXELS + 50)

        pygame.display.flip()


# -----------------------------
# ENTRY POINT
# -----------------------------
def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
