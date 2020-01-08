# -*- coding: utf-8 -*-
import flask
import telebot

from bot import get_bot_update, set_hook, main

app = flask.Flask(__name__)
app.debug = True


@app.route('/HOOK', methods=['POST', 'GET'])
def webhook_handler():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        get_bot_update(update)
        return ''
    else:
        flask.abort(403)


set_hook()
main()
