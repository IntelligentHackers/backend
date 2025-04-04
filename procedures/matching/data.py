from database import db
from procedures.matching.normalize import NormalizedUserSurveyResult
from procedures.matching.parameters import batch_size, positive_sample_ratio
from typings.selection import SelectionResult
from utils.object_id import validate_object_id


async def get_selection_data(batch_size=batch_size):
    """
    In this function, we should find `batch_size` items that is not used for train, with appropriate ratio of
    p+ and p-. We should also look up the `users` collection, to find out user data, and vectorize.

    It involves `subject` and `object`, which is the subject and object of the matching record.
    They are `str`, since it's unable to use ObjectId in pydantic.
    But you need to convert them to ObjectId when querying the database.
    """

    async def generate_pipeline(scope: SelectionResult):
        return [
            {"$match": {"trained": False, "result": scope}},
            {
                "$sample": {
                    "size": int(
                        batch_size * positive_sample_ratio
                        if scope == SelectionResult.approved
                        else batch_size * (1 - positive_sample_ratio)
                    )
                }
            },
        ]

    # Get positive samples
    positive_pipeline = await generate_pipeline(SelectionResult.approved)
    positive_samples = await db.selections.aggregate(positive_pipeline).to_list(
        length=None
    )
    # Get negative samples
    negative_pipeline = await generate_pipeline(SelectionResult.rejected)
    negative_samples = await db.selections.aggregate(negative_pipeline).to_list(
        length=None
    )

    # Combine positive and negative samples
    samples = positive_samples + negative_samples

    # Shuffle the samples to ensure randomness
    import random

    random.shuffle(samples)

    result = []

    for sample in samples:
        # make them to be the vector.
        subject_user = NormalizedUserSurveyResult(
            **await db.users.find_one({"_id": validate_object_id(sample["subject"])})
        ).vector
        object_user = NormalizedUserSurveyResult(
            **await db.users.find_one({"_id": validate_object_id(sample["object"])})
        ).vector
        res = SelectionResult(sample["result"]).award.item()  # Convert tensor to float
        result.append((res, subject_user, object_user))
        print(subject_user.shape, object_user.shape)

    return result
