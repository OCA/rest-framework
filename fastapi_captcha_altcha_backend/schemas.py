# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from extendable_pydantic import StrictExtendableBaseModel


class AltchaChallenge(StrictExtendableBaseModel):
    algorithm: str
    challenge: str
    max_number: int
    salt: str
    signature: str

    @classmethod
    def from_challenge(cls, challenge):
        return cls.model_construct(
            algorithm=challenge.algorithm,
            challenge=challenge.challenge,
            max_number=challenge.max_number,
            salt=challenge.salt,
            signature=challenge.signature,
        )
