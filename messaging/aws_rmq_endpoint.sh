aws mq describe-broker --broker-id $(aws mq list-brokers --query 'BrokerSummaries[?BrokerName==`CRARabbitMQBroker`].BrokerId' --output text) --query 'BrokerInstances[?ConsoleURL!=`null`].Endpoints[0]' --output text > url.txt

echo "def rmq_url(): return '$(<url.txt)'" > ../backend/bermq/rmq_url.py
echo "def rmq_url(): return '$(<url.txt)'" > ../frontend/craui/rmq_url.py
echo "def rmq_url(): return '$(<url.txt)'" > ../database/rmq_url.py
