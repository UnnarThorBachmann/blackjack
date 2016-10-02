#!/usr/bin/env python

"""
This is a code modified by Unnar Thor Bachmann in Udacity full stack program.
The project is to design a game from Guess a number. I modified the code to
implement Blackjack. 
"""

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging
from datetime import datetime
import webapp2
from google.appengine.api import mail, app_identity
from api import BlackjackApi

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """
        Sends an email to users every 12 hours
        if they have unfinished game.
        """
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        d = datetime.now()
        for user in users:
            # Filter games that are unfinished.
            games = Game.query(Game.user == user.key)
            games = games.filter(Game.game_over == False)
            for game in games:
                
                if (d-game.datetime).days > 0:
                    subject = 'This is a reminder!'
                    body = 'Hello {}! You have an unfinished game. \n\n House: {}. \n\n Your hand: {}'.format(user.name, game.house_hand[0] + ',' + 'XX', game.user_hand)
                    # This will send test emails, the arguments to send_mail are:
                    # from, to, subject, body
                    mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)


class UpdateAverageUserScores(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        BlackjackApi._cache_average_user_scores()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_user_scores', UpdateAverageUserScores),
], debug=True)
