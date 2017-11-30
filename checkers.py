import os
os.environ['KIVY_TEXT'] = 'pil'
import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.properties import ListProperty, BooleanProperty, OptionProperty, StringProperty, BoundedNumericProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from simpletablelayout import SimpleTableLayout
from kivy.graphics import Ellipse

RED_PIECE = -1
RED_KING = -2
BLACK_PIECE = 1
BLACK_KING = 2
EMPTY = 0

class CheckersApp(App):
	def build(self):
		game = CheckersGame(rows=8, cols=8)
		game.initialize_board()
		return game

class CheckersTile(Button):
	possible_moves = []
	selected = None

	is_possible_move = BooleanProperty(False)
	piece = OptionProperty(EMPTY, options=[
		EMPTY,
		RED_PIECE,
		RED_KING,
		BLACK_PIECE,
		BLACK_KING])

	def __init__(self, **kwargs):
		super(CheckersTile, self).__init__(**kwargs)
		self.piece = kwargs.get('piece', EMPTY)

		if 'row' in kwargs and 'col' in kwargs:
			self.row = kwargs['row']
			self.col = kwargs['col'] 
		else:
			raise Exception('Please specify the position with the "row" and "col" arguments')

		if (self.row + self.col) % 2 == 0:
			self.background_color = [1,0,0,1]

	def is_black(self):
		return self.piece == BLACK_PIECE or self.piece == BLACK_KING
	def is_red(self):
		return self.piece == RED_PIECE or self.piece == RED_KING
	def is_empty(self):
		return self.piece == 0
	def is_king(self):
		return self.piece == BLACK_KING or self.piece == RED_KING

	def set_possible(self, possible):
		self.is_possible_move = possible
	def select(self, piece):
		self.is_selected = piece

	def empty_possible_moves(self):
		#unhighlight possible moves for previous piece
		for pos in CheckersTile.possible_moves:
			self.parent.cell(pos[0], pos[1]).set_possible(False)
		CheckersTile.possible_moves = []

	def on_press(self):
		super(CheckersTile, self).on_press()

		#selected a piece, show all possible moves
		if not self.is_possible_move:
			self.empty_possible_moves()

			# jumps, moves = self.parent.get_legal_moves(self.row, self.col, self.is_black)
			# CheckersTile.possible_moves = jumps if jumps else moves
			if self.parent.all_legal_moves == None:
				self.parent.all_legal_moves = self.parent.get_all_legal_moves()

			CheckersTile.possible_moves = self.parent.all_legal_moves.get((self.row, self.col), [])
			for move in CheckersTile.possible_moves:
				self.parent.cell(move[0], move[1]).set_possible(True)
			CheckersTile.selected = self

		else:
			piece_row = CheckersTile.selected.row
			piece_col = CheckersTile.selected.col
			self.parent.move_piece(piece_row, piece_col, self.row, self.col)
			self.empty_possible_moves()

	def on_is_possible_move(self, instance, possible):
		if possible:
			self.border = [0,0,0,0]
		else:
			self.border = [16,16,16,16]

	def on_piece(self, instance, piece):
		if piece == RED_PIECE:
			self.background_normal = 'red_piece.png'
		elif piece == BLACK_PIECE:
			self.background_normal = 'black_piece.png'
		elif piece == RED_KING:
			self.background_normal = 'red_king.png'
		elif piece == BLACK_KING:
			self.background_normal = 'black_king.png'
		else:
			self.background_normal = 'atlas://data/images/defaulttheme/button'
		
