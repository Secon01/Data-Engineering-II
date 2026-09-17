import pulsar

# Connect to the local Pulsar broker running in standalone mode
client = pulsar.Client('pulsar://localhost:6650')

# Subscribe to 'DEtopic' using a named subscription to track message offsets
consumer = client.subscribe('DEtopic', subscription_name='DE-sub')

# Block until a message is received from the topic
msg = consumer.receive()
try:
    # Print the received message payload
    print("Received message : '%s'" % msg.data())
    # Acknowledge successful processing so the message is not redelivered
    consumer.acknowledge(msg)
except:
    # Negatively acknowledge on failure so Pulsar redelivers the message
    consumer.negative_acknowledge(msg)

# Close the client connection to release resources
client.close()
