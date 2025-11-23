# Pod of Tokyo Core

This repository contains the core services for the Pod of Tokyo game.

## Prerequisites

- Python 3.13+
- `pip`
- `virtualenv` (recommended)

## Setup

1.  **Clone the repository** (if you haven't already).

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Game

You will need to run three separate components in separate terminal windows/tabs. Ensure your virtual environment is activated in each.

### 1. Start the Controller Service
This service manages the game state and logic.
```bash
python -m controller_service.main
```

### 2. Start the Game Service
This service handles player connections and game flow.
```bash
python -m game_service.main
```

### 3. Start a Client Instance
Run this command for each player you want to join the game.
```bash
textual run --dev pod_of_tokyo_client.main
```

## Development

To run tests:
```bash
pytest
```