class CheckersGame(SimpleTableLayout):
	blacks_turn = BooleanProperty(True)
	red_pieces = ListProperty([])
	black_pieces = ListProperty([])
	all_legal_moves = None

	def initialize_board(self):
		for row in range(8):
			for col in range(8):
				if col < 3 and (row + col) % 2 == 1:
					self.add_widget(CheckersTile(row=row, col=col, piece=BLACK_PIECE))
					self.black_pieces.append((row, col))
				elif col >= 5 and col < 8 and (row + col) % 2 ==1:
					self.add_widget(CheckersTile(row=row, col=col, piece=RED_PIECE))
					self.red_pieces.append((row, col))
				else:
					self.add_widget(CheckersTile(row=row, col=col, game=self))

	def different_color(self, row1, col1, row2, col2):
		return self.get_piece(row1, col1) * self.get_piece(row2, col2) < 0

	def get_piece(self, row, col):
		return self.cell(row, col).piece

	def set_piece(self, row, col, piece):
		self.cell(row, col).piece = piece

	def has_empty(self, row, col):
		return self.cell(row, col).is_empty()

	def has_red(self, row, col):
		return self.cell(row, col).is_red()

	def has_black(self, row, col):
		return self.cell(row, col).is_black()

	def has_king(self, row, col):
		return self.cell(row, col).is_king()

	def get_possible_jumps(self, row, col):
		jumps = []
		jumps.append((row+2, col+2))
		jumps.append((row+2, col-2))
		jumps.append((row-2, col+2))
		jumps.append((row-2, col-2))
		return jumps

	def get_possible_nonjumps(self, row, col):
		nonjumps = []
		nonjumps.append((row+1, col+1))
		nonjumps.append((row+1, col-1))
		nonjumps.append((row-1, col+1))
		nonjumps.append((row-1, col-1))
		return nonjumps

	#helper function that determines if a move is legal
	def is_legal_move(self, start_row, start_col, end_row, end_col, blacks_turn):
		if abs(start_row - end_row) > 2 or abs(start_col - end_col) > 2:
			return False
		elif abs(start_row - end_row) != abs(start_col - end_col):
			return False
		elif end_row > 7 or end_row < 0 or end_col > 7 or end_col < 0:
			return False
		elif self.has_red(start_row, start_col) and blacks_turn:
			return False
		elif self.has_black(start_row, start_col) and not blacks_turn:
			return False

		#jumping
		elif abs(end_col - start_col) == 2:
			mid_row = (start_row + end_row) / 2
			mid_col = (start_col + end_col) / 2

			jumpable = self.different_color(start_row, start_col, mid_row, mid_col)

			if self.has_king(start_row, start_col):
				right_direction = True
			elif self.has_black(start_row, start_col):
				right_direction = end_col > start_col
			else:
				right_direction = start_col > end_col

			return jumpable and right_direction and self.has_empty(end_row, end_col)

		#moving
		else:
			if self.has_king(start_row, start_col):
				right_direction = True
			elif self.has_black(start_row, start_col):
				right_direction = end_col > start_col
			else:
				right_direction = start_col > end_col

			return right_direction and self.has_empty(end_row, end_col)

	#returns an array of tuples indicating legal positions to move to
	def get_legal_moves(self, row, col, blacks_turn):
		if self.has_empty(row, col):
			return [], []
		
		possible_jumps = self.get_possible_jumps(row, col)
		jumps = filter(lambda pos : self.is_legal_move(
			row, col, pos[0], pos[1], blacks_turn), possible_jumps)

		possible_nonjumps = self.get_possible_nonjumps(row, col)

		nonjumps = filter(lambda pos : self.is_legal_move(
			row, col, pos[0], pos[1], blacks_turn), possible_nonjumps)

		return jumps, nonjumps

	def get_all_legal_moves(self):
		all_jumps = {}
		all_moves = {}
		pieces = self.black_pieces if self.blacks_turn else self.red_pieces
		
		for start_row, start_col in pieces:
			jumps, moves = self.get_legal_moves(start_row, start_col, self.blacks_turn)
			if jumps:
				all_jumps[(start_row, start_col)] = jumps
			if moves:
				all_moves[(start_row, start_col)] = moves
		
		return all_jumps if all_jumps else all_moves

	#PRECONDITION: move is valid
	def move_piece(self, start_row, start_col, end_row, end_col):
		if self.has_black(start_row, start_col):
			my_pieces = self.black_pieces
			opponent_pieces = self.red_pieces
		elif self.has_red(start_row, start_col):
			my_pieces = self.red_pieces
			opponent_pieces = self.black_pieces

		self.set_piece(end_row, end_col, self.get_piece(start_row, start_col))
		my_pieces.append((end_row, end_col))

		if abs(start_row - end_row) == 2: # jump
			mid_row = (start_row + end_row) / 2
			mid_col = (start_col + end_col) / 2

			self.set_piece(mid_row, mid_col, EMPTY)
			opponent_pieces.remove((mid_row, mid_col))

		self.set_piece(start_row, start_col, EMPTY)
		my_pieces.remove((start_row, start_col))

		if self.has_black(end_row, end_col) and end_col == 7:
			self.make_king(end_row, end_col)
		elif self.has_red(end_row, end_col) and end_col == 0:
			self.make_king(end_row, end_col)

		jumps, _ = self.get_legal_moves(end_row, end_col, self.has_black(end_row, end_col))
		if jumps and abs(start_row - end_row) == 2:
			self.all_legal_moves = {(end_row, end_col) : jumps}
		else:
			self.all_legal_moves = None
			self.blacks_turn = not self.blacks_turn

	def make_king(self, row, col):
		if self.has_black(row, col):
			self.set_piece(row, col, BLACK_KING)
		else:
			self.set_piece(row, col, RED_KING)

	def cell(self, row, col):
		return self._grid[row][col]

	def create_victory_screen(self, black_won):
		if black_won:
			text = 'Black Wins!'
		else:
			text = 'Red Wins!'
		victory_screen = Popup(title='Victory!',
		    content=Label(text=text),
		    size_hint=(None, None), size=(400, 400))
		return victory_screen

	def on_black_pieces(self, instance, pieces):
		if len(pieces) == 0:
			victory_screen = self.create_victory_screen(False)
			victory_screen.open()

	def on_red_pieces(self, instance, pieces):
		if len(pieces) == 0:
			victory_screen = self.create_victory_screen(True)
			victory_screen.open()

if __name__ == '__main__':
	CheckersApp().run()
