import pika
import ssl
import uuid
import json
import requests
from datetime import date, timedelta

from bermq.rmq_url import rmq_url
from bermq.smtp import send_email_smtp

rmq_host = rmq_url().split('//')[1].split(':')[0]
rmq_port = 5671
rmq_user = 'be'
rmq_password = 'b3_pa55w0rd$'

context = ssl.create_default_context()
ssl_options = pika.SSLOptions(context, rmq_host)
rmq_credentials = pika.PlainCredentials(username=rmq_user, password=rmq_password)

def get_rmq_connection():
    return pika.BlockingConnection(
        pika.ConnectionParameters(host=rmq_host, port=rmq_port,
        credentials=rmq_credentials,
        ssl_options=ssl_options))

class RMQRPCClient(object):

    def __init__(self, rpc_queue):
        self.rpc_queue = rpc_queue
        self.connection = get_rmq_connection()
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, request):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=self.rpc_queue,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=request)
        self.connection.process_data_events(time_limit=None)
        return self.response

def get_users():
    return RMQRPCClient('get_users').call("")

def get_alerts(email):
    return RMQRPCClient('get_alerts').call(email)

def update_alert(email, numerator, denominator, treshold, last):
    req = ' '.join([str(last), email, numerator, denominator, str(treshold)])
    return RMQRPCClient('update_alert').call(req)

def unique_symbols(alerts):
    symbols = []
    for alert in alerts:
        if alert['numerator'] not in symbols:
            symbols.append(alert['numerator'])
        if alert['denominator'] not in symbols:
            symbols.append(alert['denominator'])
    return symbols

def get_rates(symbols, base='BTC'):
    url = f'https://api.exchangerate.host/latest?base={base}&symbols={",".join(symbols)}'
    response = requests.get(url)
    data = response.json()
    current_rates = data['rates']
    previous_day = str(date.fromisoformat(data['date']) - timedelta(days=1))
    url = f'https://api.exchangerate.host/{previous_day}?base={base}&symbols={",".join(symbols)}'
    response = requests.get(url)
    previous_rates = response.json()['rates']
    return current_rates, previous_rates

def alert_email_message(numerator, denominator, treshold, ratio):
    return f'''<html><head></head><body>
    <p>Hi,</p>
    <p>The ratio of {numerator} / {denominator} has crossed your alert treshold of {treshold} to {ratio}.</p>
    <p>Thank you.<p>
    </body><html>'''

def alert_triggered(alert, ratio):
    subject = f"CRA Alert on {alert['numerator']}/{alert['denominator']}"
    message = alert_email_message(alert['numerator'], alert['denominator'], alert['treshold'], ratio)
    send_email_smtp(alert['email'], subject, message)

def process_alerts():
    users = get_users().split()
    alerts = []
    for email in users:
        alerts.extend(json.loads(get_alerts(email)))
    symbols = unique_symbols(alerts)
    current_rates, previous_rates = get_rates(symbols)
    for alert in alerts:
        ratio = current_rates[alert['denominator']] / current_rates[alert['numerator']]
        if not alert['last']:
            alert['last'] = previous_rates[alert['denominator']] / previous_rates[alert['numerator']]
        if alert['last'] < alert['treshold']:
            if alert['treshold'] <= ratio:
                alert_triggered(alert, ratio)
        else:
            if alert['treshold'] >= ratio:
                alert_triggered(alert, ratio)
        update_alert(alert['email'], alert['numerator'], alert['denominator'], alert['treshold'], ratio)

if __name__ == "__main__":
    process_alerts()
