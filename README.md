# YOLOv5 Farwest

Welcome to the YOLOv5 Farwest project repository. This project utilizes the YOLOv5 model to perform object detection tailored to specific requirements. It's designed to be easy to set up and flexible for various customization options.

## Prerequisites

Before starting, ensure you have the following installed on your system:

- Git
- Python 3.8 or newer

## Installation

To get the project up and running on your local machine, follow these steps:

### 1. Clone the Repository

First, clone the repository to your local machine using Git:

```bash
git clone https://github.com/Aadi0032007/yolov5_farwest.git
cd yolov5_farwest
pip install -r requirements.txt
```

### 2. Configuration
Before running inference, you should check and adjust the model, source, and parameters according to your needs:

Model and Parameters: Inspect test_server.py to verify the model settings, source paths, and parameters such as debug_save, confidences, etc.
Customized Parameters: Review detect.py for customized parameters, including paths where the results should be saved.


### 3. Running Inference
To run inference with the model, execute the following command:

```bash
python test_server.py
```

This command will process the input data using the YOLOv5 model and output the results according to the configurations set in test_server.py and detect.py.
