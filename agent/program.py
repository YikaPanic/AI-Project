# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent
import random

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexDir, Board

import copy

DEFAULT_POWER = 0.1
DEFAULT_MAX = 1000000

MINIMAX_TREE_DEPTH = 3 # Test: 1 3 5
TOPK_VALUE = 15 # Test: 10 15 20

class Agent:
    def __init__(self, color: PlayerColor, **referee: dict):
        """
        Initialise the agent.
        """
        self._color = color
        self.state = {}
        self.game_board = Board()
        self.game_board.render()
        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as red")
            case PlayerColor.BLUE:
                print("Testing: I am playing as blue")
        return

    def action(self, **referee: dict) -> Action:
        """
        Return the next action to take.
        """
        transposition_table = {}
        match self._color:
            case PlayerColor.RED:
                player = 'MAX'
                action = self.alpha_beta_minimax_tree(self.game_board, PlayerColor.RED, player, MINIMAX_TREE_DEPTH)
                # _, action = self.minimax_tree_search(self.game_board, PlayerColor.RED, MINIMAX_TREE_DEPTH, float('-inf'),
                # float('inf'), transposition_table)
                return action
            case PlayerColor.BLUE:
                player = 'MAX'
                action = self.alpha_beta_minimax_tree(self.game_board, PlayerColor.BLUE, player, MINIMAX_TREE_DEPTH)
                # _, action = self.minimax_tree_search(self.game_board, PlayerColor.BLUE, MINIMAX_TREE_DEPTH, float('-inf'),
                # float('inf'), transposition_table) This is going to be invalid... BLUE never spawned!
                return action

    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        match action:
            case SpawnAction(cell):
                self.game_board.apply_action(action)
                print(f"Testing: {color} SPAWN at {cell}")
                pass
            case SpreadAction(cell, direction):
                self.game_board.apply_action(action)
                print(f"Testing: {color} SPREAD from {cell}, {direction}")
                pass

    def get_cor_list(self, color: PlayerColor, cur_board: Board):
        """
        :param color: player's color current turn
        :param cur_board: current board state
        :return: a list which contains coordinate of all the player's token
        """
        cor_list = []
        for cor, (player, power) in cur_board._state.items():
            if player == color:
                cor_list.append(cor)
        return cor_list

    def get_none_cell(self, cur_board: Board):
        """
        :param cur_board: current board state
        :return: a list which contains coordinate of all the empty cell
         in current board
        """
        none_cor_list = []
        for cor, (player, power) in cur_board._state.items():
            if player == None:
                none_cor_list.append(cor)
        return none_cor_list

    def generate_spread_action_list(self, cor_list):
        """
        :param cor_list: a list which contains coordinate of all the player's token
        :return: a list of action which can be used in referee agent that represent
         all the valid spread action in current
        """
        spread_list = []
        for cor in cor_list:
            for dir in HexDir:
                spread_list.append(SpreadAction(cell=cor, direction=dir))
        return spread_list

    def generate_spawn_action_list(self, cur_board: Board, none_cor_list):
        """
        :param none_cor_list: a list which contains coordinate of all the empty cell
        in current board
        :return: a list of action which can be used in referee agent that represent
        all the valid spawn action in current turn

        NOTICE: this function hasn't considered whether the board is full
        (no more than 49 powers on the current board in total)
        """
        total_power = 0
        for player, power in cur_board._state.values():
            total_power += power
        spawn_list = []
        if total_power >= 49:
            return spawn_list
        for cor in none_cor_list:
            spawn_list.append(SpawnAction(cell=cor))
        return spawn_list

    def get_cur_action_list(self, spread_list, spawn_list):
        """
        merge the spread action and spawn action to an action list
        """
        return spread_list + spawn_list

    def calculate_heuristic(self, cur_board: Board, color: PlayerColor, action: Action):
        self_power = 0
        enemy_power = 0
        cur_board.apply_action(action)
        for (player, power) in cur_board._state.values():
            if player == color:
                self_power += power
            else:
                enemy_power += power
        cur_board.undo_action()
        if self_power == 0 and cur_board.game_over:
            return -1000
        elif enemy_power == 0 and cur_board.game_over:
            return 1000
        return self_power - enemy_power

    def apply_heuristic_to_list(self, cur_board: Board, action_list, color: PlayerColor):
        """
        apply heuristic value for every action in action list,
        and change the list to a dict with key equals action,
        value equals heuristic value and return the dict
        """
        action_dict = {}
        for action in action_list:
            action_dict[action] = self.calculate_heuristic(cur_board, color, action)
        return action_dict

    def get_action_list(self, cur_board: Board, color: PlayerColor, top_k: int = TOPK_VALUE):
        """
        Based on the current chessboard information and turn color, generate all feasible actions
        and store them in the list structure. For each action in the list, apply it to the 
        current chessboard to calculate the utility value. Combine the generated utility value 
        with the corresponding action to form a new action dictionary. By disrupting the acion 
        dictionary and sorting it based on its value. Then combine the first k keys of the 
        dictionary into a new action list and return it
        """
        cor_list = self.get_cor_list(color, cur_board)
        none_cell = self.get_none_cell(cur_board)
        spread_list = self.generate_spread_action_list(cor_list)
        spawn_list = self.generate_spawn_action_list(cur_board, none_cell)
        action_list = self.get_cur_action_list(spread_list, spawn_list)

        action_dict = self.apply_heuristic_to_list(cur_board, action_list, color)
        keys = list(action_dict.keys())
        random.shuffle(keys)

        shuffled_dict = {}
        for key in keys:
            shuffled_dict[key] = action_dict[key]

        # Sort actions by heuristic values and select the top k actions
        sorted_actions_temp = sorted(shuffled_dict.items(), key=lambda x: x[1], reverse=True)

        sorted_actions = []
        for item in sorted_actions_temp:
            sorted_actions.append(item[0])

        top_k_actions = sorted_actions[:top_k]

        return top_k_actions

    def get_action_dict(self, cur_board: Board, color: PlayerColor):
        """
        get action dict for current board.
        """
        action_list = self.get_action_list(cur_board, color)
        action_dict = self.apply_heuristic_to_list(cur_board, action_list, color)
        return action_dict

    def minimax_tree_search(self, cur_board: Board, turn_color: PlayerColor, depth, alpha, beta, transposition_table):
        """
        old version of mini-max tree search with transposition table
        """
        # Check if the current board state is in the transposition table.
        board_hash = hash(cur_board)
        if board_hash in transposition_table and depth <= transposition_table[board_hash][1]:
            return transposition_table[board_hash][0], None
        # if current board has no valid action or the game is over, return the action
        if depth == 0 or cur_board.game_over:
            return self.new_evaluate_board(cur_board, turn_color), None

        best_value = float('-inf')
        best_action = None

        # do recursion until we reach the root depth, apply value changes to the recursion
        for action in self.get_action_list(cur_board, turn_color, top_k=TOPK_VALUE):
            new_board = self.clone_board(cur_board)
            new_board.apply_action(action)

            value, _ = self.minimax_tree_search(new_board, turn_color.opponent, depth - 1, -beta, -alpha, transposition_table)
            value = -value + self.evaluate_board(new_board, turn_color.opponent)

            if value > best_value:
                best_value = value
                best_action = action

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        # Store the best_value for the current board state and depth in the transposition table
        transposition_table[board_hash] = (best_value, depth)

        return best_value, best_action

    def evaluate_board(self, cur_board: Board, color: PlayerColor):
        """
        old version of evaluation function, abandoned
        """
        action_dict = self.get_action_dict(cur_board, color)

        total_score = max(action_dict.values())
        return total_score

    def new_evaluate_board(self, cur_board: Board, color: PlayerColor):
        """
        calculates the game state's value by subtracting the total power of the opponent's 
        pieces from the total power of the current player's pieces.
        """
        if cur_board.winner_color == color.opponent:
            return float('-inf')
        elif cur_board.winner_color == color:
            return float('inf')
        self_power = 0
        opponent_power = 0
        for (player, power) in cur_board._state.values():
            if player == color:
                self_power += power
            elif player == color.opponent:
                opponent_power += power
        value = self_power - opponent_power
        return value

    def clone_board(self, cur_board: Board) -> Board:
        
        new_board = Board()
        new_board = copy.deepcopy(cur_board)
        return new_board

    def alpha_beta_prune(self, cur_board: Board, turn_color: PlayerColor, depth, alpha, beta, player):
        """
        do a recursion, apply alpha beta prune to the minimax tree search, each MAX turn, choose best action
        and apply value to alpha if value is bigger than alpha, each MIN turn, choose best
        action and apply value to beta if value is smaller than beta, once alpha large than
        beta, cut off the node
        """
        if depth == 0 or cur_board.game_over:
            return self.new_evaluate_board(cur_board, turn_color)

        if player == 'MAX':
            value = float('-inf')
            for action in self.get_action_list(cur_board, turn_color, top_k=TOPK_VALUE):
                new_board = self.clone_board(cur_board)
                new_board.apply_action(action)
                if cur_board.winner_color == turn_color.opponent:
                    value = float('-inf')
                elif cur_board.winner_color == turn_color:
                    value = float('inf')
                else:
                    value = max(value, self.alpha_beta_prune(new_board, turn_color.opponent, depth - 1, alpha, beta, 'MIN'))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for action in self.get_action_list(cur_board, turn_color, top_k=TOPK_VALUE):
                new_board = self.clone_board(cur_board)
                new_board.apply_action(action)
                if cur_board.winner_color == turn_color.opponent:
                    value = float('-inf')
                elif cur_board.winner_color == turn_color:
                    value = float('inf')
                else:
                    value = max(value, self.alpha_beta_prune(new_board, turn_color.opponent, depth - 1, alpha, beta, 'MAX'))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    def alpha_beta_minimax_tree(self, cur_board: Board, turn_color: PlayerColor, player, depth):
        """
        main body of the minimaxtree search, apply all the posible move to the board and call 
        alpha_beta_prune function to do the alpha-beta minimax tree search, update the best action 
        according to the value of the action returned from alpha_beta_prune function
        """
        best_action = None
        opponent_player = None
        if player == 'MAX':
            best_value = float('-inf')
            opponent_player = 'MIN'
        else:
            best_value = float('inf')
            opponent_player = 'MAX'

        for action in self.get_action_list(cur_board, turn_color, top_k=TOPK_VALUE):
            cur_board.apply_action(action)
            if cur_board.winner_color == turn_color.opponent:
                value = float('-inf')
            elif cur_board.winner_color == turn_color:
                value = float('inf')
            else:
                value = self.alpha_beta_prune(cur_board, turn_color.opponent, depth - 1, float('-inf'), float('inf'), opponent_player)
            cur_board.undo_action()
            if (player == 'MAX'):
                if value > best_value:
                    best_value = value
                    best_action = action
            else:
                if value < best_value:
                    best_value = value
                    best_action = action
        return best_action
