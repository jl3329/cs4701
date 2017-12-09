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
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Ellipse
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.modalview import ModalView
import random
import csv

RED_PIECE = -1
RED_KING = -2
BLACK_PIECE = 1
BLACK_KING = 2
EMPTY = 0

class CheckersApp(App):
	def build(self):
		game = CheckersGame(rows=8, cols=8)
		# menu = game.create_menu()
		# menu.open()
		game.AIvAI = True
		# game.random = True
		# game.more_random = True
		game.initialize_board(None)
		game.cell(0,0).on_press()
		self.game = game
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
		if 'game' in kwargs:
			self.game = kwargs['game']

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

		if self.parent.AIvAI:
			if self.parent.more_random:
				self.parent.random_move()
			else:
				self.parent.smart_move()
			return

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

iterations = 0
max_iterations = 85

class CheckersGame(SimpleTableLayout):
	blacks_turn = BooleanProperty(True)
	red_pieces = ListProperty([])
	black_pieces = ListProperty([])
	red_kings = ListProperty([])
	black_kings = ListProperty([])
	all_legal_moves = None
	red_won = BooleanProperty(False)
	black_won = BooleanProperty(False)
	HvH = False
	HvAI = False
	AIvAI = False
	random = False
	more_random = False
	minimaxing = False
	AI = False
	

	def create_menu(self):
		box = BoxLayout(orientation='vertical')
		b1 = Button(text='Human vs Human')
		b1.bind(on_press=self.setup)
		b1.bind(on_press=self.initialize_board)
		box.add_widget(b1)
		b2 = Button(text='Human vs Random AI')
		b2.bind(on_press=self.setup)
		b2.bind(on_press=self.initialize_board)
		box.add_widget(b2)
		b3 = Button(text='Human vs Smart AI')
		b3.bind(on_press=self.setup)
		b3.bind(on_press=self.initialize_board)
		box.add_widget(b3)
		b4 = Button(text='Random AI vs Random AI')
		b4.bind(on_press=self.setup)
		b4.bind(on_press=self.initialize_board)
		box.add_widget(b4)
		b5 = Button(text='Random AI vs Smart AI')
		b5.bind(on_press=self.setup)
		b5.bind(on_press=self.initialize_board)
		box.add_widget(b5)
		b6 = Button(text='Smart AI vs Smart AI')
		b6.bind(on_press=self.setup)
		b6.bind(on_press=self.initialize_board)
		box.add_widget(b6)
		menu = Popup(title='Minimax Checkers',
		    content=box,
		    size_hint=(None, None), size=(400, 400),
		    auto_dismiss=False)
		b1.bind(on_press=menu.dismiss)
		b2.bind(on_press=menu.dismiss)
		b3.bind(on_press=menu.dismiss)
		b4.bind(on_press=menu.dismiss)
		b5.bind(on_press=menu.dismiss)
		b6.bind(on_press=menu.dismiss)
		return menu

	def setup(self, instance):
		if instance.text == 'Human vs Human':
			self.HvH=True
		elif instance.text == 'Human vs Random AI':
			self.HvAI=True
			self.random=True
		elif instance.text == 'Human vs Smart AI':
			self.HvAI=True
		elif instance.text == 'Random AI vs Random AI':
			self.AIvAI=True
			self.random=True
			self.more_random=True
		elif instance.text == 'Random AI vs Smart AI':
			self.AIvAI=True
			self.random=True
		elif instance.text == 'Smart AI vs Smart AI':
			self.AIvAI=True

	def board_visual(self):
		b = ''
		for x in range(8):
			for y in range(8):
				b = b + (' o ' if (x,y) in self.black_pieces else (' x ' if (x,y) in self.red_pieces else ' . '))
			b = b + '\n'	
		print(b)

	def initialize_board(self, instance):
		for row in range(8):
			for col in range(8):
				if col < 3 and (row + col) % 2 == 1:
					if not self.minimaxing:
						self.add_widget(CheckersTile(row=row, col=col, piece=BLACK_PIECE))
					self.black_pieces.append((row, col))
				elif col >= 5 and col < 8 and (row + col) % 2 ==1:
					if not self.minimaxing:
						self.add_widget(CheckersTile(row=row, col=col, piece=RED_PIECE))
					self.red_pieces.append((row, col))
				else:
					if not self.minimaxing:
						self.add_widget(CheckersTile(row=row, col=col, game=self))
		self.do_layout()

	def different_color(self, row1, col1, row2, col2):
		return ((row1, col1) in self.black_pieces and (row2, col2) in self.red_pieces) or ((row1, col1) in self.red_pieces and (row2, col2) in self.black_pieces)
		#return self.get_piece(row1, col1) * self.get_piece(row2, col2) < 0

	def get_piece(self, row, col):
		return self.cell(row, col).piece

	def set_piece(self, row, col, piece):
		self.cell(row, col).piece = piece

	def has_empty(self, row, col):
		return (row, col) not in self.black_pieces and (row, col) not in self.red_pieces
		#return self.cell(row, col).is_empty()

	def has_red(self, row, col):
		return (row, col) in self.red_pieces
		#return self.cell(row, col).is_red()

	def has_black(self, row, col):
		return (row, col) in self.black_pieces
		#return self.cell(row, col).is_black()

	def has_king(self, row, col):
		return (row, col) in self.black_kings or (row, col) in self.red_kings
		#return self.cell(row, col).is_king()

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

		if not all_jumps and not all_moves and not self.minimaxing:
			if self.blacks_turn:
				self.red_won = True
			else:
				self.black_won = True
		return all_jumps if all_jumps else all_moves

	#PRECONDITION: move is valid
	def move_piece(self, start_row, start_col, end_row, end_col):
		if self.has_black(start_row, start_col):
			my_pieces = self.black_pieces
			opponent_pieces = self.red_pieces
			my_kings = self.black_kings
			opponent_kings = self.red_kings
		elif self.has_red(start_row, start_col):
			my_pieces = self.red_pieces
			opponent_pieces = self.black_pieces
			my_kings = self.red_kings
			opponent_kings = self.black_kings

		if not self.minimaxing:
			self.set_piece(end_row, end_col, self.get_piece(start_row, start_col))
		my_pieces.append((end_row, end_col))
		if (start_row, start_col) in my_kings:
			my_kings.append((end_row, end_col))

		if not self.minimaxing:
			self.set_piece(start_row, start_col, EMPTY)
		my_pieces.remove((start_row, start_col))
		if (start_row, start_col) in my_kings:
			my_kings.remove((start_row, start_col))

		if self.has_black(end_row, end_col) and end_col == 7 and not self.has_king(end_row, end_col):
			if not self.minimaxing:
				self.make_king(end_row, end_col)
			self.black_kings.append((end_row, end_col))

		elif self.has_red(end_row, end_col) and end_col == 0 and not self.has_king(end_row, end_col):
			if not self.minimaxing:
				self.make_king(end_row, end_col)
			self.red_kings.append((end_row, end_col))

		if abs(start_row - end_row) == 2: # jump
			mid_row = (start_row + end_row) / 2
			mid_col = (start_col + end_col) / 2

			if (mid_row, mid_col) in my_kings:
				my_kings.remove((mid_row, mid_col))
			if (mid_row, mid_col) in opponent_kings:
				opponent_kings.remove((mid_row, mid_col))

			if not self.minimaxing:
				self.set_piece(mid_row, mid_col, EMPTY)
			opponent_pieces.remove((mid_row, mid_col))
			

		jumps, _ = self.get_legal_moves(end_row, end_col, self.has_black(end_row, end_col))
		if jumps and abs(start_row - end_row) == 2:
			self.all_legal_moves = {(end_row, end_col) : jumps}
			if (self.AIvAI or self.HvAI) and self.AI and not self.minimaxing:
				self.move_piece(end_row, end_col, jumps[0][0], jumps[0][1])
		else:
			self.all_legal_moves = None
			self.blacks_turn = not self.blacks_turn

		if self.AIvAI and not self.minimaxing:
			self.board_visual()
			if self.more_random:
				self.random_move()
			elif not self.blacks_turn or self.random == False:
				self.smart_move()
			else:
				self.random_move()

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

	def on_black_won(self, instance, black_victory):
		if black_victory:
			# self.create_victory_screen(True).open()

			with open('smart_vs_smart.csv', 'ab') as f:
				writer = csv.writer(f)
				writer.writerow([0, len(self.black_pieces), len(self.black_kings), len(self.red_pieces), len(self.red_kings)])
			quit()

	def on_red_won(self, instance, red_victory):
		if red_victory:
			# self.create_victory_screen(False).open()

			with open('smart_vs_smart.csv', 'ab') as f:
				writer = csv.writer(f)
				writer.writerow([1, len(self.black_pieces), len(self.black_kings), len(self.red_pieces), len(self.red_kings)])

			quit()



	def on_black_pieces(self, instance, pieces):
		if len(pieces) == 0 and not self.minimaxing:
			# victory_screen = self.create_victory_screen(False)
			# victory_screen.open()
			self.red_won = True

	def on_red_pieces(self, instance, pieces):
		if len(pieces) == 0 and not self.minimaxing:
			# victory_screen = self.create_victory_screen(True)
			# victory_screen.open()
			self.black_won = True

	def random_move(self):
		print 'random'
		if self.get_all_legal_moves():
			print(self.blacks_turn)
			start_move = random.choice(self.get_all_legal_moves().keys())
			end_move = random.choice(self.get_all_legal_moves().get(start_move))
			self.AI = True
			self.move_piece(start_move[0],start_move[1],end_move[0],end_move[1])
			self.AI = False

	def smart_move(self):
		print 'smart'
		if self.get_all_legal_moves():
			m = Minimax(6)
			best_move = Minimax.start(m,self)
			if best_move == None:
				self.random_move()
			else:
				self.minimaxing = False
				self.AI = True
				self.move_piece(best_move[0],best_move[1],best_move[2],best_move[3])
				self.AI = False

