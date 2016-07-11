"""models.py - This file contains the class definitions for the Datastore
entities used by the Game."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""
    user = ndb.KeyProperty(required=True, kind='User')
    cards = ndb.StringProperty(required=True, default='')
    available_cards = ndb.StringProperty(required=True, default='')
    successful_attempts = ndb.IntegerProperty(required=True, default=0)
    failed_attempts = ndb.IntegerProperty(required=True, default=0)
    total_attempts = ndb.IntegerProperty(required=True, default=0)
    game_over = ndb.BooleanProperty(required=True, default=False)
    move_history = ndb.StringProperty(required=True, default='')

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game object instance"""
        RANKS = ('_A','_2','_3','_4','_5','_6','_7',\
                 '_8','_9','10','_J','_Q','_K')
        SUITES = ('H','D','C','S')
        card_list = []
        card_string = ''
        
        for suite in SUITES:
            for rank in RANKS:
                card_list.append(rank + suite)
        
        random.shuffle(card_list)
        card_string = ','.join(card_list)
        
        game = Game(user=user,
                    cards=card_string,
                    available_cards=card_string,
                    successful_attempts=0,
                    failed_attempts=0,
                    total_attempts=0,
                    game_over=False,
                    move_history='')         
        game.put()
        
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.successful_attempts = self.successful_attempts
        form.failed_attempts = self.failed_attempts
        form.total_attempts = self.total_attempts
        form.game_over = self.game_over
        form.message = message
        return form

    def end_game(self, won):
        """Ends the game - if won is True, the player won. - if won is False,
           the player cancelled the game and player win lose record object is 
           updated."""
        self.game_over = True
        self.put()
        
        # Creates a new game score object
        score = Score(user=self.user, 
                      date=date.today(),
                      successful_attempts=self.successful_attempts,
                      failed_attempts=self.failed_attempts,
                      total_attempts=self.total_attempts,
                      won=won)
        score.put()
        
        # Update player win/lose record object
        record = Record.query(Record.user==self.user).get()
        if won:
            record.wins += 1
        else:
            record.loses += 1
         
        record.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    successful_attempts = ndb.IntegerProperty(required=True)
    total_attempts = ndb.IntegerProperty(required=True)
    failed_attempts = ndb.IntegerProperty(required=True)
    won = ndb.BooleanProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, 
                         date=str(self.date),
                         successful_attempts=self.successful_attempts,
                         total_attempts=self.total_attempts,
                         failed_attempts=self.failed_attempts,
                         won=self.won)

class Record(ndb.Model):
    """Player win/loss record object"""
    user = ndb.KeyProperty(required=True, kind='User')
    wins = ndb.IntegerProperty(required=True, default=0)
    loses = ndb.IntegerProperty(required=True, default=0)

    def to_form(self):
        return RecordForm(user_name=self.user.get().name,
                          wins=self.wins,
                          loses=self.loses)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    successful_attempts = messages.IntegerField(2, required=True)
    failed_attempts = messages.IntegerField(3, required=True)
    total_attempts = messages.IntegerField(4, required=True)
    game_over = messages.BooleanField(5, required=True)
    message = messages.StringField(6, required=True)
    user_name = messages.StringField(7, required=True)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    first_choice = messages.IntegerField(1, required=True)
    second_choice =  messages.IntegerField(2, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    successful_attempts = messages.IntegerField(3, required=True)
    failed_attempts = messages.IntegerField(4, required=True)
    total_attempts = messages.IntegerField(5, required=True)
    won = messages.BooleanField(6, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class NumberOfResultsForm(messages.Message):
    """Used to input a number of results for score and rank return info"""
    number_of_results = messages.IntegerField(1, required=False)


class RecordForm(messages.Message):
    """Record output formating"""
    user_name = messages.StringField(1, required=True)
    wins = messages.IntegerField(2, required=True)
    loses = messages.IntegerField(3, required=True)


class RecordForms(messages.Message):
    """Return multiple Record Form objects"""
    items = messages.MessageField(RecordForm, 1, repeated=True)


class StringMessage(messages.Message):
    """Return single string message"""
    message = messages.StringField(1, required=True)

