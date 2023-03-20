import pika
import ssl
import json
from rmq_url import rmq_url


def send_message(email, subject, body):
    rmq_host = rmq_host = rmq_url().split('//')[1].split(':')[0]
    rmq_port = 5671
    rmq_user = 'be'
    rmq_password = 'b3_pa55w0rd$'

    context = ssl.create_default_context()
    ssl_options = pika.SSLOptions(context, rmq_host)
    rmq_credentials = pika.PlainCredentials(username=rmq_user, password=rmq_password)
    rmq_connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rmq_host, port=rmq_port,
        credentials=rmq_credentials,
        ssl_options=ssl_options))

    channel = rmq_connection.channel()
    channel.queue_declare(queue='send_email', durable=True)
    message = json.dumps({"to": email, "subject": subject, "body": body})
    channel.basic_publish(exchange="", routing_key="send_email", body=message)
    rmq_connection.close()

if __name__ == "__main__":
    send_message("cassandra@sehic.net", "Test Email", "This is a test email sent from RabbitMQ. pls work")