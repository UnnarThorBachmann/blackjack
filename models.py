"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""
""" Modified by Unnar Thor Bachmann to play blackjack"""
import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

"""
class Move(messages.Enum):
      HIT = "hit"
      STAND = "stand"
"""      
class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""
    user_hand = ndb.StringProperty(repeated=True)
    house_hand = ndb.StringProperty(repeated=True)
    deck = ndb.StringProperty(repeated=True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user_score = ndb.IntegerProperty(required=True,default=0)
    house_score = ndb.IntegerProperty(required=True,default=0)
    user = ndb.KeyProperty(required=True, kind='User')

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        """ Modified """
        hearts = ['H2', 'H3', 'H4','H5','H6','H7','H8','H9','H10', 'HJack', 'HQueen', 'HKing', 'HAce']
        spades = ['S2', 'S3', 'S4','S5','S6','S7','S8','S9','S10', 'SJack', 'SQueen', 'SKing', 'SAce']
        diamonds = ['D2', 'D3', 'D4','D5','D6','D7','D8','D9','D10', 'DJack', 'DQueen', 'DKing', 'DAce']
        clubs = ['C2', 'C3', 'C4','C5','C6','C7','C8','C9','C10', 'CJack', 'CQueen', 'CKing', 'CAce']
        deck = hearts + spades + diamonds + clubs
        random.shuffle(deck)

        user_hand = deck[:2]
        house_hand = deck[2:4]
        deck = deck[4:]
        game = Game(user=user,
                    user_hand = user_hand,
                    house_hand = house_hand,
                    deck = deck,
                    user_score = 0,
                    house_score = 0,
                    game_over=False)
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
        """ Methods wich scores hands """
        total_score  = 0
        n_aces = 0
        for card in hand:
            score = card[1:]
            if score.isdigit():
               total_score += int(score)
            elif score == 'Jack' or score == 'Queen' or score == "King":
                 total_score += 10
            else:
                total_score += 1
                n_aces += 1

        for i in range(n_aces):
            if 21-total_score < 10:
               break
            else:
                total_score += 10
        return total_score
        
    
    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        """ Modified """
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.user_hand = ','.join(self.user_hand)
        if self.game_over:
           form.house_hand = ','.join(self.house_hand)
        else:
            form.house_hand = self.house_hand[0] + ',' + 'XX'
        form.game_over = self.game_over
        form.message = message
        return form

    def end_game(self, result=0.5):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        """ Modified"""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), result=result,
                      hand_score=self.score_hand(self.user_hand),
                      numb_cards = len(self.user_hand)
                      )
        score.put()


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


class NewGameForm(messages.Message):
    """Used to create a new game"""
    """ Modified """
    user_name = messages.StringField(1, required=True)



class MakeMoveForm(messages.Message):
    hit_or_stand = messages.StringField(1, required=True)

"""
class HitMoveForm(messages.Message):

      hit = messages.BooleanField(1,required=True)

class StandMoveForm(messages.Message):
      
      stand = messages.BooleanField(1,required=True)
"""
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


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)