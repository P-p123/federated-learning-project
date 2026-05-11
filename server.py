import flwr as fl
import matplotlib.pyplot as plt
import os
import json
import time

# 🔥 Reset lists every run
round_accuracies = []
round_precisions = []
round_recalls = []
round_f1s = []

start_time = time.time()


def weighted_average(metrics):
    global round_accuracies, round_precisions, round_recalls, round_f1s

    accuracies = []
    precisions = []
    recalls = []
    f1s = []

    for num_examples, m in metrics:
        if "accuracy" in m:
            accuracies.append(num_examples * m["accuracy"])
            precisions.append(num_examples * m["precision"])
            recalls.append(num_examples * m["recall"])
            f1s.append(num_examples * m["f1_score"])

    total_examples = sum(num_examples for num_examples, _ in metrics)

    if total_examples == 0:
        return {
            "accuracy": 0,
            "precision": 0,
            "recall": 0,
            "f1_score": 0
        }

    # ✅ Calculate averages
    round_accuracy = sum(accuracies) / total_examples
    round_precision = sum(precisions) / total_examples
    round_recall = sum(recalls) / total_examples
    round_f1 = sum(f1s) / total_examples

    # ✅ Store for graph
    round_accuracies.append(round_accuracy)
    round_precisions.append(round_precision)
    round_recalls.append(round_recall)
    round_f1s.append(round_f1)

    print(f"Round {len(round_accuracies)}")
    print(f"Accuracy: {round_accuracy:.4f}")

    # 🔥 VERY IMPORTANT: SAVE LIVE RESULTS FOR DASHBOARD
    live_results = {
        "accuracy": round_accuracy,
        "precision": round_precision,
        "recall": round_recall,
        "f1_score": round_f1,
        "training_time": time.time() - start_time
    }

    with open("federated_results.json", "w") as f:
        json.dump(live_results, f)

    return {
        "accuracy": round_accuracy,
        "precision": round_precision,
        "recall": round_recall,
        "f1_score": round_f1
    }


# 🚀 Strategy
strategy = fl.server.strategy.FedAvg(
    evaluate_metrics_aggregation_fn=weighted_average
)


# 🚀 Start server
fl.server.start_server(
    server_address="0.0.0.0:8081",
    config=fl.server.ServerConfig(num_rounds=10),
    strategy=strategy,
)

# ⏱️ Total training time
end_time = time.time()
training_time = end_time - start_time


# ===============================
# ✅ FINAL SAVE (after training)
# ===============================
final_results = {
    "accuracy": round_accuracies[-1] if round_accuracies else 0,
    "precision": round_precisions[-1] if round_precisions else 0,
    "recall": round_recalls[-1] if round_recalls else 0,
    "f1_score": round_f1s[-1] if round_f1s else 0,
    "training_time": training_time
}

with open("federated_results.json", "w") as f:
    json.dump(final_results, f)

print("Final Federated Results:", final_results)


# ===============================
# 📈 GRAPH SECTION
# ===============================

graph_path = "static/federated_accuracy_plot.png"

# Remove old graph
if os.path.exists(graph_path):
    os.remove(graph_path)

plt.figure(figsize=(10, 6))

plt.plot(
    range(1, len(round_accuracies) + 1),
    round_accuracies,
    marker='o'
)

plt.title("Federated Learning Accuracy over Rounds")
plt.xlabel("Rounds")
plt.ylabel("Accuracy")
plt.grid(True)

# Annotate points
for i, acc in enumerate(round_accuracies):
    plt.text(i + 1, acc, f"{acc:.2f}", ha='center', fontsize=8)

plt.tight_layout()
plt.savefig(graph_path)

# ❌ REMOVE THIS (IMPORTANT — avoids blocking)
# plt.show()