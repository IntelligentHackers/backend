from procedures.matching.tokenizer import encode_tags, encode_bio
from procedures.survey.struct import UserSurveyResult
import torch


class NormalizedUserSurveyResult(UserSurveyResult):
    @property
    def age_(self):
        from datetime import date, datetime

        today = date.today()
        age = (
            today.year
            - datetime.fromisoformat(self.birth).year
            - ((today.month, today.day) < (datetime.fromisoformat(self.birth).month, datetime.fromisoformat(self.birth).day))
        )
        normalized = (age - 10) / 90
        return torch.tensor([[normalized]], dtype=torch.float32)

    @property
    def gender_(self):
        mapping = {
            "male": 1,
            "female": 2,
            "nonbinary": 3,
            "unknown": 4,
        }
        gender = mapping[self.gender]
        return torch.tensor([gender], dtype=torch.long).unsqueeze(0)

    @property
    def tags_(self):
        return encode_tags(self.tags).unsqueeze(0)

    @property
    def bio_(self):
        return encode_bio(self.bio).unsqueeze(0)

    @property
    def vector(self):
        """
        It should be perfectly concat with items above.
        """
        return torch.cat(
            [
                self.age_,
                self.gender_,
                self.tags_,
                self.bio_,
            ]
        )
