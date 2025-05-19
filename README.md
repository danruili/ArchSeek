# ArchSeek🏠🔍

[![arXiv](https://img.shields.io/badge/arXiv-1234.56789-b31b1b.svg)](https://arxiv.org/abs/2503.18680) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Web demo](https://img.shields.io/badge/Web%20demo-https%3A%2F%2Farchseek.onrender.com-darkgreen)](https://archseek.onrender.com)

Efficiently searching for relevant case studies is critical in architectural design, as designers rely on precedent examples to guide or inspire their ongoing projects. Traditional text-based search systems, while useful, struggle to capture the inherently visual and complex nature of architectural information. 

This paper introduces **ArchSeek🏠🔍**, an innovative case study search system with recommendation capability, tailored for architecture design professionals 📐. Leveraging vision-language models and cross-modal embeddings, ArchSeek enables domain-specific understandings of design cases, facilitating:
- Text search 💬 in natural language.
- Images search 🖼️ with fine-grained control.
- Case recommendations by *Liking design cases*❤️. 

It enhances personalization and efficiency, allowing architects to articulate preferences and discover design inspirations seamlessly.

## Install

(1) Clone the repository:
```bash
git clone https://github.com/danruili/ArchSeek.git
```

(2) Create a new conda environment and install the dependencies:

```bash
conda create -n archseek python=3.12
conda activate archseek
pip install -r requirements.txt
```

Conda can be installed from [Anaconda](https://docs.anaconda.com/miniconda/) or [MiniForge](https://conda-forge.org/miniforge/).

Every time before running the program, you need to activate the conda environment:

```bash
conda activate archseek
```

(3) Add a file named `.env` in the root directory of the project with the following content:

```env
OPENAI_API_KEY="your-openai-api-key"
REPLICATE_API_TOKEN="your-replicate-api-token"
```

OpenAI API key can be obtained from the [OpenAI website](https://platform.openai.com/docs/quickstart).
Replicate API token can be obtained from the [Replicate website](https://replicate.com/).


## Usage

By default you will use `/data/example_dataset` as the dataset, which is collected from Wikipedia. All materials in the example dataset are licensed under Creative Commons Attribution-ShareAlike Licenses. You can find the attributions in the `meta.csv` file in each design case folder.

To start the Rec-Arch program with user interface, run the following command:

```bash
python main.py
```

If you want to use the program in terminal, you can use the following commands:

```bash
python -m retrieval.query --query "red brick" --database "data/example_index"
```

Notice: 
- We use Replicate API for ImageBind model, which might take a while to warm up if the model is not frequently accessed. Please be patient. Also, it might hit the API rate limit if too many requests are sent in a short period of time, leading to temporary unavailability.
- By default the precomputed data can only be run on Windows. If you want to run it on Linux, please delete all `.pkl` data in the `data/example_index` and recompute the `.pkl` data by conducting the step 2 in the next section.

## Use your own dataset

(1) Prepare your dataset in the following format: Put your dataset in the `/data/<your_dataset>` directory. Each design case should be in a separate folder, and the folder name should be the case name. Inside each folder, there should be a `description.txt` file containing the description of the design case, and an optional image files containing the image of the design case. Also, you need a `meta.csv` where you store the link to the project in the first row. An example of the `meta.csv` file is shown below:

```csv
Vyborg_Library,https://en.wikipedia.org/wiki/Vyborg_Library
<any other information you want to add>, <any other link you want to add>
...
```

The folder structure should look like this:

```text
data/
    └── <your_dataset>
        ├── case1
        │   ├── description.txt
        │   ├── image1.jpg
        │   └── meta.csv
        ├── case2
        │   ├── description.txt
        │   ├── image1.jpg
        │   └── meta.csv
        └── case3
            ├── description.txt
            ├── image1.jpg
            └── meta.csv
```

(2) To build the database index on a new dataset, use the following command. Remember to change the `--data` and `--output` parameters to your own dataset and output directory. The output directory will be created if it does not exist. The building process will take a while depending on the size of your dataset. Also, if it breaks in the middle, you can always restart it and it will continue from where it left off.

```bash
python -m preprocess.build --data "data/example_dataset" --output "data/example_index"
```

(3) Finally, you need to change the source and index directory in the `config.json` to your own dataset and index directory:

```json
"backend_config": {
    "source_directory": "<your_dataset_path>",
    "index_directory": "<your_index_path>"
}
```