j"""
This is a code modified by Unnar Thor Bachmann in Udacity full stack program.
The project is to design a game from Guess a number. I modified the code to
implement Blackjack. 
"""

"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""



import random
from datetime import date, datetime
from protorpc import messages
from google.appengine.ext import ndb

    
class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    n_games = ndb.FloatProperty(required = True,default = 0)
    winning_ratio = ndb.FloatProperty(required = True, default = 0)
    def to_form(self):
        """Returns a UserForm representation of the User"""
        form = UserForm()
        form.user_name = self.name
        form.winning_ratio = self.winning_ratio
        form.n_games = self.n_games
        return form
    


class Game(ndb.Model):
    """Game object"""
    user_hand = ndb.StringProperty(repeated=True)
    house_hand = ndb.StringProperty(repeated=True)
    deck = ndb.StringProperty(repeated=True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user_score = ndb.IntegerProperty(required=True, default=0)
    house_score = ndb.IntegerProperty(required=True, default=0)
    canceled = ndb.BooleanProperty(required=True, default=False)
    moves = ndb.StringProperty(repeated=True)
    msgs = ndb.StringProperty(repeated=True)
    user = ndb.KeyProperty(required=True, kind='User')
    # Datetime added to handle cron jobs.
    datetime = ndb.DateTimeProperty(required=True)
    result = ndb.StringProperty(required=True)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        """ Modified """
        hearts = ['H2', 'H3', 'H4','H5','H6','H7','H8','H9','H10', 'HJack', 'HQueen', 'HKing', 'HAce']
        spades = ['S2', 'S3', 'S4','S5','S6','S7','S8','S9','S10', 'SJack', 'SQueen', 'SKing', 'SAce']
        diamonds = ['D2', 'D3', 'D4','D5','D6','D7','D8','D9','D10', 'DJack', 'DQueen', 'DKing', 'DAce']
        clubs = ['C2', 'C3', 'C4','C5','C6','C7','C8','C9','C10', 'CJack', 'CQueen', 'CKing', 'CAce']
        deck = hearts + spades + diamonds + clubs
        # Each time a game is created it gets a randomly shuffled deck.
        random.shuffle(deck)

        # The user gets the first two cards and the house another two
        # The rest of the deck is for dealing.
        user_hand = deck[:2]
        house_hand = deck[2:4]
        deck = deck[4:]
        game = Game(user=user,
                    user_hand = user_hand,
                    house_hand = house_hand,
                    deck = deck,
                    user_score = 0,
                    house_score = 0,
                    moves = [],
                    msgs = [],
                    game_over = False,
                    canceled = False,
                    datetime = datetime.now(),
                    result = 'Undecided')
        game.update_user_score()
        game.update_house_score()
        game.put()
        return game
    
    def update_user_score(self):
        """ Updates user score """
        self.user_score = self.score_hand(self.user_hand)
        
    def update_house_score(self):
        """ Update house score"""
        self.house_score = self.score_hand(self.house_hand)
        

    def deal_to_user(self):
        """ deal a card to the user hand """
        self.user_hand.append(self.deck[0])
        self.deck = self.deck[1:]
        
    def deal_to_house(self):
        """ deal a card to the house hand"""
        self.house_hand.append(self.deck[0])
        self.deck = self.deck[1:]
        
    def score_hand(self,hand):
        """ Methods which scores hands 
        Jacks, queens and kings count as 10.
        Aces count as either 1 or 11.
        Other cards count as their face value.
        A hand is a sum of its cards.
        Returns the highest score-below 21 if possible.
        """
        total_score  = 0
        n_aces = 0
        # Initial counting. Count aces as 1.
        for card in hand:
            score = card[1:]
            if score.isdigit():
               total_score += int(score)
            elif score == 'Jack' or score == 'Queen' or score == "King":
                 total_score += 10
            else:
                total_score += 1
                n_aces += 1
                
        # While hand is below or equal to 21 add 10 for each ace.
        for i in range(n_aces):
            if 21-total_score < 10:
               break
            else:
                total_score += 10
        return total_score
        
    def end_game(self, result=0.5):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        """ Modified"""

        # Update the winning ratio and total of games played.
        user = self.user.get()
        n_games = user.n_games
        winning_ratio = user.winning_ratio
        winning_sum = n_games*winning_ratio
        winning_sum += result
        user.winning_ratio = winning_sum/(n_games + 1)
        user.n_games += 1
        user.put()

        self.game_over = True
        self.result = str(result)
        self.put()
        
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), result=result,
                      hand_score=self.score_hand(self.user_hand),
                      numb_cards = len(self.user_hand)
                      )
        score.put()
        # Assert if moves list and messages list are of same length.
            
        
    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.user_hand = ','.join(self.user_hand)
        # Displaying the house hand depending on the game status
        # Not displaying the second if game is still on.
        if self.game_over:
           form.house_hand = ','.join(self.house_hand)
        else:
            form.house_hand = self.house_hand[0] + ',' + 'XX'
        form.game_over = self.game_over
        form.message = message
        if len(self.msgs) != len(self.moves):
           self.msgs.append(message)
           
        self.put()
        print self.msgs
        print self.moves
        assert len(self.moves) == len(self.msgs)
  
        return form
    
    def to_history(self):
        """ Returns a HistoryForm representation of the game hitory """
        form = HistoryForm()
        form.urlsafe_key = self.key.urlsafe()
        form.player = self.user.get().name
        if self.game_over:             
           form.status = "Game is over"     
        else:
            if self.canceled:
               form.status = "Game is canceled"
            else: 
                form.status = "Game is not over"
                
        form.results = self.result
            
        form.moves = []
        # Each move stored in a MoveFom resource container.
        for i in range(len(self.moves)):
            form.moves.append(MoveForm(move = self.moves[i], message=self.msgs[i]))
            
        form.user_hand_init = ','.join(self.user_hand[:2])
        form.user_hand_end = ','.join(self.user_hand)

        # House hand not displayed fully if the game is still on.
        if self.game_over:
           form.house_hand_init = ','.join(self.house_hand[:2])
           form.house_hand_end = ','.join(self.house_hand)
        else:
            form.house_hand_init = self.house_hand[0] + ',' + 'XX'
            form.house_hand_end = self.house_hand[0] + ',' + 'XX'
        return form 

