#Full Stack Nanodegree Project 4 Concentration Game

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
    in the App Engine admin console and would like to use to host your instance of this sample.
2.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
    running by visiting the API Explorer - by default http://localhost:8080/_ah/api/explorer
 
##Game Description:
Concentration is a simple card matching game. Each game begins with a randomly 
ordered deck of 52 cards with no jokers. 

The user selects two numbers from 0 - 51 for their first_choice and second_choice,
these choices are sent to the make_move endpoint which will reply
with either: `(card-number):(rank/suit) ~ (card-number):(rank/suit):|Match` for a matching pair  
or `(card-number):(rank/suit) ~ (card-number):(rank/suit)|No_Match` for a non-matching pair.

Many different Concentration games can be played by many different users at any
given time. 

Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

Players scores are based on the lowest amount of attempts made in a fully completed game where 
all cards are matched.

Players are ranked according to the amount of fully completed games wherin all cards are matched.

##Files Included:
 - api.py: Contains endpoints and game logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
      raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
      existing user - will raise a NotFoundException if not.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, first_choice, second_choice
    - Returns: GameForm with new game state.
    - Description: Accepts a 'first_choice' and 'second_choice' containing 
      values from 0 - 51, then returns the updated game state. If this causes a 
      game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
      Will raise a NotFoundException if the User does not exist.
    
 - **get_average_attempts**
    - Path: 'games/average_attempts'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
      from a previously cached memcache key.
    
 - **get_user_games
    - Path: 'games/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: StringMessage
    - Description: Gets all user active games.

 - **cancel_game
    - Path: 'game/cancel/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: Cancels a specified active game.

 - **get_high_scores
    - Path: 'games/high_scores'
    - Method: GET
    - Parameters: number_of_results(optional)
    - Returns: ScoreForms
    - Description: Gets a certain number of high scores or 10 high scores if
      number_of results is not specified.

 - **get_user_rankings
    - Path: 'games/ranks'
    - Method: GET
    - Parameters: number_of_results
    - Returns: RecordForms
    - Description: Gets ranks of different users.

 - **get_game_history
    - Path: 'game/history/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: Gets a specified games move history. 

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Stores completed games. Associated with User model via KeyProperty.
    
 - **Record**
    - Stores a users wins and loses. Associated with User model via KeyProperty.

##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key,
      game_over flag, message, user_name).
 
 - **GameForms**
    - Multiple GameForm containers.

 - **NewGameForm**
    - Used to create a new game (user_name)

 - **MakeMoveForm**
    - Inbound make move form (first_choice, second_choice).

 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
      guesses).

 - **ScoreForms**
    - Multiple ScoreForm containers.

 - **NumberOfResultsForm**
    - Inbound make move form (number_of_results).

 - **RecordForm**
    - Representation of User game Record object(user_name, wins, loses).

 - **RecordForms**
    - Multiple RecordForm containers. 

 - **StringMessage**
    - General purpose String container.