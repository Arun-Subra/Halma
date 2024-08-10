import sqlite3
import tkinter as tk
import customtkinter as ctk
import tkinter.font as tkFont
import tkinter.ttk as ttk

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.con = None

    def create_con(self):
        if not self.con:
            try:
                self.con = sqlite3.connect(self.db_name)
            except Exception as e:
                print(e)
                return False
        return True
    
    def close_con(self):
        # Create a connection
        if self.con:
            self.con.close()
    
    def create_table(self, sql):
        # Create connection
        self.create_con()
        try:
            # Execute the query
            cursor = self.con.cursor()
            cursor.execute(sql)
        except Exception as e:
            print(e)
        # Save changes
        self.con.commit()

    def add_config(self, board_size, board_colours, theme):
        self.create_con()
        # Create query
        query = """INSERT INTO config(board_size, board_colours, theme) VALUES (?, ?, ?);"""
        # Execute query
        cursor = self.con.cursor()
        cursor.execute(query, (board_size, board_colours, theme))
        # Save changes
        self.con.commit()
    
    def configs_exist(self):
        self.create_con()
        # Create query
        query = """SELECT COUNT(*) FROM config"""
        # Execute query
        cursor = self.con.cursor()
        num = cursor.execute(query).fetchall()[0][0]
        # Return if any records exist
        return True if num else False
    
    def get_last_config(self):
        self.create_con()
        # Create query
        query = f"""SELECT board_size, board_colours, theme FROM config WHERE config_id=(SELECT MAX(config_id) FROM config);"""
        # Execute query
        cursor = self.con.cursor()
        config = cursor.execute(query).fetchall()[0]
        return config
    
    def player_exists(self, player_name):
        self.create_con()
        # Create query
        sql_get_player_names = """SELECT name FROM player;"""
        cursor = self.con.cursor()
        # Put all players into a list
        players = []
        for x in cursor.execute(sql_get_player_names).fetchall():
            players.append(x[0])
        # Check if the player name is in the list
        for name in players:
            if name == player_name:
                return True
        return False
    
    def get_player_id(self, player_name):
        self.create_con()
        # Create query
        query = f"""SELECT player_id FROM player WHERE name = '{player_name}';"""
        # Execute query
        cursor = self.con.cursor()
        id = cursor.execute(query).fetchall()[0][0]
        return id
    
    def get_player_name(self, id):
        self.create_con()
        # Create query
        query = f"""SELECT name FROM player WHERE player_id = '{id}';"""
        # Execute query
        cursor = self.con.cursor()
        name = cursor.execute(query).fetchall()[0][0]
        return name
    
    def add_player(self, player, ai):
        self.create_con()
        # Check if player name already used
        if not self.player_exists(player):
            # Set correct AI field value
            ai = 1 if ai else 0
            # Create query
            query = """INSERT INTO player(name, ai, active) VALUES (?, ?, 1);"""
            # Execute query
            cursor = self.con.cursor()
            cursor.execute(query, (player, ai))
            # Save changes
            self.con.commit()
            return True
        else:
            return False
    
    def disable_player(self, player_name):
        self.create_con()
        # Create query
        query = f"""UPDATE player
                    SET active = 0
                    WHERE
                        name = '{player_name}';"""
        # Execute query
        cursor = self.con.cursor()
        cursor.execute(query)
        # Save changes
        self.con.commit()
        
    def get_player_names(self):
        self.create_con()
        # Create query
        sql_get_player_names = """SELECT name FROM player WHERE ai = 0 AND active = 1;"""
        # Execute query
        cursor = self.con.cursor()
        # Add players to a list
        players = []
        for x in cursor.execute(sql_get_player_names).fetchall():
            players.append(x[0])
        return players
    
    def add_game(self, player_one_id, player_two_id, result, board_size, date_played, time_played, num_moves):
        self.create_con()
        # Put field values in a list
        values = [player_one_id, player_two_id, result, board_size, date_played, time_played, num_moves]
        # Create query
        query = """INSERT INTO game(player_one_id, player_two_id, result, board_size, date_played, time_played, num_moves) VALUES (?,?,?,?,?,?,?);"""
        # Execute query
        cursor = self.con.cursor()
        cursor.execute(query, values)
        # Save changes
        self.con.commit()
        # Return game id of the record just inserted
        return cursor.lastrowid
    
    def add_move(self, game_id, move_id, position):
        self.create_con()
        # Put field values in a list
        values = [game_id, move_id, position]
        # Create query
        query = """INSERT INTO move(game_id, move_id, position) VALUES (?,?,?);"""
        # Execute query
        cursor = self.con.cursor()
        cursor.execute(query, values)
        # Save changes
        self.con.commit()

    def get_player_games(self, player=None):
        self.create_con()
        # Check if a player name has been given to filter
        if player:
            # Get the id of the player
            id = self.get_player_id(player)
            # Create query
            query = f"""SELECT game_id, player_one.name as player_one_name, player_two.name as player_two_name, result, board_size, date_played, time_played, num_Moves
                        FROM game
                        JOIN player player_one on game.player_one_id = player_one.player_id
                        JOIN player player_two on game.player_two_id = player_two.player_id
                        WHERE player_one_id = '{id}' OR player_two_id = '{id}';"""
        else:
            # Create query
            query = """SELECT game_id, player_one.name as player_one_name, player_two.name as player_two_name, result, board_size, date_played, time_played, num_Moves
                        FROM game
                        JOIN player player_one on game.player_one_id = player_one.player_id
                        JOIN player player_two on game.player_two_id = player_two.player_id;"""
        # Execute query
        cursor = self.con.cursor()
        games = cursor.execute(query).fetchall()
        return games
    
    def get_game(self, id):
        self.create_con()
        # Create query
        query = f"""SELECT * FROM game WHERE game_id = '{id}';"""
        # Execute query
        cursor = self.con.cursor()
        game = cursor.execute(query).fetchall()[0]
        return game

    def get_moves(self, id):
        self.create_con()
        # Create query
        query = f"""SELECT position FROM move WHERE game_id={id} ORDER BY move_id ASC;"""
        # Execute query
        cursor = self.con.cursor()
        moves = cursor.execute(query).fetchall()
        return moves
            
    def get_number_games(self, id):
        self.create_con()
        # Create query
        query = f"""SELECT COUNT(*) FROM game WHERE player_one_id = {id} OR player_two_id = {id};"""
        # Execute query
        cursor = self.con.cursor()
        num = cursor.execute(query).fetchall()[0][0]
        return num
    
    def get_number_wins(self, id):
        self.create_con()
        # Create queries
        query_one = f"""SELECT COALESCE(SUM(result=1), 0) FROM game WHERE player_one_id = {id};"""
        query_two = f"""SELECT COALESCE(SUM(result=2), 0) FROM game WHERE player_two_id = {id};"""
        # Execute queries
        cursor = self.con.cursor()
        num = cursor.execute(query_one).fetchall()[0][0]
        num += cursor.execute(query_two).fetchall()[0][0]
        return num
    
    def get_average_moves(self, id):
        self.create_con()
        # Create query
        query = f"""SELECT COALESCE(AVG(num_moves), 0) FROM game WHERE player_one_id = {id} OR player_two_id = {id};"""
        # Execute query
        cursor = self.con.cursor()
        num = round(cursor.execute(query).fetchall()[0][0])
        return num

    def setup_tables(self):
        # Create table queries
        sql_create_game_table = """ CREATE TABLE IF NOT EXISTS game (
                                            game_id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                                            player_one_id integer NOT NULL,
                                            player_two_id integer NOT NULL,
                                            result integer NOT NULL,
                                            board_size integer NOT NULL,
                                            date_played text NOT NULL,
                                            time_played text NOT NULL,
                                            num_moves integer NOT NULL
                                        ); """
        
        sql_create_player_table = """ CREATE TABLE IF NOT EXISTS player (
                                            player_id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                                            name text NOT NULL,
                                            active integer NOT NULL,
                                            ai integer NOT NULL
                                        ); """
        
        sql_create_move_table = """ CREATE TABLE IF NOT EXISTS move (
                                            game_id integer NOT NULL,
                                            move_id integer NOT NULL,
                                            position text NOT NULL,
                                            PRIMARY KEY (game_id, move_id)
                                        ); """
        
        sql_create_config_table = """ CREATE TABLE IF NOT EXISTS config (
                                            config_id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                                            board_size integer NOT NULL,
                                            board_colours text NOT NULL,
                                            theme text NOT NULL
                                        ); """
        
        # Execute table queries
        self.create_table(sql_create_game_table)
        self.create_table(sql_create_player_table)
        self.create_table(sql_create_move_table)
        self.create_table(sql_create_config_table)

        # Add players
        self.add_player("Guest", False)
        self.add_player("AI Difficulty 1", True)
        self.add_player("AI Difficulty 2", True)
        self.add_player("AI Difficulty 3", True)
        self.add_player("AI Difficulty 4", True)
        self.add_player("AI Difficulty 5", True)

        # Add default configuration
        if not self.configs_exist():
            self.add_config(10, "Coral", "System")


