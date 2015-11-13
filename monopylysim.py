#  Monopoly play simulator for finding probabilities of various game eventualities

from random import randrange, shuffle

class Simulator:
	def __init__(self, 
			circles	          = 1000, 	# number of times to passing Go to simulate
			jail_sim          = True, 	# simulate landing on going to jail on space 33
			jail_escape_strat = 1,		# strategy for escaping jail: 1=try for doubles 3 times, 2=always buy out
			chance_sim        = True,	# simiulate chance cards
			cmtchest_sim      = True):	# simulate community chest cards

		self.circles           = circles
		self.jail_sim          = jail_sim
		self.jail_escape_strat = jail_escape_strat
		self.chance_sim        = chance_sim
		self.cmtchest_sim      = cmtchest_sim

		# Sim vars
		self.board_size     = 40	# standard Monopoly board size
		self.player_pos     = 1 	# start on 'Go'
		self.dbls_in_row    = 0		# 3 doubles in a row = got to jail
		self.player_in_jail = False
		self.has_GOOJF      = False	# Get out of jail free
		self.dbls_attmpts   = 0		# attempts to get out jail

		self.chance   = Chance()
		self.cmtchest = CmtChest()
		
		# Result vars
		self.land_ons       = {}
		self.turn_count     = 0
		self.circ_count     = 0
		self.times_in_jail  = 0
		self.turns_in_jail  = 0
		
		self.chance_cards_drawn   = 0
		self.cmtchest_cards_drawn = 0

	def runSim(self):
		while True:
			if self.circ_count >= self.circles:	# end simulation
				break
			else:
				self.takeTurn()
		
		# Make land on percentages
		land_percs = {}
		for key in self.land_ons:
			land_percs[key] = self.land_ons[key]/self.circ_count*100

		return {'circ_count':           self.circ_count,
			'turn_count':           self.turn_count,
			'avg_turns_per_circ':   self.turn_count/self.circ_count,
		        'land_ons':             self.land_ons,
		        'land_percs':           land_percs,
	       	        'times_in_jail':        self.times_in_jail,
		        'turns_in_jail':        self.turns_in_jail,
		        'chance_cards_drawn':   self.chance_cards_drawn,
		        'cmtchest_cards_drawn': self.cmtchest_cards_drawn}

	def takeTurn(self):
		self.turn_count += 1
		if not self.player_in_jail:	
			d1, d2 = self.rollDice()
			if d1==d2:			# rolled doubles
				self.dbls_in_row += 1
			if self.dbls_in_row == 3:
				self.dbls_in_row == 0
				self.goToJail()
			if not self.player_in_jail:	# still not in jail after roll?
				dice_roll = d1+d2
				if self.player_pos + dice_roll > self.board_size:
					self.circ_count += 1
					self.player_pos = (self.player_pos + dice_roll) - self.board_size    	# pass 'Go'
				else:
					self.player_pos += dice_roll
				self.processPos()
		else:
			self.jailTurn()

	def processPos(self):
		if self.player_pos in self.land_ons.keys():
			self.land_ons[self.player_pos] += 1		# record number of times landed here
		else:
			self.land_ons[self.player_pos] = 1	
		if self.player_pos == 31 and self.jail_sim == True: 		# go to jail
			self.goToJail()
		elif self.player_pos in self.chance.positions and self.chance_sim == True:
			self.chance_cards_drawn += 1
			self.chance.draw()(self)
		elif self.player_pos in self.cmtchest.positions and self.cmtchest_sim == True:
			self.cmtchest_cards_drawn += 1
			self.cmtchest.draw()(self)

	def jailTurn(self):
		self.turns_in_jail += 1
		if self.has_GOOJF:		# always use get out of jail free card
			self.player_in_jail = False
			# make sure we only return one
			if self.chance.GOOJF_in == False:
				self.chance.returnGoojf()
			else:
				self.cmtchest.returnGoojf()
			if self.chance.GOOJF_in == True and self.cmtchest.GOOJF_in == True:
				self.has_GOOJF = False
		elif self.jail_escape_strat == 1:			# roll for doubles
			d1, d2 = self.rollDice()
			if d1 == d2:
				self.player_in_jail = False
			else:
				self.dbls_attmpts += 1
				if self.dbls_attmpts == 3:
					self.player_in_jail = False	# have to buy way out after 3 rolls
		elif self.jail_escape_strat == 2:
			self.player_in_jail = False			# buy way out

	def goToJail(self):
		# Doesn't pass Go
		self.player_in_jail = True
		self.times_in_jail += 1
		self.dbls_attmpts   = 0
		self.player_pos     = 11
		self.processPos()

	def rollDice(self):
		return (randrange(1,7), randrange(1,7))


