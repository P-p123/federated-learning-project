import pandas as pd
import torch
import numpy as np

from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_data(client_id, num_clients=10):

    # ✅ FIXED SEED (important for consistent results)
    np.random.seed(42)
    torch.manual_seed(42)

    # Load dataset
    df = pd.read_csv("diabetes.csv")

    # Features & Labels
    X = df.drop("Outcome", axis=1).values
    y = df["Outcome"].values.reshape(-1, 1)

    # ✅ NORMALIZATION (VERY IMPORTANT)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # ✅ STRATIFIED SPLIT (fix class imbalance)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=42
    )

    # ✅ SPLIT DATA AMONG CLIENTS
    X_splits = np.array_split(X_train, num_clients)
    y_splits = np.array_split(y_train, num_clients)

    X_client = X_splits[client_id]
    y_client = y_splits[client_id]

    # Convert to tensors
    trainset = TensorDataset(
        torch.tensor(X_client, dtype=torch.float32),
        torch.tensor(y_client, dtype=torch.float32)
    )

    testset = TensorDataset(
        torch.tensor(X_test, dtype=torch.float32),
        torch.tensor(y_test, dtype=torch.float32)
    )

    # ✅ DataLoaders
    trainloader = DataLoader(trainset, batch_size=32, shuffle=True)
    testloader = DataLoader(testset, batch_size=32)

    return trainloader, testloader
