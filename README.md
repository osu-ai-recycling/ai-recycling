# AI Recycling

This is the main project repo for the Automated AI-Recycling OSU Project. 

## Prerequisites

Before starting, ensure you have the following installed on your system:

- Git
- 3.8 <= Python <= 3.11 (PyTorch does not work with newer versions of Python yet)
- Requirements as specificed in requirements.txt (pip install -r requirements.txt)

## Installation

To get the project up and running on your local machine, follow these steps:

### 1. Clone the Repository

First, clone the repository to your local machine using Git:

```bash
git clone https://github.com/osu-ai-recycling/ai-recycling
cd ai-recycling
pip install -r requirements.txt
```

### 2. Configuration
Before running inference, you should check and adjust the model, source, and parameters according to your needs:

Model and Parameters: Inspect **test_server.py** to verify the model settings, source paths, and parameters such as **debug_save**, **confidences**, etc.
Customized Parameters: Review **detect.py** for **customized parameters**, including paths where the results should be saved.


### 3. Running Inference
To run inference with the model, execute the following command:

```bash
python test_server.py video_path
```

This command will process the input data using the YOLOv5 model and output the results according to the configurations set in test_server.py and detect.py.
The parameter video_path is the path to the input video.
