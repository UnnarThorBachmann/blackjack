#Full Stack Nanodegree Project 4 Refresh

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 
 
 
##Game Description:

Blackjack is a well known card game. A game begins with the user and the house 
having two cards on their hands. The user can only view one card of the house. 
He can either 'hit' or 'stand'. Upon choosing to 'hit' he gets another card while
choosing to 'stand' is a request for no more cards. After the user stands it is the 
house's chance to 'hit' or 'stand'. Both players can 'hit' as long as their score 
is below or equal to 21. If the score exceeds 21 it is an automatic loss to either 
player. If neither score is above 21 then the higher scoring hand wins. Equal score results in a draw.

A simple AI agent plays for the house. It simply hits while the score of the hand is below 17.

The hands are scored as a sum of the score of each card on hand. The jacks, queens and 
kings are scored as 10, the aces as either 1 or 11 and other cards as their face value.

Each game can be retrieved or played by using the path parameter `urlsafe_game_key`.

Players are ranked by winning ratio and ties broken by number of games.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **cancel_game**
   - Path: 'user'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: GameForm
    - Description: Cancels a game. Returns a game state wit cancel message. 
    Will raise a ForbiddenException if the game is over.

 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **get_game_history**
    - Path: 'move/{urlsafe_game_key}'
    - Method: GET
    - Parameters: url_safe_key  
    - Returns: HistoryForm
    - Description: Returns the history of a game.

 - **get_high_scores**
    - Path: 'get_high_scores'
    - Method: GET
    - Parameters: number_of_results
    - Returns: ScoreForms
    - Description: Returns highest scores. Ties broken with number of cards.

 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_active_game_count**
    - Path: 'games/active'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

- **get_average_scores**
   - Path: games/average_scores
   - Method: GET
   - Parameters: None
   - Returns: StringMessage
   - Description:Get the cached average moves remaining. 

- **get_user_games**
   - Path: 'games/user/{user_name}'
   - Method: GET
   - Parameters: user_name
   - Returns: GameForms
   - Description: Returns all active Users games.

- **get_user_rankings**
   - Path: 'games/average_attempts'
   - Method: GET
   - Parameters: None
   - Returns: UserForms
   - Description: Returns players ranked by performance.

- **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Makes a move. Returns a game state with message. User can either hit or stand. Hit is a request for another card while stand is a request for no more cards during the game. Will raise a ForbiddenException if the game is over or canceled.
    
- **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, min, max, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Min must be less than
    max. Also adds a task to a task queue to update the average moves remaining
    for active games.

- **resume_game**
   - Path: 'resume/{urlsafe_game_key}'
   - Method: PUT
   - Parameters: urlsafe_game_key
   - Returns: GameForm
   - Description: Resumes a canceled game to a normal game state.
   Will raise a ForbiddenException if the game is over.

##Models Included:
 - **User**
    - Stores unique user_name, winning_ratio, number of games (n_games) and (optional) email address. Users are ranked by winning ration. Ties broken by number of games. 
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records results from each game. A game can be won (1.0), drawn (0.5) or lost (0.0). Ties broken with number of cards. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, user_hand, house_hand, game_over flag, message)
    game_over flag, message, user_name).
 - **HistoryForm**
    - Representation of a Game's history (urlsafe_key, player, status, results, moves, user_hand_init house_hand_init, user_hand_end, house_hand_end)
 - **NewGameForm**
    - Used to create a new game (user_name)
 - **MakeMoveForm**
    - Inbound make move form (hit_or_stand).
 - **MoveForm**
    - Used to represent a move (move, message)
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, result (0, 1/2 or 1), hand_score and numb_cards)
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.
 - **UserForm**
    - Represents a user (user_name, winning_ratio, n_games)
 - **UserForms**
    - Multiple UserForm container.