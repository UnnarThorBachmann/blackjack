# -*- coding: utf-8 -*-`
"""
This is a code modified by Unnar Thor Bachmann in Udacity full stack program.
The project is to design a game from Guess a number. I modified the code to
implement Blackjack. 
"""

"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


from datetime import datetime
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import (StringMessage,
                    NewGameForm,
                    GameForm,
                    MakeMoveForm,
                    ScoreForms,
                    GameForms,
                    UserForms,
                    HistoryForm)
from utils import get_by_urlsafe


# Resource containers.
NUMBER_REQUEST = endpoints.ResourceContainer(
    number_of_results = messages.IntegerField(1),)
            
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)


MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)

MEMCACHE_SCORES_REMAINING = 'SCORES_REMAINING'

@endpoints.api(name='blackjack', version='v1')
class BlackjackApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                    response_message=StringMessage,
                    path='user',
                    name='create_user',
                    http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
       
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game """
        
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key)
        except ValueError:
            raise endpoints.BadRequestException('Error in creating a game')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Blackjack!')

    @endpoints.method(request_message=GAME_REQUEST,
    	response_message=GameForm,
        path='game/{urlsafe_game_key}',
        name='get_game',
        http_method='GET')
    def get_game(self, request):
        """ Return the current game state."""
        """ Motified """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
            	return game.to_form("Game is over")
            else:
            	return game.to_form('Hit or stand!')
        else:
        	raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GAME_REQUEST,
    	response_message=GameForm,
        path='cancel/{urlsafe_game_key}',
        name='cancel_game',
        http_method='PUT')
    def cancel_game(self, request):
    	""" Cancels a game. Returns a game state wit cancel message."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # Raises exception if game is already over.
        if game.game_over:
        	raise endpoints.ForbiddenException('Game is already over.')
        
        game.canceled = True
        game.put()
        return game.to_form('Game is canceled')
    
    @endpoints.method(request_message=GAME_REQUEST,
                    response_message=GameForm,
                    path='resume/{urlsafe_game_key}',
                    name='resume_game',
                    http_method='PUT')
    def resume_game(self, request):
    	""" Resumes a game. Returns a game state wit hit or stand message."""
        game = get_by_urlsafe(request.urlsafe_game_key,Game)
        # Raises exception if game is already over.
        if game.game_over:
        	raise endpoints.ForbiddenException('Game is already over.')
              
        game.canceled = False
        game.put()
        return game.to_form('Hit or stand?')
    @endpoints.method(request_message=GAME_REQUEST,
    	response_message=HistoryForm,
        path='history/{urlsafe_game_key}',
        name='get_game_history',
        http_method='GET')
    def get_game_history(self, request):
        """ Returns the history of a game"""
        game = get_by_urlsafe(request.urlsafe_game_key,Game)
        return game.to_history()
    
    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
    	response_message=GameForm,
        path='move/{urlsafe_game_key}',
        name='make_move',
        http_method='PUT')
    def make_move(self, request):
        """ Makes a move. Returns a game state with message
            User can either hit or stand. Hit is a request for
            another card while stand is a request for no more cards
            during the game.
        """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        # Raises exception if either games is over or canceled.
        if game.game_over:
        	raise endpoints.ForbiddenException('Game is already over.')
        
        if game.game_over:
        	raise endpoints.ForbiddenException('Game is canceled.') 
        
        if request.hit_or_stand == 'hit':
        	game.moves.append('hit')
        	game.deal_to_user()
        	game.update_user_score()
        	game.put()

        	# If the user gets busted it is an automatic loss.
                if game.user_score <= 21:
                    return game.to_form('Hit or deal?')
                else:
                    game.end_game(0.0)
                    return game.to_form('You are busted.')
            
        elif request.hit_or_stand == 'stand':
            game.moves.append('stand')
            
            # The house has the strategy of automatically
            # request a card while the value of the hand is below 17.
            while game.house_score < 17:
            	game.deal_to_house()
            	game.update_house_score()
                  
            # Check if the house is busted.
            # If so the user wins.
            # Else the higher scoring hand wins.
            if game.house_score > 21:
            	game.end_game(1.0)
               
            	return game.to_form('The house got busted.')
             
            elif game.user_score > game.house_score:
            	game.end_game(1.0)
                
            	return game.to_form('You win')
                
            elif game.user_score < game.house_score:
            	game.end_game(0.0)
            	return game.to_form('You lose!')
            else:
            	game.end_game(0.5)
                return game.to_form('Draw!')
        else:
        	# If the request is neither hit or stand the game state is returned
            # with instructions on playing the game.
            return game.to_form('Either hit or stand. No other moves available.')
    @endpoints.method(response_message=ScoreForms,
    	path='scores',
        name='get_scores',
        http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
       
        return ScoreForms(items=[score.to_form() for score in Score.query()])
    
    @endpoints.method(request_message=NUMBER_REQUEST,
    	response_message=ScoreForms,
        path='get_high_scores',
        name='get_high_scores',
        http_method='GET')
    def get_high_scores(self,request):
        """ Returns highest scores. Ties broken with number of cards."""
        scores = Score.query()
        scores = scores.order(-Score.result)
        scores = scores.order(-Score.hand_score)
        scores = scores.order(-Score.numb_cards)
        scores = scores.fetch(request.number_of_results)
        return ScoreForms(items=[score.to_form() for score in scores])
        
    @endpoints.method(request_message=USER_REQUEST,
    	response_message=ScoreForms,
        path='scores/user/{user_name}',
        name='get_user_scores',
        http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
           raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=UserForms,
    	path='rankings',
        name='get_user_rankings',
        http_method='GET')
    def get_user_rankings(self,request):
        """ Returns players ranked by performance. """
        users = User.query()
        users = users.order(-User.winning_ratio)
        users = users.order(-User.n_games)
        return UserForms(items = [user.to_form() for user in users])
        
    @endpoints.method(response_message=StringMessage,
                      path='games/average_scores',
                      name='get_average_scores_remaining',
                      http_method='GET')   
    def get_average_scores(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_SCORES_REMAINING) or '')

    @endpoints.method(request_message=USER_REQUEST,
    	response_message=GameForms,
        path='games/user/{user_name}',
        name='get_user_games',
        http_method='GET')
    def get_user_games(self,request):
        """Returns all active Users games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
        	raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query(Game.user == user.key)
        games = games.filter(Game.game_over == False)
        games = games.filter(Game.canceled == False)
        return GameForms(items=[game.to_form("Hit or stand?") for game in games])
    
    @staticmethod
    def _cache_average_user_scores():
        """Populates memcache with the average moves remaining of Games"""
        
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_scores_remaining = sum([game.user_score
                                        for game in games])
            average = float(total_scores_remaining)/count
            memcache.set(MEMCACHE_SCORES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))
     

api = endpoints.api_server([BlackjackApi])
