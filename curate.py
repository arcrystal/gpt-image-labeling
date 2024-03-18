import os
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import time
import base64
from sentence_transformers import SentenceTransformer
import asyncio
import aiohttp


def get_prompt(filename="prompt.txt"):
    return (open(os.path.join(os.getcwd(), filename), 'r')
            .read()
            .strip())


def get_labels(data_dir, filename="labels.txt"):
    return (open(os.path.join(os.path.join(os.getcwd(), data_dir), filename), 'r')
            .read()
            .strip()
            .split('\n'))


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def process_text(text):
    return ''.join(c for c in text if c.isalpha() or c == " ").replace("  ", " ")


class Curate:
    def __init__(self, api_key_fname="API_KEY",
                 similarity_model='sentence-transformers/all-mpnet-base-v2',
                 prompt=""):
        self.df = None
        self.model = SentenceTransformer(similarity_model)
        try:
            self.api_key = open(api_key_fname).read()
        except FileNotFoundError:
            print("API Key not found in current working directory")
            print("Please add your openai API key in a text file called 'API_KEY'")
            exit()

        self.prompt = prompt if prompt else get_prompt("prompt.txt")

    async def call_api(self, image_base64, session, semaphore):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": self.prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [message for _ in range(5)],  # Repeat the same message 5 times
            "max_tokens": 50  # Adjust for more extensive output
        }

        async with semaphore:
            await asyncio.sleep(1)
            async with session.post("https://api.openai.com/v1/chat/completions",
                                    headers=headers,
                                    json=payload) as resp:
                response_json = await resp.json()
                return response_json["choices"][0]['message']["content"]

    async def get_completion_list(self, image_base64, max_parallel_calls):
        semaphore = asyncio.Semaphore(value=max_parallel_calls)

        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.call_api(image_base64, session, semaphore) for _ in
                  range(5)])

    async def query_gpt4_with_image(self, image_path):
        image_base64 = encode_image(image_path)
        responses = await self.get_completion_list(image_base64, 100)
        return responses

    def add_to_results(self, data_dir, img_file, responses, similarities, true_label):
        pred_label = [process_text(r) for r in responses]
        true_label = process_text(true_label)
        new_row = {"Directory": [data_dir],
                   "Image File": [img_file],
                   "Actual Label": [true_label]}
        for i in range(len(pred_label)):
            new_row[f"Response{i}"] = [pred_label[i]]
            new_row[f"Similarity{i}"] = [similarities[i]]

        df2 = pd.DataFrame(new_row)
        if self.df is None:
            self.df = df2
        else:
            self.df = pd.concat([self.df, df2], ignore_index=True)

    def get_similarity(self, response, true_label):
        res = self.model.encode(response)
        lab = self.model.encode(true_label)
        return cosine_similarity(res.reshape(1, -1), lab.reshape(1, -1))[0][0]

    def process_directory(self, data_dir):
        if os.path.exists(os.path.join(data_dir, "results.csv")):
            self.df = pd.read_csv(os.path.join(data_dir, "results.csv"), index_col=0)
            print("Found existing results csv.")

        files = sorted([f for f in os.listdir(data_dir)
                        if os.path.isfile(os.path.join(data_dir, f)) and '.txt' not in f])
        num_files = len(files)
        labels = get_labels(data_dir)
        start = time.time()
        assert len(labels) == num_files or len(
            labels) == num_files - 1, f"{len(labels)}!={num_files}"
        num_queries = 0
        for i, (true_label, img_file) in enumerate(zip(labels, files)):
            if self.df is not None:
                if self.df['Image File'].str.contains(img_file).any():
                    print(f"Skipping {img_file}...")
                    continue

            img_path = os.path.join(data_dir, img_file)
            print(f"Querying example {i + 1}/{num_files}: {img_path}...", end=" ")
            try:
                responses = asyncio.run(self.query_gpt4_with_image(img_path))
                similarities = [self.get_similarity(res, true_label) for res in responses]
                self.add_to_results(data_dir, img_file, responses, similarities, true_label)
                print("Done.")
                num_queries += 1
            except KeyError as e:
                print("429 Error. Stopping run.")
                if self.df is not None:
                    self.df.to_csv(os.path.join(data_dir, "results.csv"))

                return num_queries - 1

        elapsed = time.time() - start
        print("Total elapsed time :", round(elapsed, 2))
        print("Time per image     :", round(elapsed / num_files, 2))
        self.df.to_csv(os.path.join(data_dir, "results.csv"))
        return num_queries

    def process_directories(self, root_dir):
        num_queries = 0
        for data_dir in os.listdir(root_dir):
            path = os.path.join(os.getcwd(), root_dir, data_dir)
            if os.path.isdir(path):
                print(f"Folder: {data_dir}")
                single_dir_queries = self.process_directory(path)
                num_queries += single_dir_queries

        return num_queries
