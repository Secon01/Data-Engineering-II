import pulsar
import json

# Input string to be split and processed word by word
INPUT_STRING = "I want to be capatilized"

# Connect to the local Pulsar broker running in standalone mode
client = pulsar.Client('pulsar://localhost:6650')

# Create a producer to publish individual words onto the words topic
producer = client.create_producer('words-topic')

words = INPUT_STRING.split()
total = len(words)

print(f"Original String: {INPUT_STRING}")
print(f"Splitting {total} words into words-topic...")

# Send each word as a JSON message carrying its index and total count for ordered reassembly
for i, word in enumerate(words):
    message = json.dumps({"index": i, "word": word, "total": total})
    producer.send(message.encode('utf-8'))
    print(f"Sent word [{i}]: {word}")

# Ensure all buffered messages are delivered before closing
producer.flush()
client.close()
print("All words sent.")
