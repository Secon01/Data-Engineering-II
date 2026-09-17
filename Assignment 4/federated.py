import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
import copy

if __name__ == '__main__':

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    full_train = datasets.MNIST('./data', train=True, download=True, transform=transform)
    test_data  = datasets.MNIST('./data', train=False, download=True, transform=transform)

    loader_a    = DataLoader(Subset(full_train, range(0, 15000)),     batch_size=64, shuffle=True,  num_workers=0)
    loader_b    = DataLoader(Subset(full_train, range(15000, 30000)), batch_size=64, shuffle=True,  num_workers=0)
    test_loader = DataLoader(test_data, batch_size=1000, shuffle=False, num_workers=0)

    print("Client A: 15,000 samples | Client B: 15,000 samples")

    class MNISTNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(784, 128)
            self.fc2 = nn.Linear(128, 64)
            self.fc3 = nn.Linear(64, 10)
        def forward(self, x):
            x = x.view(-1, 784)
            x = torch.relu(self.fc1(x))
            x = torch.relu(self.fc2(x))
            return self.fc3(x)

    def evaluate(model, loader):
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for X, y in loader:
                preds = model(X).argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)
        return correct / total

    def train_local(model, loader, epochs=2):
        local_model = copy.deepcopy(model)
        optimizer = optim.SGD(local_model.parameters(), lr=0.01, momentum=0.9)
        criterion = nn.CrossEntropyLoss()
        local_model.train()
        for _ in range(epochs):
            for X, y in loader:
                optimizer.zero_grad()
                loss = criterion(local_model(X), y)
                loss.backward()
                optimizer.step()
        return local_model.state_dict()

    def fed_avg(state_dicts):
        avg = copy.deepcopy(state_dicts[0])
        for key in avg:
            for i in range(1, len(state_dicts)):
                avg[key] += state_dicts[i][key]
            avg[key] = avg[key] / len(state_dicts)
        return avg

    # Federated Training
    NUM_ROUNDS = 5
    global_model = MNISTNet()
    print(f"Initial accuracy: {evaluate(global_model, test_loader):.4f}")
    print(f"\nFederated Training — {NUM_ROUNDS} rounds\n")

    for r in range(1, NUM_ROUNDS + 1):
        state_a = train_local(global_model, loader_a, epochs=2)
        state_b = train_local(global_model, loader_b, epochs=2)
        global_model.load_state_dict(fed_avg([state_a, state_b]))
        print(f"  Round {r}/{NUM_ROUNDS} — Global accuracy: {evaluate(global_model, test_loader):.4f}")

    fed_accuracy = evaluate(global_model, test_loader)

    # Single worker baseline
    print(f"\nBaseline: Client A only\n")
    single_model = MNISTNet()
    for r in range(1, NUM_ROUNDS + 1):
        state = train_local(single_model, loader_a, epochs=2)
        single_model.load_state_dict(state)
        print(f"  Round {r}/{NUM_ROUNDS} — Single accuracy: {evaluate(single_model, test_loader):.4f}")

    single_accuracy = evaluate(single_model, test_loader)

    print("\n" + "="*48)
    print("  FEDERATED LEARNING RESULTS")
    print("="*48)
    print(f"  Federated model accuracy  : {fed_accuracy:.4f}")
    print(f"  Single worker accuracy    : {single_accuracy:.4f}")
    print(f"  Improvement from FL       : {(fed_accuracy - single_accuracy)*100:+.2f}%")
    print(f"  Rounds                    : {NUM_ROUNDS}")
    print(f"  Clients                   : 2 (15,000 samples each)")
    print("="*48)