class Minimax():

	def __init__(self, depth):
		self.depth = depth

	def copy_board(self,board):
		new_board = CheckersGame(rows=8, cols=8)
		new_board.minimaxing = True
		new_board.initialize_board(new_board)
		new_board.red_pieces = board.red_pieces
		new_board.black_pieces = board.black_pieces
		new_board.red_kings = board.red_kings
		new_board.black_kings = board.black_kings
		new_board.blacks_turn = board.blacks_turn
		return new_board

	def evaluate(self,board):
		if board.blacks_turn:
			return len(board.black_pieces) - len(board.red_pieces)
		return len(board.red_pieces) - len(board.black_pieces)
			# return len(board.black_pieces) + len(board.black_kings) - len(board.red_pieces) - len(board.red_kings)
		# return len(board.red_pieces) + len(board.red_kings) - len(board.black_pieces) - len(board.black_kings)

	def negamax(self,board,depth,alpha,beta):
		if depth==0:
			return self.evaluate(board)
		moves = board.get_all_legal_moves()
		best_score = -1000
		localalpha = alpha
		if board.black_won or board.red_won:
			return -100
		for start in moves:
			for end in moves.get(start):
				new_board = self.copy_board(board)
				new_board.move_piece(start[0],start[1],end[0],end[1])
				new_score = -self.negamax(new_board, depth - 1, -beta, -localalpha)
				best_score = max(new_score, best_score)
				if best_score >= beta:
					return best_score
				if best_score > localalpha:
					localalpha = best_score
				
		return best_score

	def start(self,board):
		alpha = -100
		best_move = None
		moves = board.get_all_legal_moves()
		for start in moves:
			for end in moves.get(start):
				new_board = self.copy_board(board)
				new_board.move_piece(start[0],start[1],end[0],end[1])
				new_score = -self.negamax(new_board, self.depth - 1, alpha, -alpha)
				print(new_score)
				if new_score > alpha:
					alpha = new_score
					best_move = (start[0],start[1],end[0],end[1])
		return best_move

if __name__ == '__main__':
	CheckersApp().run()

