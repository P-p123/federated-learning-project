import argparse
import json
import os
import random
import time

import flwr as fl
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from model import DiabetesModel
from utils import load_data

# 🔐 Differential Privacy Toggle
USE_DP = True  # change to False if needed

# Real-world Hospital Clients with diverse behaviors
HOSPITAL_CLIENTS = {
    0: {'name': 'Mayo Clinic', 'location': 'Rochester, MN', 'behavior': 'honest', 'type': 'Teaching Hospital'},
    1: {'name': 'Cleveland Clinic', 'location': 'Cleveland, OH', 'behavior': 'slow', 'type': 'Specialty Hospital'},
    2: {'name': 'Johns Hopkins', 'location': 'Baltimore, MD', 'behavior': 'sleepy', 'type': 'Research Hospital'},
    3: {'name': 'Massachusetts General', 'location': 'Boston, MA', 'behavior': 'honest', 'type': 'General Hospital'},
    4: {'name': 'UCLA Medical Center', 'location': 'Los Angeles, CA', 'behavior': 'fast', 'type': 'University Hospital'},
    5: {'name': 'NYU Langone', 'location': 'New York, NY', 'behavior': 'unreliable', 'type': 'Urban Hospital'},
    6: {'name': 'Duke University Hospital', 'location': 'Durham, NC', 'behavior': 'honest', 'type': 'Academic Medical Center'},
    7: {'name': 'Stanford Hospital', 'location': 'Stanford, CA', 'behavior': 'slow', 'type': 'Research Hospital'},
    8: {'name': 'Mount Sinai Hospital', 'location': 'New York, NY', 'behavior': 'sleepy', 'type': 'Teaching Hospital'},
    9: {'name': 'Barnes-Jewish Hospital', 'location': 'St. Louis, MO', 'behavior': 'honest', 'type': 'General Hospital'},
}

# Client behavior types with more variety
CLIENT_BEHAVIORS = {
    'honest': {'description': 'Always trains reliably', 'color': '#10B981'},
    'slow': {'description': 'Delays training (1.5-3s)', 'color': '#F59E0B'},
    'sleepy': {'description': '50% chance to skip training', 'color': '#EF4444'},
    'fast': {'description': 'Trains quickly with fewer epochs', 'color': '#3B82F6'},
    'unreliable': {'description': '30% chance to skip, variable delays', 'color': '#8B5CF6'},
}


# 🔐 Add noise for privacy
def add_noise(parameters, noise_scale=0.005):
    noisy_params = []
    for param in parameters:
        noise = np.random.normal(0, noise_scale, param.shape)
        noisy_params.append(param + noise)
    return noisy_params