class Cards:
	def __init__(self):
		self.cards = [self.advToGo,
				self.GOOJF,
				self.goToJail]
		self.GOOJF_in  = True

	def shuffle(self):
		shuffle(self.cards)

	def draw(self):
		card = self.cards.pop()			# take card from top
		if card != self.GOOJF:			# player keeps get out of jail free
			self.cards.insert(0, card)	# place at bottom
		else:
			self.GOOJF_in = False
		return card

	def returnGoojf(self):
		if not self.GOOJF_in:
			self.cards.insert(0, self.GOOJF)	# return to bottom of stack
			self.GOOJF_in = True

	def advToGo(self, sim):
		"Advance to go. (Collect $200)"
		sim.circ_count += 1
		sim.player_pos = 1
		sim.processPos()
	def goToJail(self, sim):
		"Go directle to jail. Do not pass Go, do not collect $200"
		sim.goToJail()
	def GOOJF(self, sim):
		"This card may be kept until needed, or sold.  Get out of jail free."
		sim.has_GOOJF = True


class Chance(Cards):
	def __init__(self):
		Cards.__init__(self)
		self.cards += [self.loanMatures,
				self.goBack3,
				self.advToBrdwlk,
				self.advToIlls,
				self.advToRR,
				self.advToRR,
				self.poorTax,
				self.advToReading,
				self.bankDvd,
				self.advToGo,
				self.elctChair,
				self.advToUtility,
				self.makeRepairs,
				self.GOOJF,
				self.advToStChrls,
				self.goToJail]
		self.positions = [8, 23, 37]
		self.shuffle()

	### Cards.  sim = Simulator instance
	def loanMatures(self, sim):
		"Your building and loan matures. Collect $150"
		# Not implemented
		pass
	def goBack3(self, sim):
		"Go back 3 spaces"
		sim.player_pos -= 3
		sim.processPos()
	def advToBrdwlk(self, sim):
		"Take a walk on the boardwalk. Advance token to Boardwalk."
		sim.player_pos = 40
		sim.processPos()
	def advToIlls(self, sim):
		"Advance to Illinois Ave."
		if sim.player_pos > 25:
			sim.circ_count += 1   # passed Go
		sim.player_pos = 25
		sim.processPos()
	def advToRR(self, sim):
		"""Advance token to the nearest Railroad and pay owner Twice the 
		   Rental to which he/she is otherwise entitled. 
		   If Railroad is UNOWNED, you may buy it from the Bank."""
		if sim.player_pos == self.positions[2]:
			sim.circ_count += 1
			sim.player_pos = 6
		elif sim.player_pos == self.positions[0]:
			sim.player_pos = 16
		elif sim.player_pos == self.positions[1]:
			sim.player_pos = 26
		# NOTE: Reaching Short Line RR is impossible with this card
		# due to the placement of Chance spaces
		sim.processPos()
	def poorTax(self, sim):
		"Pay poor tax of $15"
		# Not implemented
		pass
	def advToReading(self, sim):
		"Take a ride on the reading. If you pass Go collect $200."
		# Card says 'If' but Go is always passed
		sim.circ_count += 1
		sim.player_pos = 6
		sim.processPos()
	def bankDvd(self, sim):
		"Bank pays you dividend of $50"
		# Not implemented
		pass
	def elctChair(self, sim):
		"You have been elected chairman of the board. Pay each player $50."
		# Not implemented
		pass
	def advToUtility(self, sim):
		"""Advance token to nearest utility.
		   If UNOWNED you may buy it from the bank.
		   If OWNED, throw dice and pay owner a total ten times the amount thrown"""
		if sim.player_pos in (self.positions[0], self.positions[2]):
			sim.player_pos = 13
		else:
			sim.player_pos = 29
		sim.processPos()
	def makeRepairs(self, sim):
		"""Make general repairs on all property.
		   For each house pay $25.
		   For each hotel $100."""
		# Not implemented
		pass
	def advToStChrls(self, sim):
		"Advance to St. Charles Place. If you pass Go, collect $200."
		if sim.player_pos in (self.positions[1], self.positions[2]):
			sim.circ_count += 1
		sim.player_pos = 12
		sim.processPos()


class CmtChest(Cards):
	def __init__(self):
		Cards.__init__(self)
		# Since money isn't implemented yet, let's save some time
		self.cards += [self.moneyCard]*13

		self.positions = [3, 18, 34]
		self.shuffle()
	
	def moneyCard(self, sim):
		# Money not implemented
		pass