class MultiColumnListbox:
    # Class taken from https://stackoverflow.com/questions/5286093/display-listbox-with-columns-using-tkinter

    def __init__(self, root, headers, lists):
        self.tree = None
        self.root = root
        self.headers = headers
        self.lists=lists

        self._setup_widgets()
        self._build_tree()
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("Treeview", background="gray17", 
                        fieldbackground=self.root.master.cget("bg"), fieldforeground="gray17", foreground="#3B8ED0")
        style.configure('Treeview.Heading', background="#3B8ED0")

    def _setup_widgets(self):
        container = ttk.Frame(self.root, )
        container.grid(sticky="nesw")
        # Modified this Treeview widget to only select one at a time (selectmode="browse")
        self.tree = ttk.Treeview(self.root, columns=self.headers, show="headings", selectmode="browse")
        vsb = ctk.CTkScrollbar(self.root, orientation="vertical",
            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=container)
        vsb.grid(column=1, row=0, sticky='ns', in_=container)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

    def _build_tree(self):
        for col in self.headers:
            self.tree.heading(col, text=col.title(),
                command=lambda c=col: self.sortby(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col, 
                             width=tkFont.Font().measure(col.title()))

        for item in self.lists:
            self.tree.insert('', 'end', values=item)
            # adjust column's width if necessary to fit each value
            for ix, val in enumerate(item):
                col_w = tkFont.Font().measure(val)
                if self.tree.column(self.headers[ix],width=None)<col_w:
                    self.tree.column(self.headers[ix], width=col_w)

    def sortby(self, tree, col, descending):
        """sort tree contents when a column header is clicked on"""
        # grab values to sort
        data = [(tree.set(child, col), child) \
            for child in tree.get_children('')]
        # if the data to be sorted is numeric change to float
        #data =  change_numeric(data)
        # now sort the data in place
        data.sort(reverse=descending)
        for ix, item in enumerate(data):
            tree.move(item[1], '', ix)
        # switch the heading so it will sort in the opposite direction
        tree.heading(col, command=lambda col=col: self.sortby(tree, col, \
            int(not descending)))
        
    def get_selected_row(self):
        selected = self.tree.focus()
        if selected:
            return self.tree.item(selected)
        else:
            return None