class FlowerClient(fl.client.NumPyClient):
    def __init__(self, cid, behavior=None):
        self.cid = cid
        hospital_info = HOSPITAL_CLIENTS.get(cid, {'name': f'Hospital {cid}', 'behavior': 'honest', 'location': 'Unknown', 'type': 'General'})
        self.hospital_name = hospital_info['name']
        self.location = hospital_info['location']
        self.hospital_type = hospital_info['type']
        self.behavior = behavior or hospital_info['behavior']
        self.behavior_info = CLIENT_BEHAVIORS[self.behavior]

        self.model = DiabetesModel()
        self.trainloader, self.testloader = load_data(cid)

        self.criterion = nn.BCELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.round_num = 0

    def log(self, message):
        print(f'🏥 [{self.hospital_name}] {message}')

    def save_status(self, trained, skipped, delay, metrics):
        os.makedirs('client_logs', exist_ok=True)
        path = os.path.join('client_logs', f'client_{self.cid}.json')

        history = []
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = []

        history.append({
            'round': self.round_num,
            'hospital_name': self.hospital_name,
            'location': self.location,
            'hospital_type': self.hospital_type,
            'behavior': self.behavior,
            'behavior_desc': self.behavior_info['description'],
            'trained': trained,
            'skipped': skipped,
            'delay': delay,
            'accuracy': metrics.get('accuracy', 0),
            'precision': metrics.get('precision', 0),
            'recall': metrics.get('recall', 0),
            'f1_score': metrics.get('f1_score', 0),
            'timestamp': time.time(),
        })

        with open(path, 'w') as f:
            json.dump(history, f, indent=2)

    # 📦 Get model weights
    def get_parameters(self, config):
        params = [val.cpu().numpy() for val in self.model.state_dict().values()]

        if USE_DP:
            params = add_noise(params)

        return params

    # 🔁 Set model weights
    def set_parameters(self, parameters):
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.model.load_state_dict(state_dict, strict=True)

    def simulate_delay(self):
        if self.behavior == 'slow':
            delay = random.uniform(1.5, 3.0)
            self.log(f'🐌 {self.behavior_info["description"]}: delaying for {delay:.1f}s before training')
            time.sleep(delay)
            return delay
        elif self.behavior == 'unreliable':
            if random.random() < 0.3:
                delay = random.uniform(0.5, 2.0)
                self.log(f'⚠️ {self.behavior_info["description"]}: delaying for {delay:.1f}s')
                time.sleep(delay)
                return delay
        return 0.0

    def should_skip_training(self):
        if self.behavior == 'sleepy':
            skip = random.random() < 0.5
            if skip:
                self.log(f'😴 {self.behavior_info["description"]}: skipping local training this round')
            return skip
        elif self.behavior == 'unreliable':
            skip = random.random() < 0.3
            if skip:
                self.log(f'⚠️ {self.behavior_info["description"]}: skipping local training this round')
            return skip
        return False

    def get_training_epochs(self):
        if self.behavior == 'fast':
            return 3  # Fewer epochs for fast training
        return 5  # Standard epochs

    # 🧠 Train model
    def fit(self, parameters, config):
        self.round_num += 1
        self.set_parameters(parameters)

        self.log(f'📥 Received global weights for round {self.round_num}')

        trained = True
        skipped = False
        delay = self.simulate_delay()

        if self.should_skip_training():
            trained = False
            skipped = True
            delay = 0.0
            loss, size, metrics = self.evaluate(None, config)
            self.save_status(trained, skipped, delay, metrics)
            return self.get_parameters(config), len(self.trainloader.dataset), metrics

        epochs = self.get_training_epochs()
        self.model.train()

        for epoch in range(epochs):
            for X, y in self.trainloader:
                self.optimizer.zero_grad()
                outputs = self.model(X)
                loss = self.criterion(outputs, y)
                loss.backward()
                self.optimizer.step()

            if self.behavior == 'slow':
                self.log(f'🐌 Slow training: finished epoch {epoch + 1}/{epochs}')
                time.sleep(0.5)
            elif self.behavior == 'fast':
                self.log(f'⚡ Fast training: finished epoch {epoch + 1}/{epochs}')

        loss, size, metrics = self.evaluate(None, config)

        self.save_status(trained, skipped, delay, metrics)
        self.log(f'✅ Finished round {self.round_num}, accuracy: {metrics["accuracy"]:.3f}')

        return self.get_parameters(config), len(self.trainloader.dataset), metrics

    # 📊 Evaluate model (NO overwriting)
    def evaluate(self, parameters, config):
        self.model.eval()

        correct = 0
        total = 0

        all_preds = []
        all_labels = []

        with torch.no_grad():
            for X, y in self.testloader:
                outputs = self.model(X)
                preds = (outputs > 0.5).float()

                correct += (preds == y).sum().item()
                total += y.size(0)

                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(y.cpu().numpy())

        all_preds = [int(p[0]) for p in all_preds]
        all_labels = [int(l[0]) for l in all_labels]

        accuracy = correct / total if total != 0 else 0
        tp = sum((p == 1 and l == 1) for p, l in zip(all_preds, all_labels))
        fp = sum((p == 1 and l == 0) for p, l in zip(all_preds, all_labels))
        fn = sum((p == 0 and l == 1) for p, l in zip(all_preds, all_labels))

        precision = tp / (tp + fp) if (tp + fp) != 0 else 0
        recall = tp / (tp + fn) if (tp + fn) != 0 else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) != 0 else 0

        self.log(f'📊 Evaluation → Acc: {accuracy:.3f}, Prec: {precision:.3f}, Recall: {recall:.3f}')

        return 0.0, len(self.testloader.dataset), {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
        }


def parse_args():
    parser = argparse.ArgumentParser(description='Start a Flower client with hospital behavior simulation.')
    parser.add_argument('--cid', type=int, default=None, help='Client ID (0-9)')
    parser.add_argument(
        '--behavior',
        choices=['honest', 'slow', 'sleepy', 'fast', 'unreliable'],
        default=None,
        help='Override the client behavior for this client.',
    )
    return parser.parse_args()


# 🚀 Start client
def main():
    args = parse_args()

    if args.cid is None:
        client_id = random.randint(0, 9)
    else:
        client_id = args.cid

    hospital_info = HOSPITAL_CLIENTS.get(client_id, {'name': f'Hospital {client_id}', 'behavior': 'honest'})
    behavior = args.behavior or hospital_info['behavior']

    print(f'🏥 Starting {hospital_info["name"]} ({hospital_info["location"]}) - {behavior.upper()} behavior')
    print(f'🏥 Hospital Type: {hospital_info["type"]}')
    print(f'🏥 Behavior: {CLIENT_BEHAVIORS[behavior]["description"]}')

    fl.client.start_numpy_client(
        server_address='127.0.0.1:8081',
        client=FlowerClient(client_id, behavior=behavior),
    )


if __name__ == '__main__':
    main()
