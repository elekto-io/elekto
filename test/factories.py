import uuid

import factory
from elekto.models.sql import Election, Ballot, Voter, User


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User


class VoterFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Voter


class BallotFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Ballot

    rank = factory.Faker('pyint', min_value=1, max_value=100)
    voter = str(uuid.uuid4())


class ElectionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Election

    name = factory.Sequence(lambda n: "Election #%s" % n)

    @factory.post_generation
    def ballots(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for n in range(extracted):
                BallotFactory.create(election=self)
