import copy
import threading
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import math
from PIL import Image, ImageTk
from module import DatabaseManager, MultiColumnListbox
from datetime import datetime
import ctypes
    
class HalmaGame:
    def __init__(self, root):
        # Create GUI window
        self.root = root
        self.root.title("Halma Game")
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.resizable(False, False)
        self.select_game_window = None

        # Set up Database if not already
        self.db = DatabaseManager("halma.db")
        self.db.setup_tables()

        # Set options        
        # Colour codes taken from https://omgchess.blogspot.com/2015/09/chess-board-color-schemes.html
        self.board_colour_options = {
            "Coral": ["#70A2A3", "#B1E4B9"],
            "Dusk": ["#706677", "#CCB7AE"],
            "Marine": ["#6F73D2", "#9DACFF"],
            "Wheat": ["#BBBE64", "#EAF0CE"],
            "Emerald": ["#6F8F72", "#ADBD8F"],
            "Sandcastle": ["#B88B4A", "#E3C16F"]
        }

        self.HIGHLIGHT_COLOUR = "yellow"
        self.BASE_COLOUR = "blue"
        self.LAST_MOVE_COLOUR = "red"
        self.VALID_MOVES_COLOUR = "grey"
        self.BEST_MOVE_COLOUR = "grey"
        self.BUTTON_HEIGHT = 25
        self.BUTTON_WIDTH = 50
        self.player_one = ctk.StringVar()
        self.player_two = ctk.StringVar()
        self.board_colours = ctk.StringVar()
        self.theme = ctk.StringVar()
        self.grid_size = ctk.IntVar()

        # Set up configurations
        config = self.db.get_last_config()
        self.grid_size.set(config[0])
        self.board_colours.set(config[1])
        self.theme.set(config[2])
        ctk.set_appearance_mode(self.theme.get())

        self.SIDE = 700
        self.cell_size = self.SIDE // self.grid_size.get()

        self.open_images()

        self.canvas = ctk.CTkCanvas(self.root, width=self.SIDE, height=self.SIDE, highlightthickness=0)
        # Canvas background same as root
        self.canvas.configure(bg=self.root.cget("bg"))
        self.canvas.grid(row=0, padx=10, pady=10)
        
        # Initialise board
        self.set_game()

        # Create Side Panel
        self.side_panel = ctk.CTkFrame(self.root)
        self.side_panel.grid(row=0, column=1, padx=20, sticky="w")

        self.set_menu()

    def open_images(self):
        # Open the piece images using PILLOW
        self.img = Image.open("red.png").resize((self.cell_size - 5, self.cell_size - 5), Image.LANCZOS)
        self.piece_one = ImageTk.PhotoImage(self.img)

        self.img = Image.open("blue.png").resize((self.cell_size - 5, self.cell_size - 5), Image.LANCZOS)
        self.piece_two = ImageTk.PhotoImage(self.img)

    def set_game(self):
        # Create the game board and variables
        self.playing = True
        self.selected_piece = None
        self.last_move = None
        self.jumped_from = None
        self.current_player = 1
        self.jumping = False
        self.move_history = []
        self.num_moves = 0
        self.show_move = 0
        self.in_play = True
        self.analysing = False

        self.reset_board()
        self.move_history.append(copy.deepcopy(self.board))
    
    def reset_board(self):
        self.player_one_positions = [
            (self.grid_size.get() - 1, self.grid_size.get() - 1),

            (self.grid_size.get() - 1, self.grid_size.get() - 2), (self.grid_size.get() - 2, self.grid_size.get() - 1),

            (self.grid_size.get() - 1, self.grid_size.get() - 3), (self.grid_size.get() - 2, self.grid_size.get() - 2), 
            (self.grid_size.get() - 3, self.grid_size.get() - 1),

            (self.grid_size.get() - 1, self.grid_size.get() - 4), (self.grid_size.get() - 2, self.grid_size.get() - 3), 
            (self.grid_size.get() - 3, self.grid_size.get() - 2), (self.grid_size.get() - 4, self.grid_size.get() - 1),
        ]

        self.player_two_positions = [
            (0, 0),
            (0, 1), (1, 0),
            (0, 2), (1, 1), (2, 0),
            (0, 3), (1, 2), (2, 1), (3, 0),
        ]
        
        self.board = [[0 for x in range(self.grid_size.get())] for y in range(self.grid_size.get())]

        for row, col in self.player_one_positions:
            self.board[row][col] = 1

        for row, col in self.player_two_positions:
            self.board[row][col] = 2
        
        self.draw_board()

    def bind_keys(self):
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.root.bind("<Return>", lambda event: self.confirm())
        self.root.bind("<Left>",  lambda event: self.prev_move())
        self.root.bind("<Right>",  lambda event: self.next_move())
        self.root.bind("<Up>",  lambda event: self.end())
        self.root.bind("<Down>",  lambda event: self.beginning())

    def unbind_keys(self):
        self.canvas.unbind("<Button-1>")
        self.root.unbind("<Return>")
        self.root.unbind("<Left>")
        self.root.unbind("<Right>")
        self.root.unbind("<Up>")
        self.root.unbind("<Down>")

    def set_game_panel(self):
        self.clear_side_panel()

        player_two_label = ctk.CTkLabel(self.side_panel, textvariable=self.player_two, anchor="nw")
        player_two_label.grid(row=0, columnspan=2, sticky="new")

        self.beginning_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="<<-", command=self.beginning)
        self.beginning_button.grid(row=1)

        self.prev_move_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="<-", command=self.prev_move)
        self.prev_move_button.grid(row=1, column=1)

        self.next_move_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="->", command=self.next_move)
        self.next_move_button.grid(row=1, column=2)

        self.end_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="->>", command=self.end)
        self.end_button.grid(row=1, column=3)

        self.info_string = ctk.StringVar()
        self.info_string.set(self.player_names[self.current_player - 1].get() + "'s Turn")
        info_text = ctk.CTkLabel(self.side_panel, textvariable=self.info_string, anchor="nw", bg_color="red")
        info_text.grid(row=2, columnspan=4, sticky="new")

        self.undo_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="⎌", command=self.undo)
        self.undo_button.configure(state="disabled")
        self.undo_button.grid(row=3)

        self.confirm_button = ctk.CTkButton(self.side_panel, text="Confirm", height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*2, command=self.confirm)
        self.confirm_button.configure(state="disabled")
        self.confirm_button.grid(row=3, column=1, columnspan=2)

        #New game
        self.new_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="+", command=self.new_game)
        self.new_button.grid(row=3, column=3)

        player_one_label = ctk.CTkLabel(self.side_panel, textvariable=self.player_one, anchor="nw")
        player_one_label.grid(row=4, columnspan=2, sticky="new")

        self.set_in_play()

    def set_menu(self):
        self.clear_side_panel()
        self.unbind_keys()
        
        play_player_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT*3, width=self.BUTTON_WIDTH*4, text="Play vs Player", command=lambda: self.start_game(False))
        play_player_button.grid(row=0)

        play_ai_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT*3, width=self.BUTTON_WIDTH*4, text="Play vs AI", command=lambda: self.start_game(True))
        play_ai_button.grid(row=1)

        analyse_game_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT*3, width=self.BUTTON_WIDTH*4, text="Analyse Game", command=self.select_game)
        analyse_game_button.grid(row=2)

        manage_players_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT*3, width=self.BUTTON_WIDTH*4, text="Manage Players", command=self.manage_players)
        manage_players_button.grid(row=3)

        settings_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT*3, width=self.BUTTON_WIDTH*4, text="Settings", command=self.settings)
        settings_button.grid(row=4)

    def clear_side_panel(self):
        for widgets in self.side_panel.winfo_children():
            widgets.destroy()
    
    def start_game(self, ai):
        self.ai_player = 2 if ai else 0
        if ai:
            self.choose_ai()
        else:
            self.choose_pvp()

    def choose_ai(self):
        self.clear_side_panel()
        player_names = self.db.get_player_names()

        player_label = ctk.CTkLabel(self.side_panel, text="Player Name", anchor="nw", height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH)
        player_label.grid(row=0)
        self.player_one.set(player_names[0])
        drop_one = ctk.CTkOptionMenu(master=self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*4, values=player_names, variable=self.player_one)
        drop_one.grid(row=1)
        
        ai_label = ctk.CTkLabel(self.side_panel, text="AI Difficulty", anchor="nw", height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH)
        ai_label.grid(row=2)
        self.player_two.set("")
        self.depth = ctk.IntVar()
        self.depth.set(1)
        difficulty = ctk.CTkSlider(self.side_panel, from_=1, to=5, number_of_steps=4, variable=self.depth)
        difficulty.grid(row=3)

        state = ctk.StringVar()
        state.set("on")
        start_switch = ctk.CTkSwitch(self.side_panel, text="Make first move", command=self.switcher, variable=state, onvalue="on", offvalue="off")
        start_switch.grid(row=4)

        submit_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Start Game", command=self.submit)
        submit_button.grid(row=5)

        back_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Back", command=self.set_menu)
        back_button.grid(row=6)

    def switcher(self):
        self.player_one, self.player_two = self.player_two, self.player_one
        self.ai_player = 3 - self.ai_player

    def choose_pvp(self):
        self.clear_side_panel()
        players = self.db.get_player_names()

        player_one_label = ctk.CTkLabel(self.side_panel, text="Player One Name", anchor="nw", height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH)
        player_one_label.grid(row=0)
        self.player_one.set(players[0])
        drop_one = ctk.CTkOptionMenu(master=self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*4, values=players, variable=self.player_one)
        drop_one.grid(row=1)

        player_two_label = ctk.CTkLabel(self.side_panel, text="Player Two Name", anchor="nw", height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH)
        player_two_label.grid(row=2)
        self.player_two.set(players[0])
        drop_two = ctk.CTkOptionMenu(master=self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*4, values=players, variable=self.player_two)
        drop_two.grid(row=3)
        
        submit_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Start Game", command=self.submit)
        submit_button.grid(row=4)

        back_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Back", command=self.set_menu)
        back_button.grid(row=5)

    def submit(self):
        # Set AI Name
        if not self.player_one.get():
            self.player_one.set("AI Difficulty " + str(self.depth.get()))
        if not self.player_two.get():
            self.player_two.set("AI Difficulty " + str(self.depth.get()))

        self.player_names = [self.player_one, self.player_two]
        self.set_game()
        self.bind_keys()
        self.set_game_panel()
        if self.ai_player == 1:
            self.ai_turn()

    def select_game(self):
        if self.select_game_window is None or not self.select_game_window.winfo_exists():
            value = []
            self.select_game_window = ToplevelWindow(value, self.BUTTON_HEIGHT, self.BUTTON_WIDTH)
            self.select_game_window.wait_window()
            if value:
                self.analyse_game(value[-1])
        else:
            self.select_game_window.focus()

    def analyse_game(self, game_id):
        self.best_move = []
        self.set_game()
        self.bind_keys()
        self.canvas.unbind("<Button-1>")
        self.analysing = True
        self.load_game(game_id)
        self.set_analysis_panel()

    def load_game(self, game_id):
        moves = self.db.get_moves(game_id)
        game = self.db.get_game(game_id)
        self.player_one.set(self.db.get_player_name(game[1]))
        self.player_two.set(self.db.get_player_name(game[2]))
        self.change_board_size(game[4])
        self.move_history = []
        for move in moves:
            move = move[0].split(",")
            move_arr = []
            for row in move:
                move_arr.append([int(x) for x in list(row)])
            self.move_history.append(copy.deepcopy(move_arr))
        self.num_moves = game[7]

    def set_analysis_panel(self):
        self.clear_side_panel()
        self.process = None

        player_two_label = ctk.CTkLabel(self.side_panel, textvariable=self.player_two, anchor="nw")
        player_two_label.grid(row=0, columnspan=2, sticky="new")

        self.beginning_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="<<-", command=self.beginning)
        self.beginning_button.grid(row=1)

        self.prev_move_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="<-", command=self.prev_move)
        self.prev_move_button.grid(row=1, column=1)

        self.next_move_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="->", command=self.next_move)
        self.next_move_button.grid(row=1, column=2)

        self.end_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="->>", command=self.end)
        self.end_button.grid(row=1, column=3)

        self.best_move_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*4, text="View Best Move", command=self.view_best_move)
        self.best_move_button.grid(row=2, columnspan=4)

        # Do not grid yet
        self.eval = ctk.StringVar()
        self.eval_label = ctk.CTkLabel(self.side_panel, textvariable=self.eval, anchor="nw")

        player_one_label = ctk.CTkLabel(self.side_panel, textvariable=self.player_one, anchor="nw")
        player_one_label.grid(row=3, columnspan=2, sticky="new")

        back_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Back", command=self.stop_analysis)
        back_button.grid(row=4, column=1, columnspan=2)

        self.set_in_play()

    def view_best_move(self):
        self.depth = ctk.IntVar()
        self.depth.set(1)
        self.best_move_button.grid_forget()
        self.eval.set("Evaluation:")
        self.eval_label.grid(row=2, columnspan=4, sticky="new")
        self.process = threading.Thread(target=self.improve_eval, daemon=True)
        self.process.start()

    def improve_eval(self):
        while self.depth.get() < 20:
            eval, best_move = self.minimax(copy.deepcopy(self.move_history[self.show_move]), self.depth.get(), -math.inf, math.inf, self.show_move % 2 == 0)
            self.eval.set(f'Evaluation: {eval:.2f} (Depth {self.depth.get()})')
            if best_move:
                self.best_move = [(best_move[0], best_move[1]), (best_move[2], best_move[3])]
            self.depth.set(self.depth.get() + 1)
            self.draw_board()

    def stop_analysis(self):
        self.best_move = []
        if self.process:
            self.terminate_thread(self.process)
        self.set_game()
        self.reset_board()
        self.set_menu()

    def manage_players(self):
        self.clear_side_panel()

        add_player_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT*3, width=self.BUTTON_WIDTH*4, text="Add Player", command=self.add_player)
        add_player_button.grid(row=0)

        disable_player_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT*3, width=self.BUTTON_WIDTH*4, text="Disable Player", command=self.disable_player)
        disable_player_button.grid(row=1)

        player_stats_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT*3, width=self.BUTTON_WIDTH*4, text="View Player Stats", command=self.view_stats)
        player_stats_button.grid(row=2)

        back_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Back", command=self.set_menu)
        back_button.grid(row=3)

    def add_player(self):
        self.clear_side_panel()

        new_name_label = ctk.CTkLabel(self.side_panel, text="Enter new player name")
        new_name_label.grid(row=0)

        self.new_name = ctk.StringVar()
        entry = ctk.CTkEntry(master=self.side_panel, textvariable=self.new_name)
        entry.grid(row=1)

        submit_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Add Player", command=self.player_added)
        submit_button.grid(row=2)

        back_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Back", command=self.manage_players)
        back_button.grid(row=3)

    def player_added(self):
        players = self.db.get_player_names()
        if not self.new_name.get():
            CTkMessagebox(title="Enter a name!", 
                            message="Please enter a name!", 
                            icon="warning", 
                            option_1="Ok")
        else:
            success = self.db.add_player(self.new_name.get(), False)
            if success:
                self.manage_players()
                CTkMessagebox(title="Added Player", 
                                message="Player '" + self.new_name.get() + "' has been added.", 
                                icon="check", 
                                option_1="Close")
            else:
                CTkMessagebox(title="Name in use!", 
                message="This name is already being used!", 
                icon="warning", 
                option_1="Ok")

    def disable_player(self):
        self.clear_side_panel()

        players = self.db.get_player_names()

        # Should not be able to deactivate guest users
        players.remove("Guest")

        disable_label = ctk.CTkLabel(self.side_panel, text="Choose a player to disable:")
        disable_label.grid(row=0)

        self.player_to_disable = ctk.StringVar()
        player_filter = ctk.CTkOptionMenu(master=self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*4, values=players, variable=self.player_to_disable)
        player_filter.grid(row=1)

        submit_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Disable", command=self.player_disabled)
        submit_button.grid(row=2)

        back_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Back", command=self.manage_players)
        back_button.grid(row=3)

    def player_disabled(self):
        self.db.disable_player(self.player_to_disable.get())
        CTkMessagebox(title="Disabled Player", 
                            message="Player '" + self.player_to_disable.get() + "' has been disabled.", 
                            icon="check", 
                            option_1="Close")
        self.manage_players()
        
    def view_stats(self):
        self.clear_side_panel()

        players = self.db.get_player_names()
        self.stats_player = ctk.StringVar()
        self.number_games = ctk.StringVar()
        self.number_wins = ctk.StringVar()
        self.average_moves = ctk.StringVar()
        self.number_games.set("-")
        self.number_wins.set("-")
        self.average_moves.set("-")

        player_label = ctk.CTkLabel(self.side_panel, text="Choose a Player to view their stats:")
        player_label.grid(row=0, columnspan=2)
        stats_options = ctk.CTkOptionMenu(master=self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*4, values=players, variable=self.stats_player, command=self.get_stats)
        stats_options.grid(row=1, columnspan=2)

        # Number of games played
        games_played_label = ctk.CTkLabel(self.side_panel, text="Number of Games Played:")
        games_played_label.grid(row=2)
        games_played = ctk.CTkLabel(self.side_panel, textvariable=self.number_games)
        games_played.grid(row=2, column=1)
        # Number of wins
        wins_label = ctk.CTkLabel(self.side_panel, text="Number of Wins:")
        wins_label.grid(row=3)
        wins = ctk.CTkLabel(self.side_panel, textvariable=self.number_wins)
        wins.grid(row=3, column=1)
        # Average number of moves
        average_label = ctk.CTkLabel(self.side_panel, text="Average Moves:")
        average_label.grid(row=4)
        average = ctk.CTkLabel(self.side_panel, textvariable=self.average_moves)
        average.grid(row=4, column=1)

        back_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Back", command=self.manage_players)
        back_button.grid(row=5, columnspan=2)
        
    def get_stats(self, player_name):
        id = self.db.get_player_id(player_name)
        self.number_games.set(str(self.db.get_number_games(id)))
        self.number_wins.set(str(self.db.get_number_wins(id)))
        self.average_moves.set(str(self.db.get_average_moves(id)))

    def settings(self):
        self.clear_side_panel()
        colour_schemes = [key for key in self.board_colour_options]
        themes = ["System", "Light", "Dark"]

        board_size_label = ctk.CTkLabel(self.side_panel, text="Board Size")
        board_size_label.grid(row=0)
        size = ctk.CTkSlider(self.side_panel, from_=5, to=16, number_of_steps=15, variable=self.grid_size, command=self.change_board_size)
        size.grid(row=1)

        board_colour_label = ctk.CTkLabel(self.side_panel, text="Board Colour")
        board_colour_label.grid(row=2)

        choose_board_colour = ctk.CTkOptionMenu(master=self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*4, values=colour_schemes, variable=self.board_colours, command=lambda x: self.reset_board())
        choose_board_colour.grid(row=3)

        theme_label = ctk.CTkLabel(self.side_panel, text="Theme")
        theme_label.grid(row=4)

        theme = ctk.CTkOptionMenu(master=self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*4, values=themes, variable=self.theme, command=lambda x: self.change_theme())
        theme.grid(row=5)

        back_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Back", command=self.set_menu)
        back_button.grid(row=6)

    def change_board_size(self, value):
        self.cell_size = int(self.SIDE / self.grid_size.get())
        self.open_images()
        self.reset_board()

    def change_theme(self):
        ctk.set_appearance_mode(self.theme.get())
        self.canvas.configure(bg=self.root.cget("bg"))

    def draw_board(self):
        # Delete Previous Board
        self.canvas.delete("pieces")

        if self.in_play:
            position = self.board
        else:
            position = self.move_history[self.show_move]

        if self.selected_piece:
            valid_moves = self.show_valid_moves(position, self.selected_piece[0], self.selected_piece[1])
        else:
            valid_moves = []

        # Adjustment to centre images correctly
        image_adjustment = self.cell_size / 2
        
        for row in range(self.grid_size.get()):
            for col in range(self.grid_size.get()):
                x_start, y_start = col * self.cell_size, row * self.cell_size
                x_finish, y_finish = x_start + self.cell_size, y_start + self.cell_size
                colour = self.board_colour_options[self.board_colours.get()][0] if (row + col) % 2 == 0 else self.board_colour_options[self.board_colours.get()][1]

                if self.analysing and (row, col) in self.best_move:
                    self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.BEST_MOVE_COLOUR, tags="pieces")
                elif (row, col) == self.selected_piece and self.in_play:
                    self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.HIGHLIGHT_COLOUR, tags="pieces")
                elif (row, col) in valid_moves and self.in_play:
                    self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.VALID_MOVES_COLOUR, tags="pieces")
                elif (row, col) == self.last_move and self.in_play:
                    self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.LAST_MOVE_COLOUR, tags="pieces")
                elif (row, col) in (self.player_one_positions + self.player_two_positions):
                    self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.BASE_COLOUR, tags="pieces")
                else:
                    self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=colour, tags="pieces")

                if position[row][col] == 1:
                    self.canvas.create_image(x_start + image_adjustment, y_start + image_adjustment, anchor="center", image=self.piece_one, tags="pieces")
                elif position[row][col] == 2:
                    self.canvas.create_image(x_start + image_adjustment, y_start + image_adjustment, anchor="center", image=self.piece_two, tags="pieces")
    
    def on_left_click(self, event):
        row, col = event.y // self.cell_size, event.x // self.cell_size
        if row < self.grid_size.get() and col < self.grid_size.get() and self.in_play:
            if self.board[row][col] == self.current_player and not self.jumping:
                self.select_piece(row, col)
            elif self.selected_piece:
                self.move_piece(row, col)  

    def select_piece(self, row, col):
        if self.selected_piece == (row, col):
            self.selected_piece = None
        else:
            self.selected_piece = (row, col)
        # Update board to show selected piece
        self.draw_board()

    def show_valid_moves(self, position, row, col):
        moves = []
        for x in range(-2, 3):
            for y in range(-2, 3):
                if 0 <= (row + x) < self.grid_size.get() and 0 <= (col + y) < self.grid_size.get():
                    if self.valid_move(position, row, col, row + x, col + y)[0]:
                        moves.append((row + x, col + y))
        return moves
    
    def move_piece(self, row, col):
        prev_row, prev_col = self.selected_piece
        valid, jump = self.valid_move(self.board, prev_row, prev_col, row, col)
        if valid:
            # First jump
            if not self.jumping and jump:
                self.jumped_from = self.selected_piece
            # Set if jumping or not
            self.jumping = jump
            self.board[row][col] = self.current_player
            self.board[prev_row][prev_col] = 0
            if self.jumping:
                self.confirm_button.configure(state="normal")
                self.selected_piece = (row, col)
                self.draw_board()
            else:
                self.last_move = (row, col)
                self.switch_player()
        elif not self.jumping:
            self.selected_piece = None
            self.draw_board()
    
    def valid_move(self, position, src_row, src_col, dest_row, dest_col):
        vector = (dest_row - src_row, dest_col - src_col)
        jump = False
        # Check if move
        valid = False
        if (vector[0] == 0 or abs(vector[0]) == 1) and (vector[1] == 0 or abs(vector[1]) == 1) \
            and not self.jumping:
            valid = True
        # Check if jump
        elif (vector[0] == 0 or abs(vector[0]) == 2) and (vector[1] == 0 or abs(vector[1]) == 2) \
            and position[src_row + vector[0] // 2][src_col + vector[1] // 2] != 0 \
                and (dest_row, dest_col) != self.jumped_from:
            valid = True
            jump = True
        # Check if there is a piece in destination square
        if position[dest_row][dest_col] != 0:
            valid = False
        return valid, jump
    
    def switch_player(self):
        # Deselect any pieces
        self.selected_piece = None
        self.jumped_from = None

        # Add move to moves list
        self.move_history.append(copy.deepcopy(self.board))
        self.num_moves += 1
        if self.num_moves >= 1:
            self.undo_button.configure(state="normal")
        self.show_move = self.num_moves

        # Update board to show any moves
        self.draw_board()
        self.set_in_play()
        if self.check_win(self.board):
            self.game_over()
            return None
        
        self.current_player = 3 - self.current_player
        self.info_string.set(self.player_names[self.current_player - 1].get() + "'s Turn")

        # Allow the UI to update before potential AI turn
        self.side_panel.update_idletasks()
        if self.current_player == self.ai_player:
            self.ai_turn()

    def ai_turn(self):
        best_move = self.minimax(copy.deepcopy(self.board), self.depth.get(), -math.inf, math.inf, self.current_player == 1)[1]

        self.last_move = (best_move[2], best_move[3])
        self.apply_move(self.board, best_move)
        self.switch_player()

    def minimax(self, position, depth, alpha, beta, max_player):
        if depth <= 0 or self.check_win(position):
            return self.evaluate(position), None
        valid_moves = self.get_valid_moves(position, max_player)
        valid_moves = self.sort_moves(position, valid_moves, max_player)

        # Cut down moves to be analysed
        cutoff = max(int(len(valid_moves) // (self.depth.get()**(self.depth.get()/2))) + 1, 3)
        valid_moves = valid_moves[:cutoff]
        best_move = None

        if max_player:
            max_eval = -math.inf
            for move in valid_moves:
                new_pos = self.apply_move(copy.deepcopy(position), move)
                # Use of recursive algorithms here
                eval = self.minimax(new_pos, depth - 1, alpha, beta, False)[0]
                if eval > max_eval:
                    max_eval = eval
                    best_move = move

                # Alpha-beta pruning
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return (max_eval, best_move)
        else:
            min_eval = math.inf
            for move in valid_moves:
                new_pos = self.apply_move(copy.deepcopy(position), move)
                # Use of recursive algorithms here
                eval = self.minimax(new_pos, depth - 1, alpha, beta, True)[0]
                if eval < min_eval:
                    min_eval = eval
                    best_move = move

                # Alpha-beta pruning
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return (min_eval, best_move)
        
    def sort_moves(self, position, valid_moves, max_player):
        eval_move = sorted([(self.evaluate(self.apply_move(copy.deepcopy(position), move)), move) for move in valid_moves])
        if max_player:
            eval_move = eval_move[::-1]
        return [combo[1] for combo in eval_move]

    def evaluate(self, position):
        win = self.check_win(position)
        if win == 1:
            return self.grid_size.get() * 50
        elif win == 2:
            return - self.grid_size.get() * 50
        score = 0
        for i in range(self.grid_size.get()):
            for j in range(self.grid_size.get()):
                if position[i][j] == 1:
                    score -= (i + j)
                elif position[i][j] == 2:
                    score += ((self.grid_size.get() - 1 - i) + (self.grid_size.get() - 1 - j))
        return score
    
    def get_valid_moves(self, position, max_player):
        moves = []
        jumps = []
        player = 1 if max_player else 2
        for row in range(self.grid_size.get()):
            for col in range(self.grid_size.get()):
                if position[row][col] == player:
                    for x in range(-2, 3):
                        for y in range(-2, 3):
                            if 0 <= (row + x) < self.grid_size.get() and 0 <= (col + y) < self.grid_size.get():
                                valid, jumping = self.valid_move(position, row, col, row + x, col + y)
                                if valid:
                                    if jumping:
                                        jumps.append((row, col, row + x, col + y))
                                    else:
                                        moves.append((row, col, row + x, col + y))
        changed = True
        while changed:
            changed = False
            new = []
            for jump in jumps:
                new_pos = self.apply_move(copy.deepcopy(position), jump)
                for x in range(-2, 3, 2):
                    for y in range(-2, 3, 2):
                        if 0 <= (jump[2] + x) < self.grid_size.get() and 0 <= (jump[3] + y) < self.grid_size.get() and not (jump[0] == jump[2] + x and jump[1] == jump[3] + y):
                            if (jump[0], jump[1], jump[2] + x, jump[3] + y) not in jumps and self.valid_move(new_pos, jump[2], jump[3], jump[2] + x, jump[3] + y)[0]:
                                    new.append((jump[0], jump[1], jump[2] + x, jump[3] + y))
                                    changed = True
            jumps = new + jumps
        return jumps + moves
    
    def apply_move(self, position, move):
        player = position[move[0]][move[1]]
        position[move[0]][move[1]] = 0
        position[move[2]][move[3]] = player
        return position
    
    def check_win(self, position):
        win = True
        enemy = False
        for coords in self.player_one_positions:
            if position[coords[0]][coords[1]] == 0:
                win = False
            elif position[coords[0]][coords[1]] == 2:
                enemy = True
        if win and enemy:
            return 2
        win = True
        enemy = False
        for coords in self.player_two_positions:
            if position[coords[0]][coords[1]] == 0:
                win = False
            elif position[coords[0]][coords[1]] == 1:
                enemy = True
        if win and enemy:
            return 1
        return 0
    
    def game_over(self):
        self.playing = False
        self.last_move = None
        self.canvas.unbind("<Button-1>")
        winner = self.player_names[self.current_player - 1]
        self.info_string.set(winner.get() + " Wins!")
        self.confirm_button.configure(state="disabled")
        self.undo_button.configure(state="disabled")
        if self.num_moves > 0:
            msg = CTkMessagebox(title="Save?", 
                            message="Do you want to save this game?", 
                            icon="question", 
                            option_1="No", 
                            option_2="Yes", 
            )     
            response = msg.get()
            if response == "Yes":
                self.save_game()
        back_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Back", command=self.set_menu)
        back_button.grid(row=5, column=1, columnspan=2)
    
    def new_game(self):
        if self.playing:
            self.current_player = 3 - self.current_player
            self.game_over()
        self.unbind_keys()
        self.reset_board()
        self.start_game(self.ai_player != 0)

    def save_game(self):
        player_one_id = self.db.get_player_id(self.player_names[0].get())
        player_two_id = self.db.get_player_id(self.player_names[1].get())
        date_played = datetime.today().strftime('%Y-%m-%d')
        time_played = datetime.now().strftime('%H:%M:%S')
        game_id = self.db.add_game(player_one_id, player_two_id, self.current_player, self.grid_size.get(), date_played, time_played, self.num_moves)
        for move in range(self.num_moves + 1):
            pos = [[str(x) for x in row] for row in copy.deepcopy(self.move_history[move])]
            pos_string = ",".join(["".join(x) for x in pos])
            self.db.add_move(game_id, move + 1, pos_string)
        CTkMessagebox(title="Game Saved", 
                                message="Game has successfully been saved!", 
                                icon="check", 
                                option_1="Close")

    def set_in_play(self):
        if self.show_move == 0:
            self.beginning_button.configure(state="disabled")
            self.prev_move_button.configure(state="disabled")
        else:
            self.beginning_button.configure(state="normal")
            self.prev_move_button.configure(state="normal")

        if self.show_move == self.num_moves:
            self.end_button.configure(state="disabled")
            self.next_move_button.configure(state="disabled")
            self.in_play = True
        else:
            self.end_button.configure(state="normal")
            self.next_move_button.configure(state="normal")
            self.in_play = False

        if self.analysing:
            self.in_play = False
            if self.process:
                self.terminate_thread(self.process)
            self.best_move = []
            self.eval_label.grid_forget()
            self.best_move_button.grid(row=2, columnspan=4)
        
        self.draw_board()

    def beginning(self):
        self.show_move = 0
        self.set_in_play()
        
    def prev_move(self):
        if self.show_move != 0:
            self.show_move -= 1
        self.set_in_play()

    def next_move(self):
        if self.show_move < self.num_moves:
            self.show_move += 1
        self.set_in_play()

    def end(self):
        self.show_move = self.num_moves
        self.set_in_play()

    def undo(self):
        self.move_history.pop()
        self.board = copy.deepcopy(self.move_history[-1])
        self.num_moves -= 1
        if self.ai_player:
            self.move_history.pop()
            self.board = copy.deepcopy(self.move_history[-1])
            self.num_moves -= 1
        else:
            self.current_player = 3 - self.current_player
            self.info_string.set(self.player_names[self.current_player - 1].get() + "'s Turn")
        self.undo_button.configure(state="disabled")
        self.show_move = self.num_moves
        self.selected_piece = None
        self.last_move = None
        self.set_in_play()
        self.draw_board()

    def confirm(self):
        # In case key binding is triggered when confirm button disabled
        if self.confirm_button.cget("state") == "disabled":
            return None
        self.jumping = False
        self.confirm_button.configure(state="disabled")
        self.last_move = self.selected_piece
        self.switch_player()

    def on_closing(self):
        self.db.add_config(self.grid_size.get(), self.board_colours.get(), self.theme.get())
        self.db.close_con()
        self.root.destroy()

    def terminate_thread(self, thread):
        # Subroutine taken from https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread
        """Terminates a python thread from another thread.

        :param thread: a threading.Thread instance
        """
        if not thread.is_alive():
            return

        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), exc)
        if res == 0:
            raise ValueError("nonexistent thread id")
        elif res > 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
        
        
class ToplevelWindow(ctk.CTkToplevel):
    def __init__(self, value, BUTTON_HEIGHT, BUTTON_WIDTH, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Select Game")
        self.resizable(False, False)
        self.value = value
        self.BUTTON_HEIGHT = BUTTON_HEIGHT
        self.BUTTON_WIDTH = BUTTON_WIDTH
        self.db = DatabaseManager("halma.db")
        players = [""] + self.db.get_player_names()
        self.headers = ["ID", "Player One", "Player Two", "Result", "Board Size", "Date", "Time", "Number of Moves"]
        games = self.db.get_player_games(None)

        filter_label = ctk.CTkLabel(self, text="Filter By Player:")
        filter_label.grid(row=0)

        filtered_player = ctk.StringVar()
        player_filter = ctk.CTkOptionMenu(master=self, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH * 4, values=players, variable=filtered_player, command=self.filter)
        player_filter.grid(row=1)

        self.container = ctk.CTkFrame(self)
        self.container.grid(row=2)
        self.games_list = MultiColumnListbox(self.container, self.headers, games)

        submit_button = ctk.CTkButton(self, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="Analyse", command=self.submit)
        submit_button.grid(row=3)
        self.grab_set() # hijack all commands from the master (clicks on the main window are ignored)

    def submit(self):
        row = self.games_list.get_selected_row()
        if row:
            self.value.append(row["values"][0])
            self.destroy()
        else:
            msg = CTkMessagebox(title="No Game Selected!", 
                            message="Please select a game to analyse.", 
                            icon="warning", 
                            option_1="Ok")
            
            # Freeze main again after messagebox closes
            msg.get()
            self.grab_set()  

    def filter(self, player):
        self.container.destroy()
        games = self.db.get_player_games(player)
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=2)
        self.games_list = MultiColumnListbox(self.container, self.headers, games)
        

if __name__ == "__main__":
    root = ctk.CTk()
    halma_game = HalmaGame(root)
    root.mainloop()