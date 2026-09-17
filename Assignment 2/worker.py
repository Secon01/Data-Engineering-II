import pulsar
import json

def function(string):
    # Convert a single word to uppercase, simulating an intensive per-word operation
    return string.upper()

# Connect to the local Pulsar broker running in standalone mode
client = pulsar.Client('pulsar://localhost:6650')

# Subscribe to words-topic using Shared mode to allow multiple parallel workers
consumer = client.subscribe('words-topic',
                            subscription_name='worker-sub',
                            consumer_type=pulsar.ConsumerType.Shared)

# Create a producer to publish converted results to the results topic
producer = client.create_producer('results-topic')

print("Worker ready, waiting for words...")

while True:
    # Block until a word message arrives from the splitter
    msg = consumer.receive()
    try:
        data = json.loads(msg.data().decode('utf-8'))
        # Apply the conversion function and forward the result with its original index
        converted = function(data['word'])
        result = json.dumps({"index": data['index'],
                             "converted": converted,
                             "total": data['total']})
        producer.send(result.encode('utf-8'))
        print(f"Processed [{data['index']}]: {data['word']} -> {converted}")
        # Acknowledge so the message is not redelivered to another worker
        consumer.acknowledge(msg)
    except Exception as e:
        print(f"Error: {e}")
        # Negatively acknowledge on failure so Pulsar redelivers the message
        consumer.negative_acknowledge(msg)