class MoveForm(messages.Message):
      """ Return for otubound Move information """
      move = messages.StringField(1, required=True)
      message = messages.StringField(2, required=True)
      
class HistoryForm(messages.Message):
      """ HistoryForm for outbound History information """
      urlsafe_key = messages.StringField(1, required=True)
      player = messages.StringField(2, required=True)
      status = messages.StringField(3, required=True)
      results = messages.StringField(4, required=True)
      moves = messages.MessageField(MoveForm, 5, repeated=True)
      user_hand_init = messages.StringField(6, required=True)
      house_hand_init = messages.StringField(7, required=True)
      user_hand_end = messages.StringField(8, required=True)
      house_hand_end = messages.StringField(9, required=True)
      
class Score(ndb.Model):
    """Score object"""
    """Modified"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    result = ndb.FloatProperty(required=True)
    hand_score = ndb.IntegerProperty(required=True)
    numb_cards = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, result=self.result,
                         date=str(self.date), hand_score = self.hand_score,
                         numb_cards = self.numb_cards)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    """ Modified """
    urlsafe_key = messages.StringField(1, required=True)
    user_hand = messages.StringField(2, required=True)
    house_hand = messages.StringField(3, required=True)
    game_over = messages.BooleanField(4, required=True)
    message = messages.StringField(5, required=True)
    user_name = messages.StringField(6, required=True)

class GameForms(messages.Message):
      items = messages.MessageField(GameForm,1,repeated=True)
      
class NewGameForm(messages.Message):
    """Used to create a new game"""
    """ Modified """
    user_name = messages.StringField(1, required=True)

class MakeMoveForm(messages.Message):
    hit_or_stand = messages.StringField(1, required=True)

class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    """ Modified """
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    result = messages.FloatField(3, required=True)
    hand_score = messages.IntegerField(4,required=True)
    numb_cards = messages.IntegerField(5,required=True)

      
class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class UserForm(messages.Message):
      """ Returns a username, winning ratio and games"""
      user_name = messages.StringField(1, required = True)
      winning_ratio = messages.FloatField(2, required = True)
      n_games = messages.FloatField(3, required = True)

class UserForms(messages.Message):
      """ Return multiple UserForm """
      items = messages.MessageField(UserForm,1,repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
