# -*- coding: utf-8 -*-`

import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from models import User, Game, Score, Record
from models import GameForm, GameForms, NewGameForm, MakeMoveForm, ScoreForm,\
    ScoreForms, NumberOfResultsForm, RecordForm, RecordForms,StringMessage
from utils import get_by_urlsafe


"""Endpoint request methods."""
USER_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),
    email=messages.StringField(2),)

NEW_GAME_REQUEST = endpoints.ResourceContainer(
    NewGameForm,)

GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)

USER_NAME_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),)

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)

NUMBER_OF_RESULTS_REQUEST = endpoints.ResourceContainer(
    NumberOfResultsForm,)

MEMCACHE_AVERAGE_MOVES = 'AVERAGE_MOVES'


@endpoints.api(name='concentration', version='v1')
class ConcentrationApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User"""
        # Checks if user provided user name exists in database
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(\
                    'A User with that name already exists!')

        # Creates new player record and user 
        # based on user inputed name and email
        user = User(name=request.user_name, 
                    email=request.email)
        user.put()

        record = Record(user=user.key,
                        wins=0,
                        loses=0)
        record.put()

        return StringMessage(message='User {} created!'.format(request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        # Retrieve user information from database based on inputed information
        user = User.query(User.name == request.user_name).get()
        
        # If logged in user does not match inputed user exception is raised.
        if not user:
            raise endpoints.NotFoundException('A User with that name does not exist!')
        
        # Instantiation of new game entry.
        game = Game.new_game(user.key)

        # Task queue to update the average attempts.
        taskqueue.add(url='/tasks/cache_average_attempts')
        
        return game.to_form('Good luck playing Concentration!')
    
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancels active game"""
        # Retrieve game instance.
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        
        # Checks if game exists to determines whether to
        # cancel game or raise exception.
        if game and game.game_over == False:
            game.end_game(won=False)
            return game.to_form('Game was successfully cancelled!')
        else:
            raise endpoints.NotFoundException('Game to be cancelled was not found!')
        
    @endpoints.method(request_message=USER_NAME_REQUEST,
                      response_message=GameForms,
                      path='games/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return user active games"""
        # Retrieve active games based on user name and false game over status.
        user = User.query(User.name==request.user_name).get()
        games = Game.query(Game.user==user.key, 
                           Game.game_over==False)
        if games:
            return GameForms(items=[game.to_form('') for game in games])
        else:
            raise endpoints.NotFoundException('No games were found!')
        
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Checks players card choices then returns 
           a game state with a message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        
        # Checks if game is over.
        if game.game_over:
            return game.to_form('This game is already over!')
                
        # Checks if all card pairs have been matched before continuing.
        elif game.successful_attempts < 26:
            # Declare variables to store player card choices.
            choice_one_int = 0
            choice_two_int = 0
        
            # Checks for valid player inputs that are castable 
            # to type int(integer) before continuing.
            try:
                choice_one_int = int(request.first_choice)
                choice_two_int = int(request.second_choice)
            except:
                return game.to_form('You have entered invalid choices, choices can only be numbers in range of 0 - 51!')
            
            # Checks player input for choices in range of 0 - 51.
            if (choice_one_int < 0) or (choice_one_int > 51):
                return game.to_form('First choice is not in range of 0-51!')
            elif (choice_two_int < 0) or (choice_two_int > 51):
                return game.to_form('Second choice is not in range of 0-51!')
            
            # Checks for identical choices.
            if choice_one_int == choice_two_int:
                return game.to_form('First choice and second choice cannot be the same!')

            # Card rank, suite colors, and game history setup variables.
            attempts = game.total_attempts
            success = game.successful_attempts
            fail = game.failed_attempts
            history = []
            history = game.move_history.split(' ')
            cards = []
            cards = game.available_cards.split(',')
            CARD_COLORS = {'H':'R', 'D':'R', 'C':'B', 'S':'B'}
            card_one = cards[choice_one_int]
            card_two = cards[choice_two_int]
            pairing_result = ''
            
            # Checks if a user selected card has been matched.
            if card_one == '---':
                return game.to_form('First choice has already been selected!')
            elif card_two == '---':
                return game.to_form('Second choice has already been selected!')
            
            # Variables storing card_one and card_two rank, suite, and color.
            card_one_rank = card_one[0:2]
            card_one_suite = card_one[2]
            card_one_color = CARD_COLORS[card_one_suite]
            card_two_rank = card_two[0:2]
            card_two_suite = card_two[2]
            card_two_color = CARD_COLORS[card_two_suite]      
            
            # Checks for matches in card rank and suit color.
            if card_one_rank == card_two_rank:
                if card_one_color == card_two_color:
                    success += 1
                    pairing_result = 'Match'
                    cards[choice_one_int] = '---'
                    cards[choice_two_int] = '---'
                else:
                    fail += 1
                    pairing_result = 'No_Match'
            else:
                fail += 1
                pairing_result = 'No_Match'
            
            # Update game statistics.
            attempts += 1
            history += '[' + str(game.total_attempts) + ']'
            history += str(choice_one_int) + ':'
            history += str(card_one) + '~'
            history += str(choice_two_int) + ':'
            history += str(card_two) + '|'
            history += str(pairing_result) + ' '
            
            joined_history = ''.join(history)
            joined_cards = ','.join(cards)
            game.available_cards = joined_cards
            game.total_attempts = attempts
            game.successful_attempts = success
            game.failed_attempts = fail
            game.move_history = joined_history
            game.put()

            form_output = str(choice_one_int) + ':' + card_one + ' ~ '
            form_output += str(choice_two_int) + ':' + card_two
            form_output += ' | ' + pairing_result

            return game.to_form(form_output)

        # Update game statistics when player wins game.    
        else:
            game.game_over = True
            game.end_game(won=True)
            game.put()
            return game.to_form('You win!')
            
    
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return a specified games move history"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if game:
            return game.to_form(game.move_history)
        else:
            raise endpoints.NotFoundException('Game not Found!')
        
    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_NAME_REQUEST,
                      response_message=ScoreForms,
                      path='scores/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        
        # Checks if the user specified exists then retrieves their scores.
        if not user:
            raise endpoints.NotFoundException('A User with that name does not exist!')
        scores = Score.query(Score.user==user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=NUMBER_OF_RESULTS_REQUEST,
                      response_message=ScoreForms,
                      path='scores/high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Return a specified number of high scores"""
        # Checks the value of number_of_results to determine if it is a number
        # to return a specific number of highscores if it is not then function
        # will only return 10 highscores
        if isinstance(request.number_of_results, int):
            _number_of_results = request.number_of_results
            scores = Score.query(Score.won==True).order(Score.total_attempts).fetch(limit=_number_of_results)
            return ScoreForms(items=[score.to_form() for score in scores])
        else:
            scores = Score.query(Score.won==True).order(Score.total_attempts).fetch(limit=10)
            return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=NUMBER_OF_RESULTS_REQUEST,
                      response_message=RecordForms,
                      path='scores/ranks',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Get user rankings"""
        if isinstance(request.number_of_results, int):
            _number_of_results = request.number_of_results
            records = Record.query().order(Record.wins).fetch(limit=_number_of_results)
            return RecordForms(items=[record.to_form() for record in records])
        else:
            records = Record.query().order(Record.wins)
            return RecordForms(items=[record.to_form() for record in records])


    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves"""
        return StringMessage(message=memcache\
                             .get(MEMCACHE_AVERAGE_MOVES) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves in games"""
        games = Game.query(Game.game_over == True).fetch()

        # Calculates the average by counting all inactive games
        # adding the sum of total_attempts in those inactive games
        # then dividing the sum_of_attempts by the count of inactive games
        # finally returning the result
        if games:
            count = len(games)
            sum_of_attempts = sum([game.total_attempts for game in games])
            average = float(sum_of_attempts)/count
            memcache.set(MEMCACHE_AVERAGE_MOVES,
                         'The average amount of moves per game is {:.2f}'.format(average))


api = endpoints.api_server([ConcentrationApi])