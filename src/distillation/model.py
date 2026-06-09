import torch
import torch.nn as nn
from transformers import AutoModel
from src.distillation.labels import LabelEncoders, SINGLE_LABEL_FIELDS, MULTI_LABEL_FIELDS

_enc = LabelEncoders()

LABEL_CONFIG = {
    field: {
        "type": "multi" if _enc.is_multi(field) else "single",
        "n_classes": _enc.vocab_size(field),
    }
    for field in list(SINGLE_LABEL_FIELDS) + list(MULTI_LABEL_FIELDS)
}


class PodcastClassifier(nn.Module):
    def __init__(self, model_name: str):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        self.heads = nn.ModuleDict({
            field: nn.Linear(hidden_size, cfg["n_classes"])
            for field, cfg in LABEL_CONFIG.items()
        })

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> dict[str, torch.Tensor]:
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        # [CLS] token representation (position 0)
        pooled = outputs.last_hidden_state[:, 0]
        return {field: head(pooled) for field, head in self.heads.items()}
