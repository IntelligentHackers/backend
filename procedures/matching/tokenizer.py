from transformers import AutoTokenizer
import torch

from procedures.matching.parameters import tag_token, bio_token

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B-Instruct")
tokenizer.pad_token = tokenizer.eos_token  # ensure padding works


def encode_bio(bio: str) -> torch.Tensor:
    tokens = tokenizer(
        bio, truncation=True, padding="max_length", max_length=bio_token, return_tensors="pt"
    )
    return tokens["input_ids"].squeeze(0)


def encode_tags(tags: list[str]) -> torch.Tensor:
    tag_string = " ".join(tags)
    tokens = tokenizer(
        tag_string,
        truncation=True,
        padding="max_length",
        max_length=tag_token,
        return_tensors="pt",
    )
    return tokens["input_ids"].squeeze(0)
