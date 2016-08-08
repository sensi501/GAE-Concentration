#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import webapp2
from google.appengine.api import mail, app_identity
from api import ConcentrationApi
from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every 24 hours using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        for user in users:
            subject = 'This is a reminder!'
            active_games = Game.query(Game.user == user.key, 
                                      Game.game_over == False).get()
            if active_games:
                body = 'Hello {}, you still have some active incomplete games,\
                        why not give the Concentration another try!'.format(user.name)
                       
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                            user.email,
                            subject,
                            body)
            else:
                body = 'Hello {}, try out Concentration!'.format(user.name)
                       
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                            user.email,
                            subject,
                            body)


class UpdateAverageMoves(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        ConcentrationApi._cache_average_attempts()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMoves),
], debug=True)
