import pulsar

# Connect to the local Pulsar broker running in standalone mode
client = pulsar.Client('pulsar://localhost:6650')

# Create a producer on 'DEtopic' to publish messages
producer = client.create_producer('DEtopic')

# Send a UTF-8 encoded message to the topic
producer.send(('Welcome to Data Engineering Course!').encode('utf-8'))

# Close the client connection to release resources
client.close()
