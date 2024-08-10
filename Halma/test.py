import copy
import threading
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import math
from PIL import Image, ImageTk
from module import DatabaseManager, MultiColumnListbox
from datetime import datetime
import ctypes

class ToplevelWindow(ctk.CTkToplevel):
    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Select Game")
        self.resizable(False, False)
        headers = ["Test1", "Test2"]
        games = [("FirstRowFirstCol", "FirstRowSecondCol"), ("SecondRowFirstCol", "SecondRowSecondCol")]

        filter_label = ctk.CTkLabel(self, text="Filter By Player:")
        filter_label.grid(row=0)

        filtered_player = ctk.StringVar()
        player_filter = ctk.CTkOptionMenu(master=self, height=25, width=200, variable=filtered_player)
        player_filter.grid(row=1)

        self.container = ctk.CTkFrame(self)
        self.container.grid(row=2)
        self.games_list = MultiColumnListbox(self.container, headers, games)

        submit_button = ctk.CTkButton(self, height=25, width=50, text="Analyse")
        submit_button.grid(row=3)

        self.grab_set() # hijack al the master (clicks on the main window are ignored)

class HalmaGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Halma Game")
        self.grid_size = 10
        self.cell_size = 70
        self.side = self.grid_size * self.cell_size

        # Open the piece images using PILLOW
        self.img = Image.open("red.png").resize((self.cell_size - 5, self.cell_size - 5), Image.LANCZOS)
        self.piece_one = ImageTk.PhotoImage(self.img)

        self.img = Image.open("blue.png").resize((self.cell_size - 5, self.cell_size - 5), Image.LANCZOS)
        self.piece_two = ImageTk.PhotoImage(self.img)

        # Create the game board
        self.board = [[0 for x in range(self.grid_size)] for y in range(self.grid_size)]
        self.selected_piece = None
        self.current_player = 1
        self.move_history = []

        self.player_one_positions = [
            (self.grid_size - 1, self.grid_size - 1),

            (self.grid_size - 1, self.grid_size - 2), (self.grid_size - 2, self.grid_size - 1),

            (self.grid_size - 1, self.grid_size - 3), (self.grid_size - 2, self.grid_size - 2), 
            (self.grid_size - 3, self.grid_size - 1),

            (self.grid_size - 1, self.grid_size - 4), (self.grid_size - 2, self.grid_size - 3), 
            (self.grid_size - 3, self.grid_size - 2), (self.grid_size - 4, self.grid_size - 1),
        ]

        self.player_two_positions = [
            (0, 0),
            (0, 1), (1, 0),
            (0, 2), (1, 1), (2, 0),
            (0, 3), (1, 2), (2, 1), (3, 0),
        ]

        for row, col in self.player_one_positions:
            self.board[row][col] = 1

        for row, col in self.player_two_positions:
            self.board[row][col] = 2
        ba = ToplevelWindow([])
        self.BUTTON_HEIGHT = 20
        self.BUTTON_WIDTH = 20

    def set_game_panel(self):
        self.clear_side_panel()

        player_two_label = ctk.CTkLabel(self.side_panel, text="Guest", anchor="nw")
        player_two_label.grid(row=0, columnspan=2, sticky="new")

        self.beginning_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="<<-")
        self.beginning_button.grid(row=1)

        self.prev_move_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="<-")
        self.prev_move_button.grid(row=1, column=1)

        self.next_move_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="->")
        self.next_move_button.grid(row=1, column=2)

        self.end_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="->>")
        self.end_button.grid(row=1, column=3)

        info_text = ctk.CTkLabel(self.side_panel, text="Arun's Turn", anchor="nw", bg_color="red")
        info_text.grid(row=2, columnspan=4, sticky="new")

        self.undo_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="⎌")
        self.undo_button.configure(state="disabled")
        self.undo_button.grid(row=3)

        self.confirm_button = ctk.CTkButton(self.side_panel, text="Confirm", height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH*2)
        self.confirm_button.configure(state="disabled")
        self.confirm_button.grid(row=3, column=1, columnspan=2)

        #New game
        self.new_button = ctk.CTkButton(self.side_panel, height=self.BUTTON_HEIGHT, width=self.BUTTON_WIDTH, text="+")
        self.new_button.grid(row=3, column=3)

        player_one_label = ctk.CTkLabel(self.side_panel, text="Arun", anchor="nw")
        player_one_label.grid(row=4, columnspan=2, sticky="new")

    # def draw_board(self):
    #     if True:
    #         position = self.board
    #     else:
    #         position = self.move_history[self.show_move]

    #     if self.selected_piece:
    #         valid_moves = self.show_valid_moves(position, self.selected_piece[0], self.selected_piece[1])
    #     else:
    #         valid_moves = []

    #     # Adjustment to centre images correctly
    #     image_adjustment = self.cell_size / 2
        
    #     for row in range(self.grid_size):
    #         for col in range(self.grid_size):
    #             x_start, y_start = col * self.cell_size, row * self.cell_size
    #             x_finish, y_finish = x_start + self.cell_size, y_start + self.cell_size
    #             colour = "yellow"

    #             if self.analysing and (row, col) in self.best_move:
    #                 self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.BEST_MOVE_COLOUR)
    #             elif (row, col) == self.selected_piece and self.in_play:
    #                 self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.HIGHLIGHT_COLOUR)
    #             elif (row, col) in valid_moves and self.in_play:
    #                 self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.VALID_MOVES_COLOUR)
    #             elif (row, col) == self.last_move and self.in_play:
    #                 self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.LAST_MOVE_COLOUR)
    #             elif (row, col) in (self.player_one_positions + self.player_two_positions):
    #                 self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=self.BASE_COLOUR)
    #             else:
    #                 self.canvas.create_rectangle(x_start, y_start, x_finish, y_finish, fill=colour)

    #             if position[row][col] == 1:
    #                 self.canvas.create_image(x_start + image_adjustment, y_start + image_adjustment, anchor="center", image=self.piece_one)
    #             elif position[row][col] == 2:
    #                 self.canvas.create_image(x_start + image_adjustment, y_start + image_adjustment, anchor="center", image=self.piece_two)

if __name__ == "__main__":
    root = ctk.CTk()
    halma_game = HalmaGame(root)
    root.mainloop()