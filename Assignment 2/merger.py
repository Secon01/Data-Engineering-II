import pulsar
import json

# Connect to the local Pulsar broker running in standalone mode
client = pulsar.Client('pulsar://localhost:6650')

# Subscribe to results-topic to collect all converted words from the worker
consumer = client.subscribe('results-topic', subscription_name='merger-sub')

print("Merger ready, waiting for results...")

# Dictionary to store converted words keyed by their original index for ordered assembly
results = {}
total = None

while True:
    # Block until a result message arrives from a worker
    msg = consumer.receive()
    try:
        data = json.loads(msg.data().decode('utf-8'))
        # Store the converted word at its original index to preserve word order
        results[data['index']] = data['converted']
        total = data['total']
        print(f"Received [{data['index']}]: {data['converted']}")
        consumer.acknowledge(msg)

        # Once all words are received, reassemble and print the final string
        if len(results) == total:
            final = ' '.join(results[i] for i in sorted(results.keys()))
            print(f"\nResultant String: {final}")
            break
    except Exception as e:
        print(f"Error: {e}")
        # Negatively acknowledge on failure so Pulsar redelivers the message
        consumer.negative_acknowledge(msg)

# Close the client connection after all results have been merged
client.close()
