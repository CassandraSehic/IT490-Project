import pika
import ssl
import mysql.connector
import json
from cradb import init_db
from rmq_url import rmq_url

rmq_host = rmq_url().split('//')[1].split(':')[0]
rmq_port = 5671
rmq_user = 'db'
rmq_password = 'db_pa55w0rd$'

db_host = 'localhost'
db_user = 'craapp'
db_password = 'password'

context = ssl.create_default_context()
ssl_options = pika.SSLOptions(context, rmq_host)
rmq_credentials = pika.PlainCredentials(username=rmq_user, password=rmq_password)
rmq_connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rmq_host, port=rmq_port,
    credentials=rmq_credentials,
    ssl_options=ssl_options))

channel = rmq_connection.channel()
channel.basic_qos(prefetch_count=1)

cradb = mysql.connector.connect(
    host=db_host, user=db_user, password=db_password)

init_db(cradb)

# get_users
channel.queue_declare(queue='get_users')

def get_users(ch, method, props, body):
    answer = []
    sql = '''SELECT email FROM users'''
    with cradb.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
            answer.append(row[0])
    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=' '.join(answer))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='get_users', on_message_callback=get_users)

# get_password_hash
channel.queue_declare(queue='get_password_hash')

def get_password_hash(ch, method, props, body):
    answer = ''
    sql = '''SELECT password_hash FROM users WHERE email = %s'''
    with cradb.cursor() as cursor:
        cursor.execute(sql, [body])
        result = cursor.fetchone()
        if result:
            answer = result[0]
    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=answer)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='get_password_hash', on_message_callback=get_password_hash)

# register_email
channel.queue_declare(queue='register_email', durable=True)

def register_email(ch, method, props, body):
    sql = '''INSERT INTO users (email, password_hash) VALUES (%s, %s)'''
    with cradb.cursor() as cursor:
        cursor.execute(sql, body.split())
        cradb.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='register_email', on_message_callback=register_email)

# get_alerts
channel.queue_declare(queue='get_alerts')

def get_alerts(ch, method, props, body):
    answer = []
    sql = '''SELECT email, numerator, denominator, treshold, last FROM alerts WHERE email = %s'''
    with cradb.cursor() as cursor:
        cursor.execute(sql, [body])
        column_names=[column[0] for column in cursor.description]
        result = cursor.fetchall()
        for row in result:
            answer.append(dict(zip(column_names, row)))
    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=json.dumps(answer, default=float))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='get_alerts', on_message_callback=get_alerts)

# set_alert
channel.queue_declare(queue='set_alert')

def set_alert(ch, method, props, body):
    sql = '''REPLACE INTO alerts (email, numerator, denominator, treshold)
        VALUES (%s, %s, %s, CONVERT(%s, DECIMAL(12,6)))'''
    with cradb.cursor() as cursor:
        cursor.execute(sql, body.split())
        cradb.commit()
    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body='DONE')
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='set_alert', on_message_callback=set_alert)

# update_alert
channel.queue_declare(queue='update_alert')

def update_alert(ch, method, props, body):
    sql = '''UPDATE alerts SET last = CONVERT(%s, DECIMAL(12,6))
        WHERE email = %s AND numerator = %s AND denominator = %s AND treshold = CONVERT(%s, DECIMAL(12,6))'''
    with cradb.cursor() as cursor:
        cursor.execute(sql, body.split())
        cradb.commit()
    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body='DONE')
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='update_alert', on_message_callback=update_alert)

# delete_alert
channel.queue_declare(queue='delete_alert')

def delete_alert(ch, method, props, body):
    sql = '''DELETE FROM alerts
        WHERE email = %s AND numerator = %s AND denominator = %s AND
        treshold = CONVERT(%s, DECIMAL(12,6))'''
    with cradb.cursor() as cursor:
        cursor.execute(sql, body.split())
        cradb.commit()
    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body='DONE')
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='delete_alert', on_message_callback=delete_alert)

channel.start_consuming()
